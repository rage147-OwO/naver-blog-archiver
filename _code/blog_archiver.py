# -*- coding: utf-8 -*-
"""
네이버 블로그 아카이버 v2
========================
글/이미지를 SQLite DB + 로컬 폴더에 증분 백업하는 도구.

  - 증분 동기화: 새 글만 받고, 제목/미리보기 변경 감지 시 재수집 (수정 이력 보존)
  - 이미지 원본 화질 다운로드 + 실제 확장자 저장
  - 삭제/비공개된 글도 아카이브에는 보존 (missing 상태로 표시)
  - 다크 테마 웹 UI (Flask) — 검색·카테고리 필터·오프라인 본문 뷰어
  - 내보내기: Jekyll(_posts/_images/nav), Markdown 폴더, JSON 덤프
  - googletrans 제거 → 내장 한글 로마자 변환 (카테고리 slug)

사용법:
  python blog_archiver.py sync   [--full] [--limit N] [--blog ID]
  python blog_archiver.py web    [--port 8765] [--no-browser]
  python blog_archiver.py export --format jekyll|markdown|json
  python blog_archiver.py stats
  python blog_archiver.py search "검색어"
  python blog_archiver.py rebuild   # 저장된 원본 HTML로 markdown/뷰어 HTML 재생성 (재다운로드 없음)
"""

import argparse
import hashlib
import html as html_mod
import json
import re
import shutil
import sqlite3
import sys
import threading
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md_convert

# PyInstaller exe로 실행되면 __file__은 임시 폴더를 가리킴 → exe 위치 기준으로
if getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(sys.executable).resolve().parent
else:
    SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
KST = timezone(timedelta(hours=9))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "blog_id": "",                         # 네이버 블로그 ID (config.json 또는 웹 UI 설정에서 지정)
    "archive_dir": "archive",              # 스크립트 기준 상대경로 (절대경로도 가능)
    "request_delay": 0.5,                  # 글/이미지 요청 사이 대기(초)
    "image_original_quality": True,        # 원본 화질 시도 (blogfiles / type=w3840)
    "excluded_categories": [],             # Jekyll 내보내기에서 제외할 카테고리 (백업은 전부 저장)
    "jekyll_image_base_url": "https://raw.githubusercontent.com/<user>/<repo>/master/_images",
    "jekyll_repo_dir": "",                 # GitHub Pages 저장소 로컬 경로 (publish 명령용)
    "publish_after_sync": False,           # 동기화 후 자동으로 블로그 배포
    "web_port": 8765,
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"[경고] config.json 파싱 실패, 기본값 사용: {e}")
    else:
        save_config(cfg)
    return cfg


