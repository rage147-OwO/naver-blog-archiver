"""On-demand ZIP downloads of public Naver Blog posts."""

import errno
import json
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlsplit
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import requests
from flask import Flask, jsonify, render_template, request, send_file

from blog_archiver import (
    NaverClient, build_outputs, extract_main, image_filename, parse_post_content, sanitize_filename,
)


BLOG_HOSTS = {"blog.naver.com", "m.blog.naver.com"}
IMAGE_HOSTS = {
    "postfiles.pstatic.net", "blogfiles.pstatic.net", "blogthumb.pstatic.net",
    "mblogthumb-phinf.pstatic.net", "blogthumb-phinf.pstatic.net",
}
IMAGE_TYPES = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
    "image/webp": ".webp", "image/bmp": ".bmp",
}
MIN_DISK_FREE_BYTES = 2 * 1024**3
TEXT_DISK_HEADROOM_BYTES = 256 * 1024**2
REQUEST_DEADLINE_SECONDS = 30
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}
MAX_PENDING = 3
MAX_JOBS = 8
JOB_TTL = 30 * 60
CLIENT_COOLDOWN = 60
DISK_SPACE_ERROR = "서버 저장 공간이 부족해 ZIP을 만들지 못했습니다. 잠시 후 다시 시도해 주세요."


class BackupError(RuntimeError):
    """An expected failure that can be shared with the visitor."""


def blog_id_from_url(value):
    if not isinstance(value, str) or len(value) > 500:
        raise BackupError("네이버 블로그 주소를 입력해 주세요.")
    address = value.strip()
    if "://" not in address:
        address = "https://" + address
    try:
        link = urlsplit(address)
        path = link.path.strip("/").split("/")
        if link.scheme not in {"http", "https"} or link.netloc.lower() not in BLOG_HOSTS:
            raise ValueError
        if link.path in {"/PostList.naver", "/PostView.naver"}:
            blog_id, = parse_qs(link.query).get("blogId", ())
        elif len(path) == 1 or (len(path) == 2 and path[1].isdigit()):
            blog_id = path[0]
        else:
            raise ValueError
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", blog_id):
            raise ValueError
        return blog_id
    except (ValueError, UnicodeError):
        raise BackupError("blog.naver.com 또는 m.blog.naver.com의 블로그 주소를 입력해 주세요.") from None


def parse_date_range(data):
    try:
        start, end = (date.fromisoformat(data[key]) if data.get(key) else None for key in ("start", "end"))
        if start and end and start > end:
            raise ValueError
        return start, end
    except (ValueError, TypeError):
        raise BackupError("시작일과 종료일을 확인해 주세요.") from None


@dataclass
class PageResponse:
    content: bytes

    @property
    def text(self):
        return self.content.decode("utf-8-sig")

    def json(self):
        return json.loads(self.text)


class BackupClient(NaverClient):
    def __init__(self, blog_id):
        super().__init__(blog_id)
        self.s.trust_env = False
        self.s.headers["User-Agent"] = "NaverBlogZipBackup/1.0"
        self.last_request = 0.0

    def download(self, url, max_bytes, image=False):
        for attempt in range(3):
            try:
                return self._download_once(url, max_bytes, image)
            except requests.RequestException as error:
                response = error.response
                if attempt == 2 or (response is not None and response.status_code not in RETRYABLE_HTTP_STATUS):
                    raise
                delay = 2 ** (attempt + 1)
                if response is not None:
                    retry_after = response.headers.get("Retry-After", "")
                    if retry_after.isascii() and retry_after.isdecimal():
                        delay = max(delay, int(retry_after))
                if delay > 120:
                    raise BackupError("네이버에서 백업 요청을 잠시 제한했습니다. 잠시 후 다시 시도해 주세요.") from error
                time.sleep(delay)

    def _download_once(self, url, max_bytes, image):
        time.sleep(max(0.0, self.last_request + self.delay - time.monotonic()))
        self.last_request = time.monotonic()
        with self.s.get(url, allow_redirects=False, stream=True, timeout=(5, 10)) as response:
            if response.status_code != 200:
                raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
            mime = response.headers.get("Content-Type", "").partition(";")[0].strip().lower()
            if image and mime not in IMAGE_TYPES:
                raise ValueError("Unsupported image")
            data = bytearray()
            for chunk in response.iter_content(65536):
                if time.monotonic() - self.last_request >= REQUEST_DEADLINE_SECONDS:
                    raise requests.Timeout("Response deadline exceeded")
                if len(data) + len(chunk) > max_bytes:
                    raise ValueError("Response is too large")
                data.extend(chunk)
            return bytes(data), mime

    def _get(self, url, **_):
        link = urlsplit(url)
        if link.netloc not in BLOG_HOSTS:
            raise ValueError("Unsupported blog host")
        max_mib = 8 if link.path == "/PostView.naver" else 3
        return PageResponse(self.download(url, max_mib * 1024**2)[0])

    def image(self, url):
        link = urlsplit(url)
        if link.scheme != "https" or link.netloc.lower() not in IMAGE_HOSTS:
            raise ValueError("Unsupported image host")
        return self.download(url, 5 * 1024 * 1024, image=True)


