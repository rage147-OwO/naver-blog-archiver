"""Synchronize the GitHub Pages tree without checking out duplicate image files."""

import mimetypes
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup

from blog_archiver import _norm_cat, blog_paths, export_jekyll, image_filename, now_iso, open_db


BRANCH = "refs/heads/master"
POSTS_DIR = "_posts/NaverBackup/"
IMAGES_DIR = "_images/"
CATEGORIES_DIR = "_pages/categories/"
NAVIGATION = "_includes/nav_list_main"
PUSH_BYTES = 1024**3
MAX_BLOB_BYTES = 100 * 1024**2


@dataclass
class OldPost:
    path: str
    title: str
    date: str
    category: str
    url: str
    markdown: str


@dataclass
class Change:
    path: str
    object_id: str = ""
    size: int = 0


class PagesRepository:
    def __init__(self, path, remote, log):
        self.path = path
        self.log = log
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(prefix="pages-clone-", dir=self.path.parent) as scratch:
                clone = Path(scratch) / "repo.git"
                self.run("clone", "--bare", "--depth=1", "--single-branch", "--branch", "master",
                         remote, str(clone), outside=True)
                clone.rename(self.path)
        if self.git("rev-parse", "--is-bare-repository").strip() != b"true":
            raise RuntimeError("GitHub Pages 자동 발행에는 전용 bare 저장소가 필요합니다")
        if self.git("remote", "get-url", "origin").decode().strip() != remote:
            raise RuntimeError("GitHub Pages 원격 저장소 주소가 일치하지 않습니다")

    def run(self, *args, data=None, env=None, outside=False):
        command = ["git"] if outside else ["git", "-C", str(self.path)]
        result = subprocess.run(
            command + list(args), input=data, capture_output=True, env=env, timeout=1800
        )
        if result.returncode:
            detail = result.stderr.decode("utf-8", "replace").strip()
            raise RuntimeError(f"git {args[0]} 실패: {detail[-800:]}")
        return result.stdout

    def git(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def fetch(self):
        self.git("fetch", "--no-tags", "--depth=1", "origin", f"+{BRANCH}:{BRANCH}")
        return self.git("rev-parse", BRANCH).decode().strip()

    def entries(self, commit):
        entries = {}
        paths = [POSTS_DIR, IMAGES_DIR, CATEGORIES_DIR, NAVIGATION]
        for line in self.git("ls-tree", "-r", "-z", commit, "--", *paths).split(b"\0"):
            if line:
                info, name = line.split(b"\t", 1)
                mode, kind, object_id = info.decode("ascii").split()
                if kind == "blob" and mode in ("100644", "100755"):
                    entries[name.decode("utf-8")] = object_id
        return entries

    def changed_file(self, path, source, entries):
        size = source.stat().st_size
        if size >= MAX_BLOB_BYTES:
            raise ValueError(f"GitHub 파일 크기 제한 초과: {path}")
        object_id = self.git("hash-object", "-w", "--", str(source)).decode().strip()
        if entries.get(path) != object_id:
            return Change(path, object_id, size)
        return None

    def push(self, base, groups, index):
        import os

        env = dict(os.environ, GIT_INDEX_FILE=str(index))
        self.git("read-tree", base, env=env)
        changed = pushed = 0
        for changes in batches(groups):
            index_entries = bytearray()
            for change in changes:
                item = (f"100644 {change.object_id}" if change.object_id else "0 " + "0" * len(base))
                index_entries.extend(f"{item}\t{change.path}\0".encode("utf-8"))
            self.git("update-index", "-z", "--index-info", data=bytes(index_entries), env=env)
            tree = self.git("write-tree", env=env).decode().strip()
            old_tree = self.git("rev-parse", f"{base}^{{tree}}").decode().strip()
            if tree == old_tree:
                continue
            message = f"네이버 블로그 동기화 {now_iso()[:16]} ({len(changes)}개 파일)"
            commit = self.git("commit-tree", tree, "-p", base, "-m", message).decode().strip()
            self.git("push", "origin", f"{commit}:{BRANCH}")
            self.git("update-ref", BRANCH, commit, base)
            self.log(f"GitHub 게시 완료: {commit[:12]} ({len(changes)}개 파일)")
            base = commit
            changed += len(changes)
            pushed += 1
        return changed, pushed


def batches(groups):
    batch, size = [], 0
    for group in groups:
        group_size = sum(change.size for change in group)
        if batch and size + group_size > PUSH_BYTES:
            yield batch
            batch, size = [], 0
        for change in group:
            if batch and size + change.size > PUSH_BYTES:
                yield batch
                batch, size = [], 0
            batch.append(change)
            size += change.size
    if batch:
        yield batch


def find_old_posts(repo, entries, blog_id):
    records = defaultdict(list)
    naver_url = re.compile(
        rf"(?m)^naver_url:\s*(https?://(?:m\.)?blog\.naver\.com/{re.escape(blog_id)}/(\d+))\s*$",
        re.IGNORECASE,
    )
    for path, object_id in entries.items():
        if not path.startswith(POSTS_DIR) or not path.endswith(".md"):
            continue
        text = repo.git("cat-file", "blob", object_id).decode("utf-8").replace("\r\n", "\n")
        front, sep, body = text.removeprefix("---\n").partition("\n---\n")
        match = naver_url.search(front) if sep and text.startswith("---\n") else None
        if not match:
            continue
        title = re.search(r"(?m)^title:[ \t]*(.*)$", front)
        date = re.search(r"(?m)^date:[ \t]*(\d{4}-\d{2}-\d{2})", front)
        category = re.search(r"""(?m)^categories:[ \t]*\n[ \t]*-[ \t]*["']?([\w-]+)""", front)
        records[int(match[2])].append(OldPost(
            path=path,
            title=title[1].strip().strip('"').replace('\\"', '"') if title else PurePosixPath(path).stem,
            date=date[1] if date else "",
            category=category[1] if category else "",
            url=match[1],
            markdown=body.lstrip("\n"),
        ))
    return records


def archive_removed(cfg, con, repo, entries, posts, log_no):
    """Keep previously published content even on a fresh server without a Naver copy."""
    original = con.execute("SELECT html_raw FROM posts WHERE log_no=?", (log_no,)).fetchone()
    if original and original["html_raw"]:
        return
    import markdown

    post = posts[0]
    prefix = f"{IMAGES_DIR}{log_no}/"
    image_dir = blog_paths(cfg)["images"] / str(log_no)
    images = []
    for path, object_id in entries.items():
        if not path.startswith(prefix) or len(PurePosixPath(path).parts) != 3:
            continue
        filename = PurePosixPath(path).name
        image_dir.mkdir(parents=True, exist_ok=True)
        target = image_dir / filename
        if not target.exists():
            content = repo.git("cat-file", "blob", object_id)
            temporary = target.with_name(f".{target.name}.import")
            temporary.write_bytes(content)
            temporary.replace(target)
        images.append((log_no, len(images), filename, mimetypes.guess_type(filename)[0] or "",
                       target.stat().st_size, 1))

    raw_prefix = re.compile(
        rf"https://raw\.githubusercontent\.com/[^/\s]+/[^/\s]+/[^/\s]+/_images/{log_no}/",
        re.IGNORECASE,
    )
    stored_markdown = raw_prefix.sub(f"images/{log_no}/", post.markdown)
    display = BeautifulSoup(markdown.markdown(stored_markdown, extensions=["extra"]), "html.parser")
    for node in display.find_all(["script", "iframe", "object", "embed"]):
        node.decompose()
    for node in display.find_all(True):
        for name in list(node.attrs):
            value = node[name]
            if name.lower().startswith("on") or (
                name in ("href", "src") and str(value).strip().lower().startswith("javascript:")
            ):
                del node[name]
        if node.name == "img" and node.get("src", "").startswith(f"images/{log_no}/"):
            node["src"] = "/" + node["src"].replace("images/", "media/", 1)
    timestamp = now_iso()
    with con:
        con.execute("""INSERT INTO posts(
                         log_no,blog_id,title,category,published_at,url,html_raw,html_local,markdown,
                         status,first_synced_at,updated_at
                       ) VALUES(?,?,?,?,?,?,?,?,?,'missing',?,?)
                       ON CONFLICT(log_no) DO UPDATE SET
                         title=excluded.title,category=excluded.category,published_at=excluded.published_at,
                         url=excluded.url,html_raw=excluded.html_raw,html_local=excluded.html_local,
                         markdown=excluded.markdown,status='missing',error='',updated_at=excluded.updated_at
                    """, (log_no, cfg["blog_id"], post.title, post.category, post.date, post.url,
                          str(display), str(display), stored_markdown, timestamp, timestamp))
        con.execute("DELETE FROM images WHERE log_no=?", (log_no,))
        con.executemany(
            "INSERT INTO images(log_no,seq,filename,content_type,bytes,ok) VALUES(?,?,?,?,?,?)", images
        )


def image_changes(repo, entries, image_dir, images, prefix):
    changes = []
    for filename in images:
        source = image_dir / filename
        if not source.is_file():
            raise ValueError(f"보관된 이미지가 없습니다: {filename}")
        change = repo.changed_file(prefix + filename, source, entries)
        if change:
            changes.append(change)
    for path in entries:
        if path.startswith(prefix) and path[len(prefix):] not in images:
            changes.append(Change(path))
    return changes


def configured_repository(cfg, log):
    remote = cfg.get("pages_git_url")
    target = cfg.get("jekyll_repo_dir")
    if not remote or not target or cfg["blog_id"] != cfg.get("pages_blog_id"):
        raise RuntimeError("GitHub Pages 자동 발행 대상이 설정과 일치하지 않습니다")
    return PagesRepository(Path(target), remote, log)


def published_image_cache(cfg, log):
    log("GitHub에 이미 보관된 이미지 확인 중")
    repo = configured_repository(cfg, log)
    entries = {}
    for path, object_id in repo.entries(repo.fetch()).items():
        if not path.startswith(IMAGES_DIR):
            continue
        parts = PurePosixPath(path).parts
        if len(parts) == 3 and parts[1].isdigit():
            entries[(int(parts[1]), PurePosixPath(parts[2]).stem)] = (parts[2], object_id)

    def cached_image(log_no, source):
        saved = entries.get((log_no, image_filename(source, "")))
        if not saved:
            return None
        filename, object_id = saved
        media_type, _ = mimetypes.guess_type(filename)
        if not media_type:
            return None
        return repo.git("cat-file", "blob", object_id), media_type, source

    return cached_image


def publish_public(cfg, public_ids, failed_ids=(), log=None):
    log = log or (lambda message: print(message, flush=True))
    log("GitHub Pages 게시본과 비교 중")
    repo = configured_repository(cfg, log)
    base = repo.fetch()
    entries = repo.entries(base)
    previous = find_old_posts(repo, entries, cfg["blog_id"])
    con = open_db(cfg)

    try:
        return apply_publication(cfg, con, repo, base, entries, previous, public_ids, set(failed_ids), log)
    finally:
        con.close()


def apply_publication(cfg, con, repo, base, entries, previous, public_ids, failed, log):
    excluded_categories = {_norm_cat(category) for category in cfg["excluded_categories"]}
    archive_images = blog_paths(cfg)["images"]
    pending, excluded, all_images = [], set(), {}
    skipped = 0
    for row in con.execute("SELECT * FROM posts WHERE status='ok' AND html_raw != '' ORDER BY published_at, log_no"):
        log_no = row["log_no"]
        if log_no not in public_ids or log_no in failed:
            continue
        if _norm_cat(row["category"]) in excluded_categories:
            excluded.add(log_no)
            continue
        images = {image["filename"] for image in con.execute(
            "SELECT filename, ok FROM images WHERE log_no=?",
            (log_no,),
        ) if image["ok"]}
        if any(not (archive_images / str(log_no) / name).is_file()
               or (archive_images / str(log_no) / name).stat().st_size >= MAX_BLOB_BYTES for name in images):
            skipped += 1
            log(f"[게시 보류] {log_no}: 이미지 누락 또는 100 MiB 제한")
            continue
        pending.append(row)
        all_images[log_no] = images

    removed = set(previous) - (public_ids - excluded)
    for log_no in sorted(removed - excluded):
        archive_removed(cfg, con, repo, entries, previous[log_no], log_no)
    groups = []
    for log_no in sorted(removed):
        prefix = f"{IMAGES_DIR}{log_no}/"
        deletes = [Change(post.path) for post in previous[log_no]]
        deletes.extend(Change(path) for path in entries if path.startswith(prefix))
        groups.append(deletes)

    retained = {post.category: post.category
                for log_no in previous.keys() - removed - all_images.keys()
                for post in previous[log_no] if post.category}
    with TemporaryDirectory(prefix="pages-publish-") as scratch:
        scratch = Path(scratch)
        export_dir = scratch / "jekyll"
        exported = export_jekyll(cfg, export_dir, log=log, posts=pending,
                                  retained_categories=retained.items(), include_images=False)
        occupied = set(entries)
        for log_no, post_file in exported["post_files"].items():
            old = previous.get(log_no)
            path = old[0].path if old else POSTS_DIR + post_file.name
            if not old and path in occupied:
                path = POSTS_DIR + f"{post_file.stem}-{log_no}.md"
                while path in occupied:
                    path = path.removesuffix(".md") + f"-{log_no}.md"
            occupied.add(path)
            prefix = f"{IMAGES_DIR}{log_no}/"
            images = image_changes(repo, entries, archive_images / str(log_no), all_images[log_no], prefix)
            post_change = repo.changed_file(path, post_file, entries)
            group = [image for image in images if image.object_id]
            if post_change:
                group.append(post_change)
            group.extend(image for image in images if not image.object_id)
            groups.append(group)

        category_updates = []
        category_dir = export_dir / CATEGORIES_DIR
        for file in sorted(category_dir.iterdir()):
            change = repo.changed_file(CATEGORIES_DIR + file.name, file, entries)
            if change:
                category_updates.append(change)
        old_slugs = {post.category for posts in previous.values() for post in posts if post.category}
        for slug in sorted(old_slugs):
            filename = f"category-{slug}.md"
            path = CATEGORIES_DIR + filename
            if path in entries and not (category_dir / filename).exists():
                category_updates.append(Change(path))
        navigation = repo.changed_file(NAVIGATION, export_dir / "nav_list_main", entries)
        if navigation:
            category_updates.append(navigation)
        groups.append(category_updates)

        changed, pushed = repo.push(base, groups, scratch / "index")
        log(f"게시 결과: 공개 글 내림 {len(removed)}개, 변경 {changed}개 파일, 푸시 {pushed}회")
        return {"count": len(pending), "changed": changed, "pushed": bool(pushed),
                "removed": len(removed), "skipped": skipped, "dest": str(repo.path)}