def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def blog_paths(cfg: dict) -> dict:
    """블로그별 저장 경로. blog_id 마다 하위 폴더로 격리."""
    base = SCRIPT_DIR / cfg["archive_dir"] / cfg["blog_id"]
    return {
        "base": base,
        "db": base / "archive.db",
        "images": base / "images",
        "exports": base / "exports",
    }


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    log_no          INTEGER PRIMARY KEY,
    blog_id         TEXT NOT NULL,
    title           TEXT NOT NULL DEFAULT '',
    category_no     INTEGER,
    category        TEXT DEFAULT '',
    published_at    TEXT DEFAULT '',
    url             TEXT DEFAULT '',
    brief           TEXT DEFAULT '',
    thumbnail_url   TEXT DEFAULT '',
    comment_count   INTEGER DEFAULT 0,
    sympathy_count  INTEGER DEFAULT 0,
    editor_version  INTEGER,
    html_raw        TEXT DEFAULT '',
    html_local      TEXT DEFAULT '',
    markdown        TEXT DEFAULT '',
    content_sha     TEXT DEFAULT '',
    status          TEXT DEFAULT 'ok',      -- ok | missing | error
    error           TEXT DEFAULT '',
    first_synced_at TEXT DEFAULT '',
    updated_at      TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_posts_pub ON posts(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_cat ON posts(category);

CREATE TABLE IF NOT EXISTS images (
    log_no       INTEGER NOT NULL,
    seq          INTEGER NOT NULL,
    src_url      TEXT DEFAULT '',
    download_url TEXT DEFAULT '',
    filename     TEXT DEFAULT '',
    content_type TEXT DEFAULT '',
    bytes        INTEGER DEFAULT 0,
    sha256       TEXT DEFAULT '',
    ok           INTEGER DEFAULT 0,
    PRIMARY KEY (log_no, seq)
);

CREATE TABLE IF NOT EXISTS media (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    log_no INTEGER NOT NULL,
    kind   TEXT NOT NULL,
    info   TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS categories (
    category_no INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    parent_no   INTEGER,
    post_count  INTEGER DEFAULT 0,
    open_yn     INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS category_map (
    kor  TEXT PRIMARY KEY,
    slug TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    log_no      INTEGER NOT NULL,
    changed_at  TEXT NOT NULL,
    title       TEXT DEFAULT '',
    content_sha TEXT DEFAULT '',
    markdown    TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT DEFAULT '',
    mode        TEXT DEFAULT '',
    listed      INTEGER DEFAULT 0,
    added       INTEGER DEFAULT 0,
    updated     INTEGER DEFAULT 0,
    failed      INTEGER DEFAULT 0,
    note        TEXT DEFAULT ''
);
"""


def open_db(cfg: dict) -> sqlite3.Connection:
    paths = blog_paths(cfg)
    paths["base"].mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(paths["db"], timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# 한글 로마자 변환 (국어의 로마자 표기법) — googletrans 대체
# ---------------------------------------------------------------------------

_CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"]
_JUNG = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo",
         "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
_JONG = ["", "g", "kk", "gs", "n", "nj", "nh", "d", "l", "lg", "lm", "lb", "ls", "lt", "lp", "lh",
         "m", "b", "bs", "s", "ss", "ng", "j", "ch", "k", "t", "p", "h"]


def romanize(text: str) -> str:
    out = []
    for ch in text:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3:
            idx = o - 0xAC00
            out.append(_CHO[idx // 588] + _JUNG[(idx % 588) // 28] + _JONG[idx % 28])
        else:
            out.append(ch)
    return "".join(out)


def category_slug(name: str) -> str:
    """카테고리명 → Jekyll에서 안전한 ASCII slug. 예: '금융'→'Geumyung', 'VRchat SDK3 강의'→'VRchatSDK3Gangui'"""
    words = re.split(r"\s+", name.strip())
    parts = []
    for w in words:
        r = re.sub(r"[^A-Za-z0-9]", "", romanize(w))
        if r:
            parts.append(r[0].upper() + r[1:])
    return "".join(parts) or "Etc"


def get_slug(con: sqlite3.Connection, kor: str) -> str:
    row = con.execute("SELECT slug FROM category_map WHERE kor=?", (kor,)).fetchone()
    if row:
        return row["slug"]
    slug = category_slug(kor)
    con.execute("INSERT OR REPLACE INTO category_map(kor, slug) VALUES(?,?)", (kor, slug))
    con.commit()
    return slug


# ---------------------------------------------------------------------------
# 네이버 클라이언트
# ---------------------------------------------------------------------------

class NaverClient:
    def __init__(self, blog_id: str, delay: float = 0.5):
        self.blog_id = blog_id
        self.delay = delay
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": USER_AGENT,
            "Referer": f"https://m.blog.naver.com/{blog_id}",
        })

    def _get(self, url, **kw):
        for attempt in range(3):
            try:
                r = self.s.get(url, timeout=20, **kw)
                if r.status_code == 200:
                    return r
                time.sleep(1 + attempt)
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)
        raise RuntimeError(f"GET 실패({r.status_code}): {url}")

    def list_posts(self):
        """모바일 API로 전체 글 목록. 실패 시 데스크톱 API 폴백."""
        try:
            return self._list_posts_mobile()
        except Exception as e:
            print(f"[경고] 모바일 API 실패({e}), 데스크톱 API로 폴백")
            return self._list_posts_desktop()

    def _list_posts_mobile(self):
        items, page = [], 1
        while page <= 300:
            url = (f"https://m.blog.naver.com/api/blogs/{self.blog_id}/post-list"
                   f"?categoryNo=0&itemCount=30&page={page}")
            data = self._get(url).json()
            batch = data.get("result", {}).get("items", [])
            if not batch:
                break
            for it in batch:
                ts = it.get("addDate")
                published = (datetime.fromtimestamp(ts / 1000, KST).isoformat(timespec="seconds")
                             if isinstance(ts, (int, float)) else "")
                items.append({
                    "log_no": int(it["logNo"]),
                    "title": html_mod.unescape((it.get("titleWithInspectMessage") or "").strip()),
                    "category": (it.get("categoryName") or "").strip(),
                    "category_no": it.get("categoryNo"),
                    "published_at": published,
                    "brief": html_mod.unescape((it.get("briefContents") or "").strip()),
                    "thumbnail_url": it.get("thumbnailUrl") or "",
                    "comment_count": it.get("commentCnt") or 0,
                    "sympathy_count": it.get("sympathyCnt") or 0,
                    "editor_version": it.get("smartEditorVersion"),
                })
            page += 1
            time.sleep(0.2)
        if not items:
            raise RuntimeError("모바일 API가 빈 목록을 반환")
        return items

    def _list_posts_desktop(self):
        """레거시 PostTitleListAsync 폴백. 메타데이터가 빈약하다."""
        from urllib.parse import unquote
        items, page, total = [], 1, None
        while total is None or (page - 1) * 30 < total:
            url = (f"https://blog.naver.com/PostTitleListAsync.naver"
                   f"?blogId={self.blog_id}&currentPage={page}&countPerPage=30")
            raw = self._get(url).text.replace("\\", "\\\\")
            data = json.loads(raw)
            total = int(data.get("totalCount", 0))
            for p in data.get("postList", []):
                add = (p.get("addDate") or "").replace(". ", "-").replace(".", "").strip()
                items.append({
                    "log_no": int(p["logNo"]),
                    "title": html_mod.unescape(unquote(p.get("title", "").replace("+", " "))),
                    "category": "",
                    "category_no": p.get("categoryNo"),
                    "published_at": add,
                    "brief": "",
                    "thumbnail_url": "",
                    "comment_count": 0,
                    "sympathy_count": 0,
                    "editor_version": None,
                })
            page += 1
            time.sleep(0.2)
        return items

    def list_categories(self):
        url = f"https://m.blog.naver.com/api/blogs/{self.blog_id}/category-list"
        try:
            data = self._get(url).json()
            out = []
            for c in data.get("result", {}).get("mylogCategoryList", []):
                if c.get("divisionLine"):
                    continue
                out.append({
                    "category_no": c.get("categoryNo"),
                    "name": (c.get("categoryName") or "").strip(),
                    "parent_no": c.get("parentCategoryNo"),
                    "post_count": c.get("postCnt") or 0,
                    "open_yn": 1 if c.get("openYN") else 0,
                })
            return out
        except Exception:
            return []

    def fetch_post_html(self, log_no: int) -> str:
        url = f"https://blog.naver.com/PostView.naver?blogId={self.blog_id}&logNo={log_no}"
        return self._get(url).text

    def download_image(self, src_url: str, original_quality: bool = True):
        """이미지 다운로드. 원본 화질 후보를 순서대로 시도.
        반환: (content_bytes, content_type, 사용한 URL) / 실패 시 (None, '', '')"""
        base = src_url.split("?")[0]
        candidates = []
        if original_quality and "postfiles.pstatic.net" in base:
            candidates.append(base.replace("postfiles.pstatic.net", "blogfiles.pstatic.net"))
            candidates.append(base + "?type=w3840")
        candidates.append(src_url)
        for cand in candidates:
            try:
                r = self.s.get(cand, timeout=30)
                ctype = r.headers.get("Content-Type", "")
                if r.status_code == 200 and ctype.startswith("image/") and len(r.content) > 100:
                    return r.content, ctype, cand
            except requests.RequestException:
                continue
        return None, "", ""


# ---------------------------------------------------------------------------
# 본문 파싱 / 변환
# ---------------------------------------------------------------------------

EXT_MAP = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/gif": ".gif", "image/webp": ".webp", "image/bmp": ".bmp",
    "image/svg+xml": ".svg",
}


def ext_from(content_type: str, url: str) -> str:
    ct = content_type.split(";")[0].strip().lower()
    if ct in EXT_MAP:
        return EXT_MAP[ct]
    m = re.search(r"\.(png|jpe?g|gif|webp|bmp)([?#]|$)", url.lower())
    if m:
        e = m.group(1)
        return ".jpg" if e in ("jpg", "jpeg") else "." + e
    return ".bin"


def image_filename(src_url: str, ext: str) -> str:
    """src URL 기반 안정적 파일명 — 글 수정으로 순서가 바뀌어도 재다운로드 없음."""
    return hashlib.sha256(src_url.encode()).hexdigest()[:12] + ext


def extract_main(html: str, log_no: int):
    """PostView HTML에서 본문 컨테이너 추출. 반환: BeautifulSoup 노드 (없으면 None)"""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("div.se-main-container")
    if main is None:
        # 구 에디터 폴백
        main = soup.select_one(f"div#post-view{log_no}") or soup.select_one("#postViewArea")
    return main


def parse_post_content(main) -> dict:
    """본문에서 이미지 URL 목록과 기타 미디어 기록 추출."""
    images = []
    for img in main.select("img.se-image-resource"):
        src = img.get("data-lazy-src") or img.get("data-src") or img.get("src")
        if src:
            images.append(src)
    media = []
    for cls, kind in [("se-module-video", "video"), ("se-module-file", "file"),
                      ("se-module-oglink", "oglink"), ("se-sticker-image", "sticker")]:
        for el in main.select("." + cls):
            info = {"text": el.get_text(" ", strip=True)[:200]}
            a = el.find("a", href=True) if hasattr(el, "find") else None
            if a:
                info["href"] = a["href"]
            if el.name == "img" and el.get("src"):
                info["src"] = el.get("src")
            script = el.find("script", {"type": "text/data-module"}) if hasattr(el, "find") else None
            if script and script.string:
                info["data"] = script.string.strip()[:500]
            media.append({"kind": kind, "info": json.dumps(info, ensure_ascii=False)})
    return {"images": images, "media": media}


def clean_content_soup(main_html: str, img_srcs: list) -> BeautifulSoup:
    """본문 HTML 정리 공용 루틴 — 제목모듈/스크립트 제거, 코드블록 정규화,
    이미지 src를 img_srcs(DOM 순서, None이면 유지)로 교체, 무의미한 앵커 제거."""
    soup = BeautifulSoup(main_html, "html.parser")
    # 문서 제목 모듈 제거 (제목은 DB에 별도 저장 — 레거시의 '첫 줄 삭제' 핵 대체)
    for t in soup.select(".se-documentTitle"):
        t.decompose()
    for s in soup.find_all("script"):
        s.decompose()
    # 코드 블록 → <pre><code> (markdownify가 ``` 로 변환)
    for cb in soup.select(".__se_code_view"):
        text = cb.get_text() if "\n" in cb.get_text() else cb.get_text("\n")
        pre = BeautifulSoup("", "html.parser").new_tag("pre")
        code = BeautifulSoup("", "html.parser").new_tag("code")
        code.string = text
        pre.append(code)
        cb.replace_with(pre)
    # 이미지 src 교체 (DOM 순서 매칭)
    for i, img in enumerate(soup.select("img.se-image-resource")):
        if i < len(img_srcs) and img_srcs[i]:
            img["src"] = img_srcs[i]
        for attr in ("data-lazy-src", "data-src", "srcset"):
            if img.has_attr(attr):
                del img[attr]
    # 라이트박스용 무의미한 앵커 제거 — markdown의 [![](...)](#) 노이즈 방지
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if (href in ("#", "") or href.startswith("javascript")) and a.find("img"):
            a.unwrap()
    return soup


def build_outputs(main_html: str, log_no: int, img_files: list, post_url: str) -> tuple:
    """원본 본문 HTML → (뷰어용 html_local, 보관용 markdown).
    img_files: DOM 순서와 같은 로컬 파일명 리스트 (실패한 이미지는 None)."""
    def srcs(prefix):
        return [f"{prefix}/{log_no}/{fn}" if fn else None for fn in img_files]

    html_local = str(clean_content_soup(main_html, srcs("/media")))

    md_soup = clean_content_soup(main_html, srcs("images"))
    # 동영상 모듈은 markdown에서 원본 링크 안내로 대체
    for v in md_soup.select(".se-module-video"):
        p = BeautifulSoup(f'<p><a href="{post_url}">[동영상 — 원본 글에서 재생]</a></p>', "html.parser")
        v.replace_with(p)
    markdown = md_convert(str(md_soup), heading_style="ATX", bullets="-")
    markdown = markdown.replace("​", "")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return html_local, markdown


def sanitize_filename(name: str, maxlen: int = 80) -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "-", name)
    name = re.sub(r"-{2,}", "-", name).strip(" .-")
    return (name[:maxlen].strip(" .-")) or "untitled"


# ---------------------------------------------------------------------------
# 동기화 엔진
# ---------------------------------------------------------------------------

def run_sync(cfg: dict, full: bool = False, limit: int = None, state: dict = None, log=None):
    """증분 동기화. state(dict)로 진행상황 공유, log(fn)로 메시지 출력.
    반환: {"listed","added","updated","failed"}"""
    state = state if state is not None else {}
    log = log or (lambda m: print(m, flush=True))
    if not cfg.get("blog_id"):
        raise RuntimeError("blog_id가 설정되지 않았습니다. config.json 또는 웹 UI 설정에서 지정하거나 --blog 옵션을 쓰세요.")
    con = open_db(cfg)
    paths = blog_paths(cfg)
    paths["images"].mkdir(parents=True, exist_ok=True)
    client = NaverClient(cfg["blog_id"], cfg["request_delay"])

    # 동시 실행 감지 (CLI+웹 등 다른 프로세스) — 차단하진 않고 경고만
    running = con.execute(
        "SELECT id, started_at FROM sync_runs WHERE finished_at='' ORDER BY id DESC LIMIT 1").fetchone()
    if running:
        log(f"[경고] 완료되지 않은 동기화(run {running['id']}, {running['started_at']})가 있습니다. "
            "동시 실행이면 중복 다운로드가 생길 수 있습니다.")

    run_id = con.execute(
        "INSERT INTO sync_runs(started_at, mode) VALUES(?,?)",
        (now_iso(), "full" if full else "incr")).lastrowid
    con.commit()

    result = {"listed": 0, "added": 0, "updated": 0, "failed": 0}
    try:
        # 1) 카테고리
        for c in client.list_categories():
            con.execute("""INSERT INTO categories(category_no,name,parent_no,post_count,open_yn)
                           VALUES(?,?,?,?,?)
                           ON CONFLICT(category_no) DO UPDATE SET
                             name=excluded.name, parent_no=excluded.parent_no,
                             post_count=excluded.post_count, open_yn=excluded.open_yn""",
                        (c["category_no"], c["name"], c["parent_no"], c["post_count"], c["open_yn"]))
        con.commit()

        # 2) 글 목록
        log("글 목록 수집 중...")
        items = client.list_posts()
        result["listed"] = len(items)
        log(f"블로그에 글 {len(items)}개 확인")

        existing = {r["log_no"]: r for r in con.execute(
            "SELECT log_no, title, brief, content_sha, status FROM posts")}

        # 3) 수집 대상 결정
        plan = []
        for it in items:
            old = existing.get(it["log_no"])
            if old is None:
                plan.append((it, "new"))
            elif full:
                plan.append((it, "refresh"))
            elif old["title"] != it["title"] or (it["brief"] and old["brief"] != it["brief"]):
                plan.append((it, "changed"))
        if limit:
            plan = plan[:limit]

        # 4) 가벼운 메타 갱신 (수집 대상이 아닌 기존 글: 공감/댓글/카테고리)
        planned = {it["log_no"] for it, _ in plan}
        for it in items:
            if it["log_no"] in existing and it["log_no"] not in planned:
                con.execute("""UPDATE posts SET comment_count=?, sympathy_count=?,
                               category=COALESCE(NULLIF(?,''),category), status='ok'
                               WHERE log_no=?""",
                            (it["comment_count"], it["sympathy_count"], it["category"], it["log_no"]))
        con.commit()

        state.update(total=len(plan), done=0)
        log(f"수집 대상 {len(plan)}개 (신규/변경/{'전체' if full else '증분'})")

        # 5) 본문 + 이미지 수집
        for it, reason in plan:
            if state.get("stop"):
                log("사용자 요청으로 중단")
                break
            log_no = it["log_no"]
            state["current"] = it["title"]
            try:
                html = client.fetch_post_html(log_no)
                main = extract_main(html, log_no)
                if main is None:
                    raise RuntimeError("본문 컨테이너를 찾지 못함 (비공개 글일 수 있음)")
                main_html = str(main)
                parsed = parse_post_content(main)

                # 이미지: URL 기반 파일명 → 이미 있으면 재다운로드 안 함
                old_imgs = {r["src_url"]: r for r in con.execute(
                    "SELECT * FROM images WHERE log_no=?", (log_no,))}
                img_dir = paths["images"] / str(log_no)
                img_rows, img_files, keep = [], [], set()
                for seq, src in enumerate(parsed["images"]):
                    old = old_imgs.get(src)
                    if old and old["ok"] and (img_dir / old["filename"]).exists():
                        fn = old["filename"]
                        img_rows.append((log_no, seq, src, old["download_url"], fn,
                                         old["content_type"], old["bytes"], old["sha256"], 1))
                    else:
                        content, ctype, used = client.download_image(src, cfg["image_original_quality"])
                        if content:
                            fn = image_filename(src, ext_from(ctype, used))
                            img_dir.mkdir(parents=True, exist_ok=True)
                            (img_dir / fn).write_bytes(content)
                            img_rows.append((log_no, seq, src, used, fn, ctype,
                                             len(content), hashlib.sha256(content).hexdigest(), 1))
                        else:
                            fn = None
                            img_rows.append((log_no, seq, src, "", "", "", 0, "", 0))
                            log(f"  [이미지 실패] {src[:80]}")
                        time.sleep(cfg["request_delay"] * 0.3)
                    img_files.append(fn)
                    if fn:
                        keep.add(fn)
                # 글 수정으로 빠진 이미지 파일 정리
                if img_dir.exists():
                    for f in img_dir.iterdir():
                        if f.name not in keep:
                            f.unlink(missing_ok=True)

                html_local, markdown = build_outputs(
                    main_html, log_no, img_files,
                    f"https://blog.naver.com/{cfg['blog_id']}/{log_no}")
                content_sha = hashlib.sha256(main_html.encode()).hexdigest()

                old = existing.get(log_no)
                if old and old["content_sha"] and old["content_sha"] != content_sha:
                    # 수정 감지 → 이전 버전 스냅샷 보존
                    prev = con.execute("SELECT title, markdown FROM posts WHERE log_no=?",
                                       (log_no,)).fetchone()
                    con.execute("""INSERT INTO posts_history(log_no, changed_at, title, content_sha, markdown)
                                   VALUES(?,?,?,?,?)""",
                                (log_no, now_iso(), prev["title"], old["content_sha"], prev["markdown"]))

                con.execute("""INSERT INTO posts(log_no, blog_id, title, category_no, category,
                                published_at, url, brief, thumbnail_url, comment_count, sympathy_count,
                                editor_version, html_raw, html_local, markdown, content_sha,
                                status, error, first_synced_at, updated_at)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(log_no) DO UPDATE SET
                                title=excluded.title, category_no=excluded.category_no,
                                category=excluded.category, published_at=excluded.published_at,
                                brief=excluded.brief, thumbnail_url=excluded.thumbnail_url,
                                comment_count=excluded.comment_count, sympathy_count=excluded.sympathy_count,
                                editor_version=excluded.editor_version, html_raw=excluded.html_raw,
                                html_local=excluded.html_local, markdown=excluded.markdown,
                                content_sha=excluded.content_sha, status='ok', error='',
                                updated_at=excluded.updated_at""",
                            (log_no, cfg["blog_id"], it["title"], it["category_no"], it["category"],
                             it["published_at"], f"https://blog.naver.com/{cfg['blog_id']}/{log_no}",
                             it["brief"], it["thumbnail_url"], it["comment_count"], it["sympathy_count"],
                             it["editor_version"], main_html, html_local, markdown, content_sha,
                             "ok", "", now_iso(), now_iso()))
                con.execute("DELETE FROM images WHERE log_no=?", (log_no,))
                con.executemany("""INSERT INTO images(log_no,seq,src_url,download_url,filename,
                                   content_type,bytes,sha256,ok) VALUES(?,?,?,?,?,?,?,?,?)""", img_rows)
                con.execute("DELETE FROM media WHERE log_no=?", (log_no,))
                con.executemany("INSERT INTO media(log_no,kind,info) VALUES(?,?,?)",
                                [(log_no, m["kind"], m["info"]) for m in parsed["media"]])
                con.commit()

                if reason == "new":
                    result["added"] += 1
                else:
                    result["updated"] += 1
                n_img = sum(1 for f in img_files if f)
                log(f"[{state.get('done',0)+1}/{len(plan)}] {it['title']} "
                    f"({it['category']}, 이미지 {n_img}/{len(img_files)})")
            except Exception as e:
                result["failed"] += 1
                log(f"[실패] {it['title']}: {e}")
                if it["log_no"] not in existing:
                    con.execute("""INSERT OR IGNORE INTO posts(log_no, blog_id, title, category,
                                   published_at, url, status, error, first_synced_at, updated_at)
                                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                                (log_no, cfg["blog_id"], it["title"], it["category"], it["published_at"],
                                 f"https://blog.naver.com/{cfg['blog_id']}/{log_no}",
                                 "error", str(e)[:300], now_iso(), now_iso()))
                    con.commit()
            state["done"] = state.get("done", 0) + 1
            time.sleep(cfg["request_delay"])

        # 6) 블로그에서 사라진 글 표시 (삭제/비공개 — 아카이브 내용은 보존)
        live = {it["log_no"] for it in items}
        gone = [ln for ln in existing if ln not in live]
        if gone and not limit:
            con.executemany("UPDATE posts SET status='missing' WHERE log_no=? AND status='ok'",
                            [(ln,) for ln in gone])
            con.commit()
            log(f"블로그에서 사라진 글 {len(gone)}개 → missing 표시 (내용은 보존)")

        con.execute("""UPDATE sync_runs SET finished_at=?, listed=?, added=?, updated=?, failed=?
                       WHERE id=?""",
                    (now_iso(), result["listed"], result["added"], result["updated"],
                     result["failed"], run_id))
        con.commit()
        log(f"완료 — 신규 {result['added']}, 갱신 {result['updated']}, 실패 {result['failed']}")

        # 동기화 후 자동 블로그 배포 (config: publish_after_sync)
        if cfg.get("publish_after_sync") and (result["added"] or result["updated"]) and not state.get("stop"):
            try:
                log("변경 감지 → GitHub Pages 블로그 자동 배포 시작")
                publish_jekyll(cfg, log=log)
            except Exception as e:
                log(f"[블로그 배포 실패] {e}")
    except Exception as e:
        con.execute("UPDATE sync_runs SET finished_at=?, note=? WHERE id=?",
                    (now_iso(), f"오류: {e}", run_id))
        con.commit()
        log(f"[동기화 오류] {e}\n{traceback.format_exc()}")
        raise
    finally:
        con.close()
    return result


def run_rebuild(cfg: dict, log=None):
    """저장된 html_raw 로 html_local/markdown 재생성 (네트워크 불필요)."""
    log = log or (lambda m: print(m, flush=True))
    con = open_db(cfg)
    rows = con.execute("SELECT log_no, url, html_raw FROM posts WHERE html_raw != ''").fetchall()
    n = 0
    for r in rows:
        imgs = con.execute("SELECT filename, ok FROM images WHERE log_no=? ORDER BY seq",
                           (r["log_no"],)).fetchall()
        img_files = [i["filename"] if i["ok"] else None for i in imgs]
        html_local, markdown = build_outputs(r["html_raw"], r["log_no"], img_files, r["url"])
        con.execute("UPDATE posts SET html_local=?, markdown=? WHERE log_no=?",
                    (html_local, markdown, r["log_no"]))
        n += 1
    con.commit()
    con.close()
    log(f"{n}개 글 재생성 완료")
    return n


# ---------------------------------------------------------------------------
# 내보내기
# ---------------------------------------------------------------------------

NAV_TEMPLATE = """<!--전체 글 수를 세기 위한 연산. sum 변수에 전체 글 수 저장-->

{% assign sum = site.posts | size %}

<nav class="nav__list">
    <input id="ac-toc" name="accordion-toc" type="checkbox" />
    <label for="ac-toc">{{ site.data.ui-text[site.locale].menu_label }}</label>
    <ul class="nav__items" id="category_tag_menu">
        <!--전체 글 수-->
        <li>
            📂 <span style="font-family:'Cafe24Oneprettynight';">전체 글 수</style> <span
                    style="font-family:'Coming Soon';">{{sum}}</style> <span
                        style="font-family:'Cafe24Oneprettynight';">개</style>
        </li>
        <li>
            <span class="nav__sub-title">카테고리</span>
"""


def _norm_cat(name: str) -> str:
    """카테고리명 비교용 정규화 — NBSP(\\xa0)·제로폭 문자 포함 모든 공백 제거 + 소문자."""
    return re.sub(r"[\s ​]+", "", (name or "")).lower()


def _export_posts(con, cfg, include_excluded: bool):
    """내보내기 대상 글 목록. Jekyll은 제외 카테고리 적용."""
    rows = con.execute(
        "SELECT * FROM posts WHERE html_raw != '' ORDER BY published_at").fetchall()
    if include_excluded:
        return rows
    excluded = {_norm_cat(c) for c in cfg.get("excluded_categories", [])}
    return [r for r in rows if _norm_cat(r["category"]) not in excluded]


def export_jekyll(cfg: dict, dest: Path = None, log=None) -> dict:
    """레거시 SavedPost 포맷 호환 Jekyll 내보내기 (_posts/_images/_pages/nav_list_main)."""
    log = log or (lambda m: print(m, flush=True))
    con = open_db(cfg)
    paths = blog_paths(cfg)
    dest = Path(dest) if dest else paths["exports"] / "jekyll"
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "_posts").mkdir(parents=True)
    (dest / "_images").mkdir()
    (dest / "_pages" / "categories").mkdir(parents=True)

    posts = _export_posts(con, cfg, include_excluded=False)
    base_url = cfg["jekyll_image_base_url"].rstrip("/")
    used_names, cat_pairs = set(), {}
    for p in posts:
        date = (p["published_at"] or "")[:10] or "1970-01-01"
        fname = f"{date}-{sanitize_filename(p['title'])}"
        if fname in used_names:
            fname += f"-{p['log_no']}"
        used_names.add(fname)
        slug = get_slug(con, p["category"] or "기타")
        cat_pairs[p["category"] or "기타"] = slug

        md = p["markdown"].replace("](images/", f"]({base_url}/")
        md = md.replace('src="images/', f'src="{base_url}/')
        title_esc = p["title"].replace('"', '\\"')
        front = (f"---\ntitle: \"{title_esc}\"\ndate: {date}\ncategories:\n - {slug}\n"
                 f"naver_url: {p['url']}\n---\n\n")
        (dest / "_posts" / f"{fname}.md").write_text(front + md, encoding="utf-8")

        # 이미지 복사
        src_dir = paths["images"] / str(p["log_no"])
        if src_dir.exists():
            shutil.copytree(src_dir, dest / "_images" / str(p["log_no"]), dirs_exist_ok=True)

    # 카테고리 페이지 + nav
    slugs = sorted(set(cat_pairs.values()))
    for slug in slugs:
        (dest / "_pages" / "categories" / f"category-{slug}.md").write_text(
            "---\ntitle: \"" + slug + "\"\nlayout: archive\npermalink: categories/" + slug +
            "\nauthor_profile: true\nsidebar_main: true\n---\n\n"
            "{% assign posts = site.categories." + slug + " %}\n"
            "{% for post in posts %} {% include archive-single2.html type=page.entries_layout %} {% endfor %}",
            encoding="utf-8")
    (dest / "_pages" / "categories" / "CategoryEng.md").write_text("\n".join(slugs), encoding="utf-8")
    (dest / "_pages" / "categories" / "CategoryKor.md").write_text(
        "\n".join(sorted(cat_pairs.keys())), encoding="utf-8")

    nav = [NAV_TEMPLATE]
    for kor, slug in sorted(cat_pairs.items()):
        nav.append(
            "\n<ul>\n{% for category in site.categories %}\n"
            '{% if category[0] == "' + slug + '" %}\n'
            '<li><a href="/categories/' + slug + '" class="">' + kor +
            " ({{category[1].size}})</a></li>\n{% endif %}\n{% endfor %}\n</ul>\n")
    nav.append("</li>\n</ul>\n</nav>")
    (dest / "nav_list_main").write_text("".join(nav), encoding="utf-8")

    con.close()
    log(f"Jekyll 내보내기 완료: 글 {len(posts)}개 → {dest}")
    return {"count": len(posts), "dest": str(dest)}


def export_markdown(cfg: dict, dest: Path = None, log=None) -> dict:
    """순수 markdown + images 폴더 내보내기 (전체 글, 제외 없음)."""
    log = log or (lambda m: print(m, flush=True))
    con = open_db(cfg)
    paths = blog_paths(cfg)
    dest = Path(dest) if dest else paths["exports"] / "markdown"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    posts = _export_posts(con, cfg, include_excluded=True)
    used = set()
    for p in posts:
        date = (p["published_at"] or "")[:10] or "1970-01-01"
        fname = f"{date}-{sanitize_filename(p['title'])}"
        if fname in used:
            fname += f"-{p['log_no']}"
        used.add(fname)
        head = (f"# {p['title']}\n\n"
                f"> {date} · {p['category']} · 공감 {p['sympathy_count']} · 댓글 {p['comment_count']}\n"
                f"> 원본: {p['url']}\n\n")
        (dest / f"{fname}.md").write_text(head + p["markdown"], encoding="utf-8")
    if paths["images"].exists():
        shutil.copytree(paths["images"], dest / "images", dirs_exist_ok=True)
    con.close()
    log(f"Markdown 내보내기 완료: 글 {len(posts)}개 → {dest}")
    return {"count": len(posts), "dest": str(dest)}


def publish_jekyll(cfg: dict, log=None) -> dict:
    """Jekyll 내보내기 → GitHub Pages 저장소 반영 → commit → push.
    관리 영역(_posts/NaverBackup, _images, _pages/categories, _includes/nav_list_main)만
    통째로 교체하므로 저장소의 다른 파일(직접 쓴 글 등)은 건드리지 않는다."""
    import subprocess
    log = log or (lambda m: print(m, flush=True))
    repo = Path(cfg.get("jekyll_repo_dir") or "")
    if not repo.is_dir() or not (repo / ".git").exists():
        raise RuntimeError(f"jekyll_repo_dir가 git 저장소가 아닙니다: {repo} (설정에서 지정하세요)")

    r = export_jekyll(cfg, log=log)
    src = Path(r["dest"])

    managed = ["_posts/NaverBackup", "_images", "_pages/categories", "_includes/nav_list_main"]
    for s, d in [(src / "_posts", repo / "_posts" / "NaverBackup"),
                 (src / "_images", repo / "_images"),
                 (src / "_pages" / "categories", repo / "_pages" / "categories")]:
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(s, d)
    (repo / "_includes").mkdir(exist_ok=True)
    shutil.copyfile(src / "nav_list_main", repo / "_includes" / "nav_list_main")

    def git(*args):
        p = subprocess.run(["git", "-C", str(repo), *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            raise RuntimeError(f"git {args[0]} 실패: {(p.stderr or p.stdout).strip()[:400]}")
        return p.stdout

    git("add", "-A", "--", *managed)
    changed = len([l for l in git("status", "--porcelain", "--", *managed).splitlines() if l.strip()])
    if changed == 0:
        log("블로그 저장소에 변경 없음 — 커밋/푸시 생략")
        return {"count": r["count"], "changed": 0, "pushed": False, "dest": str(repo)}
    git("commit", "-m", f"네이버 블로그 동기화 {datetime.now(KST):%Y-%m-%d %H:%M} — 글 {r['count']}개")
    log(f"커밋 완료 (변경 {changed}개 파일) — push 중...")
    git("push", "origin", "HEAD")
    log(f"배포 완료: 글 {r['count']}개 → {repo}")
    return {"count": r["count"], "changed": changed, "pushed": True, "dest": str(repo)}


def export_json(cfg: dict, dest: Path = None, log=None) -> dict:
    """DB 전체를 JSON 한 파일로 덤프 (이동/2차 가공용)."""
    log = log or (lambda m: print(m, flush=True))
    con = open_db(cfg)
    paths = blog_paths(cfg)
    dest = Path(dest) if dest else paths["exports"] / "archive_dump.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dump = {"exported_at": now_iso(), "blog_id": cfg["blog_id"]}
    for table in ("posts", "images", "media", "categories", "posts_history", "sync_runs"):
        dump[table] = [dict(r) for r in con.execute(f"SELECT * FROM {table}")]
    dest.write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
    con.close()
    log(f"JSON 덤프 완료: 글 {len(dump['posts'])}개 → {dest}")
    return {"count": len(dump["posts"]), "dest": str(dest)}


# ---------------------------------------------------------------------------
# 통계
# ---------------------------------------------------------------------------

def get_stats(cfg: dict) -> dict:
    con = open_db(cfg)
    s = {}
    s["posts"] = con.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    s["missing"] = con.execute("SELECT COUNT(*) c FROM posts WHERE status='missing'").fetchone()["c"]
    s["errors"] = con.execute("SELECT COUNT(*) c FROM posts WHERE status='error'").fetchone()["c"]
    img = con.execute("SELECT COUNT(*) c, COALESCE(SUM(bytes),0) b FROM images WHERE ok=1").fetchone()
    s["images"], s["image_bytes"] = img["c"], img["b"]
    s["image_failed"] = con.execute("SELECT COUNT(*) c FROM images WHERE ok=0").fetchone()["c"]
    s["categories"] = [dict(r) for r in con.execute(
        "SELECT category, COUNT(*) c FROM posts GROUP BY category ORDER BY c DESC")]
    s["years"] = [dict(r) for r in con.execute(
        """SELECT substr(published_at,1,4) y, COUNT(*) c FROM posts
           WHERE published_at != '' GROUP BY y ORDER BY y""")]
    s["runs"] = [dict(r) for r in con.execute(
        "SELECT * FROM sync_runs ORDER BY id DESC LIMIT 5")]
    s["history"] = con.execute("SELECT COUNT(*) c FROM posts_history").fetchone()["c"]
    con.close()
    return s


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}GB"


# ---------------------------------------------------------------------------
# 웹 UI (Flask, 다크 테마)
# ---------------------------------------------------------------------------

SYNC_STATE = {"running": False, "mode": "", "total": 0, "done": 0, "current": "",
              "stop": False, "log": [], "result": None}

BASE_HTML = """<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}{% endblock %} · 블로그 아카이버</title>
<style>
:root{--bg:#1E1E24;--card:#2A2A33;--card2:#33333E;--green:#3DDC97;--naver:#03C75A;
      --text:#E8E8EE;--muted:#9A9AA8;--line:#3A3A46;--red:#FF6B6B;--yellow:#FFD166;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Malgun Gothic','Segoe UI',sans-serif;
     font-size:14px;display:flex;min-height:100vh}
a{color:var(--green);text-decoration:none} a:hover{text-decoration:underline}
aside{width:210px;min-width:210px;background:var(--card);padding:22px 16px;display:flex;
      flex-direction:column;gap:4px;position:sticky;top:0;height:100vh}
aside .logo{font-weight:bold;font-size:16px;margin-bottom:2px}
aside .logo .dot{color:var(--naver)}
aside .blogid{color:var(--muted);font-size:12px;margin-bottom:18px;word-break:break-all}
aside a.nav{display:block;padding:9px 12px;border-radius:8px;color:var(--text);font-size:14px}
aside a.nav:hover{background:var(--card2);text-decoration:none}
aside a.nav.active{background:var(--card2);color:var(--green);font-weight:bold}
aside .foot{margin-top:auto;color:var(--muted);font-size:11px;line-height:1.7}
main{flex:1;padding:26px 34px;max-width:1150px}
h1{font-size:21px;margin-bottom:18px} h2{font-size:16px;margin:20px 0 10px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.card{background:var(--card);border-radius:12px;padding:16px 18px}
.card .num{font-size:26px;font-weight:bold;color:var(--green);margin-top:4px}
.card .sub{color:var(--muted);font-size:12px;margin-top:3px}
.card.wide{grid-column:1/-1}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);font-size:13px}
th{color:var(--muted);font-weight:normal;font-size:12px}
tr:last-child td{border-bottom:none}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;background:var(--card2)}
.badge.missing{background:#4a3800;color:var(--yellow)}
.badge.error{background:#4a1f1f;color:var(--red)}
.badge.ok{color:var(--green)}
.btn{display:inline-block;background:var(--green);color:#10231b;border:none;border-radius:8px;
     padding:9px 18px;font-size:14px;font-weight:bold;cursor:pointer;font-family:inherit}
.btn:hover{filter:brightness(1.1)} .btn:disabled{opacity:.4;cursor:default}
.btn.ghost{background:var(--card2);color:var(--text);font-weight:normal}
.btn.danger{background:var(--red);color:#2b0f0f}
input[type=text],input[type=number],select,textarea{background:var(--bg);color:var(--text);
     border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:14px;font-family:inherit}
input:focus,select:focus,textarea:focus{outline:1px solid var(--green)}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.postrow{display:flex;gap:14px;align-items:center;background:var(--card);border-radius:12px;
         padding:12px 16px;margin-bottom:8px}
.postrow:hover{background:var(--card2)}
.postrow .thumb{width:60px;height:60px;border-radius:8px;object-fit:cover;background:var(--card2);
                display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0}
.postrow .t{font-size:15px;color:var(--text);font-weight:bold}
.postrow .m{color:var(--muted);font-size:12px;margin-top:4px}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:6px;font-size:13px}
.bar-row .label{width:170px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-row .bar{height:14px;background:var(--green);border-radius:4px;min-width:2px;opacity:.85}
.bar-row .cnt{color:var(--muted)}
.progress{height:16px;background:var(--card2);border-radius:8px;overflow:hidden;margin:10px 0}
.progress>div{height:100%;background:var(--green);width:0%;transition:width .4s}
.logbox{background:#15151A;border-radius:10px;padding:12px;font-family:Consolas,monospace;
        font-size:12px;height:300px;overflow-y:auto;white-space:pre-wrap;color:#B8B8C8;line-height:1.6}
.se-viewer{background:#FAFAFA;color:#1a1a1a;border-radius:14px;padding:34px 40px;line-height:1.75;
           font-size:15px;word-break:break-word}
.se-viewer img{max-width:100%;height:auto;border-radius:6px}
.se-viewer a{color:#03674f}
.se-viewer pre{background:#22252A;color:#E8E8EE;padding:14px;border-radius:8px;overflow-x:auto;
               font-size:13px;line-height:1.5;margin:12px 0}
.se-viewer table{background:transparent;color:#1a1a1a}
.se-viewer th,.se-viewer td{border:1px solid #ccc;color:#1a1a1a}
.mdbox{width:100%;height:480px;background:#15151A;color:#C8C8D8;border:1px solid var(--line);
       border-radius:10px;padding:14px;font-family:Consolas,monospace;font-size:12.5px;line-height:1.6}
.flash{background:var(--card2);border-left:3px solid var(--green);padding:10px 14px;
       border-radius:8px;margin-bottom:14px}
.pager{display:flex;gap:8px;align-items:center;margin-top:14px;color:var(--muted)}
.tabs{display:flex;gap:6px;margin-bottom:12px}
.tabs button{background:var(--card2);color:var(--text);border:none;border-radius:8px;
             padding:7px 14px;cursor:pointer;font-family:inherit;font-size:13px}
.tabs button.on{background:var(--green);color:#10231b;font-weight:bold}
</style></head>
<body>
<aside>
  <div class="logo">네이버 블로그<br>아카이버 <span class="dot">●</span></div>
  <div class="blogid">{{ cfg.blog_id }}</div>
  <a class="nav {{ 'active' if active=='dash' }}" href="/">대시보드</a>
  <a class="nav {{ 'active' if active=='posts' }}" href="/posts">글 목록</a>
  <a class="nav {{ 'active' if active=='sync' }}" href="/sync">동기화</a>
  <a class="nav {{ 'active' if active=='cats' }}" href="/categories">카테고리</a>
  <a class="nav {{ 'active' if active=='export' }}" href="/export">내보내기</a>
  <a class="nav {{ 'active' if active=='settings' }}" href="/settings">설정</a>
  <div class="foot">글 {{ side_posts }} · 이미지 {{ side_images }}<br>
    <a href="https://blog.naver.com/{{ cfg.blog_id }}" target="_blank">블로그 열기 ↗</a></div>
</aside>
<main>{% block body %}{% endblock %}</main>
</body></html>"""

DASH_HTML = """{% extends "base.html" %}{% block title %}대시보드{% endblock %}
{% block body %}
<h1>대시보드</h1>
<div class="cards">
  <div class="card"><div>보관된 글</div><div class="num">{{ s.posts }}</div>
    <div class="sub">missing {{ s.missing }} · 오류 {{ s.errors }} · 수정이력 {{ s.history }}</div></div>
  <div class="card"><div>이미지</div><div class="num">{{ s.images }}</div>
    <div class="sub">{{ size_str }}{% if s.image_failed %} · 실패 {{ s.image_failed }}{% endif %}</div></div>
  <div class="card"><div>카테고리</div><div class="num">{{ s.categories|length }}</div>
    <div class="sub">&nbsp;</div></div>
  <div class="card"><div>마지막 동기화</div>
    <div class="num" style="font-size:15px;margin-top:8px">{{ last_sync }}</div>
    <div class="sub">{{ last_sync_sub }}</div></div>
</div>

<div class="cards">
<div class="card">
<h2 style="margin-top:0">카테고리 분포</h2>
{% for c in s.categories[:15] %}
<div class="bar-row"><span class="label">{{ c.category or '(없음)' }}</span>
  <div class="bar" style="width:{{ (c.c / max_cat * 240)|int }}px"></div>
  <span class="cnt">{{ c.c }}</span></div>
{% endfor %}
</div>
<div class="card">
<h2 style="margin-top:0">연도별 글 수</h2>
{% for y in s.years %}
<div class="bar-row"><span class="label" style="width:50px">{{ y.y }}</span>
  <div class="bar" style="width:{{ (y.c / max_year * 240)|int }}px;background:var(--naver)"></div>
  <span class="cnt">{{ y.c }}</span></div>
{% endfor %}
</div>
</div>

<h2>최근 글</h2>
{% for p in recent %}
<a href="/post/{{ p.log_no }}" style="text-decoration:none"><div class="postrow">
  {% if p.thumb %}<img class="thumb" src="{{ p.thumb }}" loading="lazy">{% else %}<div class="thumb">📄</div>{% endif %}
  <div><div class="t">{{ p.title }}</div>
  <div class="m">{{ p.published_at[:10] }} · {{ p.category }} · ♥ {{ p.sympathy_count }} · 댓글 {{ p.comment_count }}</div></div>
</div></a>
{% endfor %}

<h2>동기화 이력</h2>
<table><tr><th>시작</th><th>모드</th><th>목록</th><th>신규</th><th>갱신</th><th>실패</th><th>비고</th></tr>
{% for r in s.runs %}
<tr><td>{{ r.started_at[:16].replace('T',' ') }}</td><td>{{ r.mode }}</td><td>{{ r.listed }}</td>
<td>{{ r.added }}</td><td>{{ r.updated }}</td><td>{{ r.failed }}</td><td>{{ r.note }}</td></tr>
{% endfor %}</table>
{% endblock %}"""

POSTS_HTML = """{% extends "base.html" %}{% block title %}글 목록{% endblock %}
{% block body %}
<h1>글 목록 <span style="color:var(--muted);font-size:14px">{{ total }}개</span></h1>
<form class="row" method="get" style="margin-bottom:16px">
  <input type="text" name="q" value="{{ q }}" placeholder="제목·본문 검색" style="width:260px">
  <select name="cat" onchange="this.form.submit()">
    <option value="">전체 카테고리</option>
    {% for c in cats %}<option value="{{ c.category }}" {{ 'selected' if c.category==cat }}>{{ c.category }} ({{ c.c }})</option>{% endfor %}
  </select>
  <button class="btn ghost">검색</button>
</form>
{% for p in posts %}
<a href="/post/{{ p.log_no }}" style="text-decoration:none"><div class="postrow">
  {% if p.thumb %}<img class="thumb" src="{{ p.thumb }}" loading="lazy">{% else %}<div class="thumb">📄</div>{% endif %}
  <div style="flex:1"><div class="t">{{ p.title }}
    {% if p.status=='missing' %}<span class="badge missing">블로그에서 사라짐</span>{% endif %}
    {% if p.status=='error' %}<span class="badge error">수집 실패</span>{% endif %}</div>
  <div class="m">{{ p.published_at[:10] }} · {{ p.category }} · ♥ {{ p.sympathy_count }} · 댓글 {{ p.comment_count }}
    {% if p.n_img %} · 🖼 {{ p.n_img }}{% endif %}</div>
  {% if p.brief %}<div class="m" style="margin-top:2px">{{ p.brief[:110] }}</div>{% endif %}</div>
</div></a>
{% else %}<div class="card">결과가 없습니다.</div>
{% endfor %}
<div class="pager">
  {% if page>1 %}<a class="btn ghost" href="?q={{ q }}&cat={{ cat }}&page={{ page-1 }}">← 이전</a>{% endif %}
  <span>{{ page }} / {{ pages }}</span>
  {% if page<pages %}<a class="btn ghost" href="?q={{ q }}&cat={{ cat }}&page={{ page+1 }}">다음 →</a>{% endif %}
</div>
{% endblock %}"""

POST_HTML = """{% extends "base.html" %}{% block title %}{{ p.title }}{% endblock %}
{% block body %}
<div class="row" style="justify-content:space-between;margin-bottom:10px">
  <a href="/posts">← 목록으로</a>
  <div class="row">
    {% if p.status=='missing' %}<span class="badge missing">블로그에서 사라짐 (아카이브 보존본)</span>{% endif %}
    <a class="btn ghost" href="{{ p.url }}" target="_blank">네이버 원본 ↗</a>
  </div>
</div>
<h1 style="margin-bottom:6px">{{ p.title }}</h1>
<div style="color:var(--muted);font-size:13px;margin-bottom:16px">
  {{ p.published_at[:16].replace('T',' ') }} · {{ p.category }} · ♥ {{ p.sympathy_count }} · 댓글 {{ p.comment_count }}
  · 이미지 {{ n_img }}{% if history %} · <a href="#history">수정이력 {{ history|length }}건</a>{% endif %}
</div>
<div class="card" style="margin-bottom:14px">
  <div class="row">
    <button class="btn" onclick="copyForNaver()">📋 네이버 재발행용 복사</button>
    <a class="btn ghost" id="write-link" href="https://blog.naver.com/{{ cfg.blog_id }}?Redirect=Write{% if p.category_no %}&categoryNo={{ p.category_no }}{% endif %}"
       target="_blank">글쓰기 창 열기 ↗</a>
    <button class="btn ghost" onclick="copyTitle()">제목만 복사</button>
    <span id="npaste-msg" style="color:var(--green);font-size:13px"></span>
  </div>
  <div style="color:var(--muted);font-size:12px;margin-top:8px">
    복사 후 글쓰기 창 <b>본문</b>에 Ctrl+V — 서식·이미지가 유지된 채 붙습니다 (제목은 별도 입력).
    다크 화면의 배경색은 딸려가지 않게 정리된 HTML을 사용합니다.</div>
</div>
<div class="tabs">
  <button class="on" id="tab-html" onclick="show('html')">본문 보기</button>
  <button id="tab-md" onclick="show('md')">Markdown</button>
</div>
<div id="view-html" class="se-viewer">{{ p.html_local|safe }}</div>
<div id="view-md" style="display:none">
  <button class="btn ghost" style="margin-bottom:8px" onclick="copyMd()">클립보드 복사</button>
  <textarea class="mdbox" id="mdsrc" readonly>{{ p.markdown }}</textarea>
</div>
{% if history %}
<h2 id="history">수정 이력</h2>
<table><tr><th>감지 시각</th><th>당시 제목</th></tr>
{% for h in history %}<tr><td>{{ h.changed_at[:16].replace('T',' ') }}</td><td>{{ h.title }}</td></tr>{% endfor %}
</table>
{% endif %}
<script>
function show(w){
  document.getElementById('view-html').style.display = w=='html'?'block':'none';
  document.getElementById('view-md').style.display = w=='md'?'block':'none';
  document.getElementById('tab-html').className = w=='html'?'on':'';
  document.getElementById('tab-md').className = w=='md'?'on':'';
}
function copyMd(){
  navigator.clipboard.writeText(document.getElementById('mdsrc').value);
}
function msg(t){ document.getElementById('npaste-msg').textContent = t; }
const POST_TITLE = {{ p.title|tojson }};
function copyTitle(){ navigator.clipboard.writeText(POST_TITLE); msg('제목 복사됨'); }
async function copyForNaver(){
  try{
    const r = await fetch('/api/post/{{ p.log_no }}/clipboard');
    const d = await r.json();
    const item = new ClipboardItem({
      'text/html': new Blob([d.html], {type: 'text/html'}),
      'text/plain': new Blob([d.text], {type: 'text/plain'})
    });
    await navigator.clipboard.write([item]);
    msg('복사됨! 글쓰기 창 본문에 Ctrl+V 하세요');
  }catch(e){ msg('복사 실패: ' + e); }
}
</script>
{% endblock %}"""

SYNC_HTML = """{% extends "base.html" %}{% block title %}동기화{% endblock %}
{% block body %}
<h1>동기화</h1>
<div class="card" style="margin-bottom:14px">
  <div class="row">
    <button class="btn" id="btn-incr" onclick="start('incr')">증분 동기화 (새 글·변경 글만)</button>
    <button class="btn ghost" id="btn-full" onclick="start('full')">전체 재수집</button>
    <label style="color:var(--muted)">개수 제한 <input type="number" id="limit" style="width:80px" placeholder="없음"></label>
    <button class="btn danger" id="btn-stop" onclick="stop()" style="display:none">중단</button>
  </div>
  <div class="progress"><div id="pbar"></div></div>
  <div id="ptext" style="color:var(--muted);font-size:13px">대기 중</div>
</div>
<div class="logbox" id="logbox"></div>
<script>
let polling=false;
async function tick(){
  const s = await (await fetch('/api/sync/status')).json();
  const pct = s.total ? Math.round(s.done/s.total*100) : (s.running?2:0);
  document.getElementById('pbar').style.width = pct+'%';
  document.getElementById('ptext').textContent = s.running
      ? `진행 ${s.done}/${s.total} — ${s.current||'목록 수집 중'}`
      : (s.result ? `완료 — 신규 ${s.result.added}, 갱신 ${s.result.updated}, 실패 ${s.result.failed}` : '대기 중');
  const lb=document.getElementById('logbox');
  lb.textContent = s.log.join('\\n');
  lb.scrollTop = lb.scrollHeight;
  document.getElementById('btn-incr').disabled = s.running;
  document.getElementById('btn-full').disabled = s.running;
  document.getElementById('btn-stop').style.display = s.running?'inline-block':'none';
  if(s.running){ setTimeout(tick, 800); polling=true; } else { polling=false; }
}
async function start(mode){
  const limit = document.getElementById('limit').value;
  await fetch('/api/sync/start', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({mode: mode, limit: limit?parseInt(limit):null})});
  if(!polling) tick();
}
async function stop(){ await fetch('/api/sync/stop', {method:'POST'}); }
tick();
</script>
{% endblock %}"""

CATS_HTML = """{% extends "base.html" %}{% block title %}카테고리{% endblock %}
{% block body %}
<h1>카테고리</h1>
<p style="color:var(--muted);margin-bottom:14px">slug는 Jekyll 내보내기의 카테고리 이름(URL)로 쓰입니다. 수정 후 저장을 누르세요.</p>
{% if saved %}<div class="flash">저장되었습니다.</div>{% endif %}
<table>
<tr><th>카테고리</th><th>글 수</th><th>Jekyll slug</th><th></th></tr>
{% for c in cats %}
<tr><td>{{ c.category }}</td><td>{{ c.c }}</td>
<td><form method="post" action="/categories/slug" class="row">
  <input type="hidden" name="kor" value="{{ c.category }}">
  <input type="text" name="slug" value="{{ c.slug }}" style="width:220px">
  <button class="btn ghost">저장</button></form></td>
<td>{% if c.is_excluded %}<span class="badge missing">Jekyll 제외</span>{% endif %}</td></tr>
{% endfor %}
</table>
{% endblock %}"""

EXPORT_HTML = """{% extends "base.html" %}{% block title %}내보내기{% endblock %}
{% block body %}
<h1>내보내기</h1>
{% if msg %}<div class="flash">{{ msg }}</div>{% endif %}
<div class="cards">
  <div class="card"><h2 style="margin-top:0">Jekyll</h2>
    <p style="color:var(--muted);font-size:13px;margin-bottom:12px">
      GitHub Pages 블로그용. _posts / _images / 카테고리 페이지 / nav_list_main 생성.<br>
      설정의 '제외 카테고리'가 적용됩니다. 이미지 링크는 설정의 base URL 사용.</p>
    <form method="post" action="/export/run"><input type="hidden" name="format" value="jekyll">
    <button class="btn" onclick="this.textContent='내보내는 중...';">Jekyll 내보내기</button></form></div>
  <div class="card"><h2 style="margin-top:0">Markdown</h2>
    <p style="color:var(--muted);font-size:13px;margin-bottom:12px">
      순수 markdown 파일 + images 폴더. 제외 없이 전체 글. 로컬 보관/옵시디언용.</p>
    <form method="post" action="/export/run"><input type="hidden" name="format" value="markdown">
    <button class="btn" onclick="this.textContent='내보내는 중...';">Markdown 내보내기</button></form></div>
  <div class="card"><h2 style="margin-top:0">JSON 덤프</h2>
    <p style="color:var(--muted);font-size:13px;margin-bottom:12px">
      DB 전체(글·이미지 메타·수정이력)를 JSON 한 파일로. 2차 가공/마이그레이션용.</p>
    <form method="post" action="/export/run"><input type="hidden" name="format" value="json">
    <button class="btn" onclick="this.textContent='내보내는 중...';">JSON 내보내기</button></form></div>
  <div class="card"><h2 style="margin-top:0">🚀 GitHub Pages 배포</h2>
    <p style="color:var(--muted);font-size:13px;margin-bottom:12px">
      Jekyll 내보내기 → 블로그 저장소 반영 → commit → push 원클릭.<br>
      저장소: <code>{{ cfg.jekyll_repo_dir or '설정에서 지정 필요' }}</code></p>
    <form method="post" action="/export/run"><input type="hidden" name="format" value="publish">
    <button class="btn" onclick="this.textContent='배포 중... (이미지 푸시로 수 분 걸릴 수 있음)';"
      {{ 'disabled' if not cfg.jekyll_repo_dir }}>블로그 배포</button></form></div>
</div>
<h2>Jekyll 내보내기 대상 미리보기 <span style="color:var(--muted);font-size:13px">
  — 포함 {{ inc_total }}개 / 제외 {{ exc_total }}개 (제외 목록은 설정에서 수정)</span></h2>
<table><tr><th>카테고리</th><th>글 수</th><th>Jekyll</th></tr>
{% for c in preview %}
<tr><td>{{ c.category or '(없음)' }}</td><td>{{ c.c }}</td>
<td>{% if c.included %}<span class="badge ok">포함</span>{% else %}<span class="badge missing">제외</span>{% endif %}</td></tr>
{% endfor %}</table>
{% endblock %}"""

SETTINGS_HTML = """{% extends "base.html" %}{% block title %}설정{% endblock %}
{% block body %}
<h1>설정</h1>
{% if saved %}<div class="flash">저장되었습니다. blog_id를 바꿨다면 해당 블로그의 아카이브 폴더가 새로 만들어집니다.</div>{% endif %}
<form method="post" class="card" style="display:flex;flex-direction:column;gap:14px;max-width:640px">
  <label>블로그 ID<br><input type="text" name="blog_id" value="{{ cfg.blog_id }}" style="width:100%"></label>
  <label>요청 간격(초) — 네이버 서버 배려용<br>
    <input type="number" name="request_delay" value="{{ cfg.request_delay }}" step="0.1" min="0" style="width:120px"></label>
  <label><input type="checkbox" name="image_original_quality" {{ 'checked' if cfg.image_original_quality }}>
    이미지 원본 화질로 저장 (blogfiles / type=w3840 시도)</label>
  <label>Jekyll 제외 카테고리 (쉼표 구분 — 백업은 전부 저장되고, Jekyll 내보내기에서만 제외)<br>
    <textarea name="excluded_categories" rows="3" style="width:100%">{{ cfg.excluded_categories|join(', ') }}</textarea></label>
  <label>Jekyll 이미지 base URL<br>
    <input type="text" name="jekyll_image_base_url" value="{{ cfg.jekyll_image_base_url }}" style="width:100%"></label>
  <label>GitHub Pages 저장소 로컬 경로 (publish용)<br>
    <input type="text" name="jekyll_repo_dir" value="{{ cfg.jekyll_repo_dir }}" style="width:100%"
           placeholder="C:\\github\\username.github.io"></label>
  <label><input type="checkbox" name="publish_after_sync" {{ 'checked' if cfg.publish_after_sync }}>
    동기화 후 자동으로 블로그 배포 (변경이 있을 때만)</label>
  <div><button class="btn">저장</button></div>
</form>
<div class="card" style="margin-top:14px;color:var(--muted);font-size:13px;line-height:1.8">
  아카이브 위치: <code>{{ paths.base }}</code><br>
  DB: <code>{{ paths.db }}</code>
</div>
{% endblock %}"""


def create_app(cfg: dict):
    from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
    from jinja2 import DictLoader

    app = Flask(__name__)
    app.jinja_loader = DictLoader({
        "base.html": BASE_HTML, "dash.html": DASH_HTML, "posts.html": POSTS_HTML,
        "post.html": POST_HTML, "sync.html": SYNC_HTML, "cats.html": CATS_HTML,
        "export.html": EXPORT_HTML, "settings.html": SETTINGS_HTML,
    })

    def side_counts():
        con = open_db(cfg)
        p = con.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
        i = con.execute("SELECT COUNT(*) c FROM images WHERE ok=1").fetchone()["c"]
        con.close()
        return {"side_posts": p, "side_images": i, "cfg": cfg}

    def local_thumb(con, row):
        """목록 썸네일: 로컬 이미지 우선, 없으면 네이버 CDN (온라인일 때만 표시됨)."""
        img = con.execute(
            "SELECT filename FROM images WHERE log_no=? AND ok=1 ORDER BY seq LIMIT 1",
            (row["log_no"],)).fetchone()
        if img:
            return f"/media/{row['log_no']}/{img['filename']}"
        return row["thumbnail_url"] or ""

    @app.route("/")
    def dash():
        s = get_stats(cfg)
        con = open_db(cfg)
        recent = []
        for r in con.execute("SELECT * FROM posts ORDER BY published_at DESC LIMIT 8"):
            d = dict(r)
            d["thumb"] = local_thumb(con, r)
            recent.append(d)
        con.close()
        last = s["runs"][0] if s["runs"] else None
        return render_template(
            "dash.html", active="dash", s=s, recent=recent,
            size_str=fmt_bytes(s["image_bytes"]),
            max_cat=max([c["c"] for c in s["categories"]] or [1]),
            max_year=max([y["c"] for y in s["years"]] or [1]),
            last_sync=(last["started_at"][:16].replace("T", " ") if last else "없음"),
            last_sync_sub=(f"{last['mode']} · 신규 {last['added']} · 실패 {last['failed']}" if last else "동기화를 실행하세요"),
            **side_counts())

    @app.route("/posts")
    def posts():
        q = request.args.get("q", "").strip()
        cat = request.args.get("cat", "").strip()
        page = max(1, int(request.args.get("page", 1)))
        per = 20
        con = open_db(cfg)
        where, args = [], []
        if q:
            where.append("(title LIKE ? OR markdown LIKE ?)")
            args += [f"%{q}%", f"%{q}%"]
        if cat:
            where.append("category=?")
            args.append(cat)
        wsql = ("WHERE " + " AND ".join(where)) if where else ""
        total = con.execute(f"SELECT COUNT(*) c FROM posts {wsql}", args).fetchone()["c"]
        rows = con.execute(
            f"""SELECT p.*, (SELECT COUNT(*) FROM images i WHERE i.log_no=p.log_no AND i.ok=1) n_img
                FROM posts p {wsql} ORDER BY published_at DESC LIMIT ? OFFSET ?""",
            args + [per, (page - 1) * per]).fetchall()
        plist = []
        for r in rows:
            d = dict(r)
            d["thumb"] = local_thumb(con, r)
            plist.append(d)
        cats = con.execute(
            "SELECT category, COUNT(*) c FROM posts GROUP BY category ORDER BY c DESC").fetchall()
        con.close()
        return render_template("posts.html", active="posts", posts=plist, total=total,
                               q=q, cat=cat, cats=cats, page=page,
                               pages=max(1, -(-total // per)), **side_counts())

    @app.route("/post/<int:log_no>")
    def post(log_no):
        con = open_db(cfg)
        p = con.execute("SELECT * FROM posts WHERE log_no=?", (log_no,)).fetchone()
        if not p:
            con.close()
            return "글이 없습니다", 404
        n_img = con.execute("SELECT COUNT(*) c FROM images WHERE log_no=? AND ok=1",
                            (log_no,)).fetchone()["c"]
        history = con.execute(
            "SELECT changed_at, title FROM posts_history WHERE log_no=? ORDER BY id DESC",
            (log_no,)).fetchall()
        con.close()
        return render_template("post.html", active="posts", p=p, n_img=n_img,
                               history=history, **side_counts())

    @app.route("/media/<int:log_no>/<path:fname>")
    def media(log_no, fname):
        return send_from_directory(blog_paths(cfg)["images"] / str(log_no), fname)

    @app.route("/api/post/<int:log_no>/clipboard")
    def post_clipboard(log_no):
        """네이버 에디터 붙여넣기용 정리된 HTML.
        이미지: 살아있는 글 → 원본 CDN URL(네이버가 재첨부), 사라진 글 → 로컬 서버 URL."""
        con = open_db(cfg)
        p = con.execute("SELECT * FROM posts WHERE log_no=?", (log_no,)).fetchone()
        if not p:
            con.close()
            return jsonify({"error": "글이 없습니다"}), 404
        imgs = con.execute("SELECT seq, src_url, filename, ok FROM images WHERE log_no=? ORDER BY seq",
                           (log_no,)).fetchall()
        con.close()
        port = cfg.get("web_port", 8765)
        srcs = []
        for r in imgs:
            if p["status"] == "ok" and r["src_url"]:
                srcs.append(r["src_url"])                      # 네이버 CDN 원본 (에디터가 fetch 가능)
            elif r["ok"] and r["filename"]:
                srcs.append(f"http://127.0.0.1:{port}/media/{log_no}/{r['filename']}")
            else:
                srcs.append(None)
        soup = clean_content_soup(p["html_raw"], srcs)
        return jsonify({"title": p["title"], "html": str(soup), "text": p["markdown"],
                        "write_url": f"https://blog.naver.com/{cfg['blog_id']}?Redirect=Write"
                                     + (f"&categoryNo={p['category_no']}" if p["category_no"] else "")})

    @app.route("/sync")
    def sync_page():
        return render_template("sync.html", active="sync", **side_counts())

    @app.route("/api/sync/status")
    def sync_status():
        st = dict(SYNC_STATE)
        st["log"] = st["log"][-200:]
        return jsonify(st)

    @app.route("/api/sync/start", methods=["POST"])
    def sync_start():
        if SYNC_STATE["running"]:
            return jsonify({"error": "이미 실행 중"}), 409
        body = request.get_json(silent=True) or {}
        full = body.get("mode") == "full"
        limit = body.get("limit")
        SYNC_STATE.update(running=True, mode=body.get("mode", "incr"), total=0, done=0,
                          current="", stop=False, log=[], result=None)

        def worker():
            def weblog(msg):
                SYNC_STATE["log"].append(msg)
            try:
                res = run_sync(cfg, full=full, limit=limit, state=SYNC_STATE, log=weblog)
                SYNC_STATE["result"] = res
            except Exception as e:
                SYNC_STATE["log"].append(f"[오류] {e}")
            finally:
                SYNC_STATE["running"] = False
        threading.Thread(target=worker, daemon=True).start()
        return jsonify({"ok": True})

    @app.route("/api/sync/stop", methods=["POST"])
    def sync_stop():
        SYNC_STATE["stop"] = True
        return jsonify({"ok": True})

    @app.route("/categories")
    def cats_page():
        con = open_db(cfg)
        cats = []
        for r in con.execute("SELECT category, COUNT(*) c FROM posts GROUP BY category ORDER BY c DESC"):
            cats.append({"category": r["category"], "c": r["c"], "slug": get_slug(con, r["category"] or "기타")})
        con.close()
        excluded = {_norm_cat(c) for c in cfg.get("excluded_categories", [])}
        for c in cats:
            c["is_excluded"] = _norm_cat(c["category"]) in excluded
        return render_template("cats.html", active="cats", cats=cats, excluded=excluded,
                               saved=request.args.get("saved"), **side_counts())

    @app.route("/categories/slug", methods=["POST"])
    def cats_slug():
        kor = request.form.get("kor", "")
        slug = re.sub(r"[^A-Za-z0-9_-]", "", request.form.get("slug", "")) or category_slug(kor)
        con = open_db(cfg)
        con.execute("INSERT OR REPLACE INTO category_map(kor, slug) VALUES(?,?)", (kor, slug))
        con.commit()
        con.close()
        return redirect(url_for("cats_page", saved=1))

    @app.route("/export")
    def export_page():
        con = open_db(cfg)
        excluded = {_norm_cat(c) for c in cfg.get("excluded_categories", [])}
        preview, inc_total, exc_total = [], 0, 0
        for r in con.execute("SELECT category, COUNT(*) c FROM posts GROUP BY category ORDER BY c DESC"):
            inc = _norm_cat(r["category"]) not in excluded
            preview.append({"category": r["category"], "c": r["c"], "included": inc})
            if inc:
                inc_total += r["c"]
            else:
                exc_total += r["c"]
        con.close()
        return render_template("export.html", active="export", msg=request.args.get("msg"),
                               preview=preview, inc_total=inc_total, exc_total=exc_total,
                               **side_counts())

    @app.route("/export/run", methods=["POST"])
    def export_run():
        fmt = request.form.get("format")
        fn = {"jekyll": export_jekyll, "markdown": export_markdown, "json": export_json,
              "publish": publish_jekyll}.get(fmt)
        if not fn:
            return redirect(url_for("export_page", msg="알 수 없는 형식"))
        try:
            r = fn(cfg)
            if fmt == "publish":
                msg = (f"블로그 배포 완료 — 글 {r['count']}개, 변경 {r['changed']}개 파일 push"
                       if r["pushed"] else "변경 없음 — 배포 생략")
            else:
                msg = f"{fmt} 내보내기 완료 — 글 {r['count']}개 → {r['dest']}"
        except Exception as e:
            msg = f"내보내기 실패: {e}"
        return redirect(url_for("export_page", msg=msg))

    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        saved = False
        if request.method == "POST":
            cfg["blog_id"] = request.form.get("blog_id", cfg["blog_id"]).strip()
            try:
                cfg["request_delay"] = float(request.form.get("request_delay", cfg["request_delay"]))
            except ValueError:
                pass
            cfg["image_original_quality"] = bool(request.form.get("image_original_quality"))
            cfg["excluded_categories"] = [c.strip() for c in
                                          request.form.get("excluded_categories", "").split(",") if c.strip()]
            cfg["jekyll_image_base_url"] = request.form.get("jekyll_image_base_url", "").strip()
            cfg["jekyll_repo_dir"] = request.form.get("jekyll_repo_dir", "").strip()
            cfg["publish_after_sync"] = bool(request.form.get("publish_after_sync"))
            save_config(cfg)
            saved = True
        return render_template("settings.html", active="settings", saved=saved,
                               paths=blog_paths(cfg), **side_counts())

    return app


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="네이버 블로그 아카이버 v2")
    sub = ap.add_subparsers(dest="cmd")

    sp = sub.add_parser("sync", help="블로그 동기화 (기본: 증분)")
    sp.add_argument("--full", action="store_true", help="전체 재수집 (수정 감지·이력 보존)")
    sp.add_argument("--limit", type=int, help="수집 글 개수 제한 (테스트용)")
    sp.add_argument("--blog", help="블로그 ID (기본: config.json)")

    wp = sub.add_parser("web", help="웹 UI 실행")
    wp.add_argument("--port", type=int, help="포트 (기본: config)")
    wp.add_argument("--no-browser", action="store_true", help="브라우저 자동 열기 끔")

    ep = sub.add_parser("export", help="내보내기")
    ep.add_argument("--format", choices=["jekyll", "markdown", "json"], required=True)
    ep.add_argument("--dest", help="출력 경로 (기본: archive/<blog>/exports/)")

    sub.add_parser("publish", help="Jekyll 내보내기 후 GitHub Pages 저장소에 commit+push")
    sub.add_parser("stats", help="아카이브 통계")
    qp = sub.add_parser("search", help="제목·본문 검색")
    qp.add_argument("query")
    sub.add_parser("rebuild", help="저장된 HTML로 markdown/뷰어 재생성")

    args = ap.parse_args()
    cfg = load_config()

    if args.cmd == "sync":
        if args.blog:
            cfg["blog_id"] = args.blog
        run_sync(cfg, full=args.full, limit=args.limit)
    elif args.cmd == "web":
        port = args.port or cfg.get("web_port", 8765)
        app = create_app(cfg)
        url = f"http://127.0.0.1:{port}"
        print(f"웹 UI: {url}  (Ctrl+C로 종료)")
        if not args.no_browser:
            import webbrowser
            threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        app.run(host="127.0.0.1", port=port, debug=False)
    elif args.cmd == "export":
        fn = {"jekyll": export_jekyll, "markdown": export_markdown, "json": export_json}[args.format]
        fn(cfg, dest=Path(args.dest) if args.dest else None)
    elif args.cmd == "publish":
        publish_jekyll(cfg)
    elif args.cmd == "stats":
        s = get_stats(cfg)
        print(f"블로그: {cfg['blog_id']}")
        print(f"글 {s['posts']}개 (missing {s['missing']}, 오류 {s['errors']}, 수정이력 {s['history']}건)")
        print(f"이미지 {s['images']}개 ({fmt_bytes(s['image_bytes'])}, 실패 {s['image_failed']})")
        print("카테고리:")
        for c in s["categories"]:
            print(f"  {c['category'] or '(없음)'}: {c['c']}")
        if s["runs"]:
            r = s["runs"][0]
            print(f"마지막 동기화: {r['started_at']} ({r['mode']}, 신규 {r['added']}, 실패 {r['failed']})")
    elif args.cmd == "search":
        con = open_db(cfg)
        rows = con.execute(
            """SELECT log_no, title, category, published_at FROM posts
               WHERE title LIKE ? OR markdown LIKE ? ORDER BY published_at DESC LIMIT 30""",
            (f"%{args.query}%", f"%{args.query}%")).fetchall()
        for r in rows:
            print(f"[{r['published_at'][:10]}] ({r['category']}) {r['title']}  — https://blog.naver.com/{cfg['blog_id']}/{r['log_no']}")
        print(f"\n{len(rows)}건 (최대 30)")
        con.close()
    elif args.cmd == "rebuild":
        run_rebuild(cfg)
    elif getattr(sys, "frozen", False):
        # exe 더블클릭(인자 없음) → 웹 UI 실행
        port = cfg.get("web_port", 8765)
        app = create_app(cfg)
        url = f"http://127.0.0.1:{port}"
        print(f"웹 UI: {url}  (이 창을 닫으면 종료됩니다)")
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        app.run(host="127.0.0.1", port=port, debug=False)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