def zip_blog(blog_id, start, end, destination, progress):
    client = BackupClient(blog_id)
    try:
        posts = [post for post in client._list_posts_mobile(verify=True, max_pages=None) if post["public"]]
        if start or end:
            selected = []
            for post in posts:
                if not post["published_at"]:
                    continue
                published = date.fromisoformat(post["published_at"][:10])
                if (not start or published >= start) and (not end or published <= end):
                    selected.append(post)
            posts = selected
        if not posts:
            raise BackupError("이 기간에 백업할 공개 글을 찾지 못했습니다.")
        return write_backup(client, blog_id, posts, destination, progress)
    finally:
        client.s.close()


def has_archive_space(destination, required_bytes):
    return shutil.disk_usage(destination.parent).free - required_bytes >= MIN_DISK_FREE_BYTES


def write_backup(client, blog_id, posts, destination, progress):
    skipped_posts, skipped_images = [], 0
    rows = []
    if not has_archive_space(destination, 0):
        raise BackupError(DISK_SPACE_ERROR)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, allowZip64=True) as archive:
        progress(0, len(posts))
        for index, post in enumerate(posts, start=1):
            log_no = post["log_no"]
            source = f"https://blog.naver.com/{blog_id}/{log_no}"
            try:
                main = extract_main(client.fetch_post_html(log_no), log_no)
                if main is None:
                    raise ValueError("Missing post")
                main_html = str(main)
                images = parse_post_content(main)["images"]
            except (requests.RequestException, ValueError):
                skipped_posts.append(source)
                progress(index, len(posts))
                continue

            image_files, saved = [], {}
            for url in images:
                if url not in saved:
                    saved[url] = None
                    if has_archive_space(destination, TEXT_DISK_HEADROOM_BYTES):
                        try:
                            data, mime = client.image(url)
                            if has_archive_space(destination, TEXT_DISK_HEADROOM_BYTES + len(data)):
                                name = image_filename(url, IMAGE_TYPES[mime])
                                archive.writestr(f"images/{log_no}/{name}", data, compress_type=ZIP_STORED)
                                saved[url] = name
                        except (requests.RequestException, BackupError, ValueError):
                            pass
                name = saved[url]
                skipped_images += name is None
                image_files.append(name)

            title = post["title"] or "제목 없음"
            published = post["published_at"][:10] or "날짜 없음"
            filename = f"{published}-{log_no}-{sanitize_filename(title, maxlen=56)}.md"
            _, markdown = build_outputs(main_html, log_no, image_files, source)
            document = f"# {title}\n\n> 발행일 {published}\n> 원본 {source}\n\n{markdown}\n".encode()
            if not has_archive_space(destination, len(document)):
                raise BackupError(DISK_SPACE_ERROR)
            archive.writestr(filename, document)
            rows.append((title, filename))
            progress(index, len(posts))

        if not rows:
            raise BackupError("글 본문을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.")
        readme = [
            f"# {blog_id} 블로그 백업", "",
            f"공개 글 {len(rows)}개 · 가져오지 못한 글 {len(skipped_posts)}개 · 생략된 이미지 {skipped_images}개",
            "동영상과 첨부파일은 원본 글에서 확인할 수 있습니다.", "",
            *[f"- {title} ({filename})" for title, filename in rows],
        ]
        if skipped_posts:
            readme += ["", "## 가져오지 못한 글", *skipped_posts]
        summary = ("\n".join(readme) + "\n").encode()
        if not has_archive_space(destination, len(summary)):
            raise BackupError(DISK_SPACE_ERROR)
        archive.writestr("README.md", summary)
    return {"posts": len(rows), "skipped_posts": len(skipped_posts), "skipped_images": skipped_images}


@dataclass
class Job:
    blog_id: str
    client: str
    state: str = "queued"
    done: int = 0
    total: int = 0
    error: str = ""
    result: Optional[dict] = None
    directory: Optional[tempfile.TemporaryDirectory] = None


def create_app(exporter=zip_blog):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 4096
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="zip")
    jobs = {}
    recent_clients = {}
    lock = threading.Lock()

    def expire(token):
        with lock:
            job = jobs.pop(token, None)
        if job and job.directory:
            job.directory.cleanup()

    def run_job(token, job, start, end):
        def progress(done, total):
            with lock:
                job.done, job.total = done, total

        with lock:
            job.state = "running"
        try:
            directory = tempfile.TemporaryDirectory(prefix="zip-", dir=os.environ.get("CACHE_DIRECTORY"))
            with lock:
                job.directory = directory
            result = exporter(job.blog_id, start, end, Path(directory.name) / "backup.zip", progress)
            with lock:
                job.result, job.state = result, "ready"
        except Exception as error:
            if not isinstance(error, BackupError):
                app.logger.exception("Could not build a public blog backup")
            message = "네이버에서 데이터를 가져오지 못했습니다. 주소를 확인하고 다시 시도해 주세요."
            if isinstance(error, BackupError):
                message = str(error)
            elif isinstance(error, OSError) and error.errno == errno.ENOSPC:
                message = DISK_SPACE_ERROR
            with lock:
                job.error = message
                job.state = "failed"
                directory, job.directory = job.directory, None
            if directory:
                directory.cleanup()
        finally:
            if job.state == "failed":
                expire_delay = 5 * 60
            else:
                expire_delay = JOB_TTL
            timer = threading.Timer(expire_delay, expire, args=(token,))
            timer.daemon = True
            timer.start()

    @app.after_request
    def prevent_cache(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/")
    def index():
        return render_template("public_backup.html")

    @app.post("/api/jobs")
    def submit():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="요청 형식을 확인해 주세요."), 400
        try:
            blog_id = blog_id_from_url(data.get("url"))
            start, end = parse_date_range(data)
        except BackupError as error:
            return jsonify(error=str(error)), 400

        client = request.headers.get("X-Backup-Client") or request.remote_addr or ""
        now = time.monotonic()
        with lock:
            expired = [key for key, last in recent_clients.items() if now - last >= CLIENT_COOLDOWN]
            for key in expired:
                del recent_clients[key]
            pending = [job for job in jobs.values() if job.state in {"queued", "running"}]
            if client in recent_clients or any(job.client == client for job in pending):
                return jsonify(error="이전 요청을 마친 뒤 다시 시도해 주세요."), 429
            if len(jobs) >= MAX_JOBS or len(pending) >= MAX_PENDING:
                return jsonify(error="백업 요청이 많습니다. 잠시 후 다시 시도해 주세요."), 503
            token = secrets.token_urlsafe(24)
            job = jobs[token] = Job(blog_id, client)
            recent_clients[client] = now
        executor.submit(run_job, token, job, start, end)
        return jsonify(token=token), 202

    @app.get("/api/jobs/<token>")
    def status(token):
        with lock:
            job = jobs.get(token)
            if job is None:
                return jsonify(error="백업 링크가 만료됐습니다."), 404
            return jsonify(state=job.state, done=job.done, total=job.total, error=job.error, result=job.result)

    @app.get("/api/jobs/<token>/download")
    def download(token):
        with lock:
            job = jobs.get(token)
            if job is None or job.state != "ready":
                return jsonify(error="다운로드할 백업이 없습니다."), 404
            return send_file(
                Path(job.directory.name) / "backup.zip", as_attachment=True,
                download_name=f"{job.blog_id}-blog-backup.zip", mimetype="application/zip",
            )

    return app


app = create_app()
