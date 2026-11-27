import sys
import tempfile
import time
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_code"))

import blog_archiver
import public_backup


class PublicBackupTest(unittest.TestCase):
    def test_blog_url_parsing(self):
        for url in (
            "blog.naver.com/example-blog",
            "https://m.blog.naver.com/example-blog/123",
            "https://blog.naver.com/PostList.naver?blogId=example-blog",
        ):
            self.assertEqual(public_backup.blog_id_from_url(url), "example-blog")
        for url in (
            "https://blog.naver.com.example.test/owner", "https://blog.naver.com@127.0.0.1/owner",
            "https://blog.naver.com:8080/owner", "https://m.blog.naver.com/%2fetc", "https://other.test/blog",
        ):
            with self.subTest(url=url), self.assertRaises(public_backup.BackupError):
                public_backup.blog_id_from_url(url)

    def test_zip_contains_only_public_posts_in_range(self):
        rows = [
            {"log_no": 101, "title": "공개", "published_at": "2026-10-01", "public": True},
            {"log_no": 102, "title": "비공개", "published_at": "2026-10-01", "public": False},
            {"log_no": 103, "title": "이전 글", "published_at": "2025-10-01", "public": True},
        ]
        progress = []
        html = '<div class="se-main-container"><p>본문</p><img class="se-image-resource" src="https://postfiles.pstatic.net/y.png"></div>'
        with tempfile.TemporaryDirectory() as directory, patch.object(public_backup, "BackupClient") as client_type:
            client = client_type.return_value
            client._list_posts_mobile.return_value = rows
            client.fetch_post_html.return_value = html
            client.image.return_value = (b"image file", "image/png")
            filename = Path(directory) / "test.zip"
            result = public_backup.zip_blog(
                "example-blog", date(2026, 10, 1), date(2026, 10, 1), filename,
                lambda *args: progress.append(args),
            )
            self.assertEqual(result, {"posts": 1, "skipped_posts": 0, "skipped_images": 0})
            self.assertEqual(progress, [(0, 1), (1, 1)])
            client.fetch_post_html.assert_called_once_with(101)
            with ZipFile(filename) as archive:
                markdown = archive.read("2026-10-01-101-공개.md").decode()
                self.assertIn("본문", markdown)
                images = [entry for entry in archive.namelist() if entry.startswith("images/")]
                self.assertEqual(len(images), 1)
                self.assertIn(images[0], markdown)

    def test_full_backup_keeps_more_than_200_posts_in_one_zip(self):
        rows = [
            {"log_no": log_no, "title": "공개", "published_at": "2026-10-01", "public": True}
            for log_no in range(1, 258)
        ]
        rows.append({"log_no": 258, "title": "비공개", "published_at": "2026-10-01", "public": False})
        html = '<div class="se-main-container"><p>본문</p></div>'
        app = public_backup.create_app()
        with patch.object(public_backup, "BackupClient") as adapter, app.test_client() as client:
            naver = adapter.return_value
            naver._list_posts_mobile.return_value = rows
            naver.fetch_post_html.return_value = html
            submitted = client.post("/api/jobs", json={"url": "https://blog.naver.com/example-blog"})
            self.assertEqual(submitted.status_code, 202)
            status_url = "/api/jobs/" + submitted.json["token"]
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                state = client.get(status_url).json
                if state["state"] in {"ready", "failed"}:
                    break
                time.sleep(.02)
            self.assertEqual(state["state"], "ready", state)
            self.assertEqual(state["result"], {"posts": 257, "skipped_posts": 0, "skipped_images": 0})
            naver._list_posts_mobile.assert_called_once_with(verify=True, max_pages=None)
            with client.get(status_url + "/download") as response:
                self.assertEqual(response.status_code, 200)
                with ZipFile(BytesIO(response.data)) as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertEqual(len(archive.namelist()), 258)
                    self.assertIn("2026-10-01-257-공개.md", archive.namelist())
                    self.assertNotIn("2026-10-01-258-비공개.md", archive.namelist())

    def test_full_listing_continues_past_page_300(self):
        client = public_backup.BackupClient("example-blog")
        self.addCleanup(client.s.close)
        batches = [
            public_backup.PageResponse(
                ('{"isSuccess":true,"result":{"items":[{"logNo":%d,"allOpenPost":true}]}}' % page).encode()
            )
            for page in range(1, 302)
        ]
        batches.append(public_backup.PageResponse(b'{"isSuccess":true,"result":{"items":[]}}'))
        with patch.object(client, "_get", side_effect=batches) as get, patch.object(blog_archiver.time, "sleep"):
            posts = client._list_posts_mobile(verify=True, max_pages=None)
        self.assertEqual(len(posts), 301)
        self.assertTrue(get.call_args.args[0].endswith("&page=302"))

    def test_full_listing_rejects_repeated_pages(self):
        client = public_backup.BackupClient("example-blog")
        self.addCleanup(client.s.close)
        batch = public_backup.PageResponse(b'{"isSuccess":true,"result":{"items":[{"logNo":1,"allOpenPost":true}]}}')
        with patch.object(client, "_get", return_value=batch) as get, patch.object(blog_archiver.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "반복"):
                client._list_posts_mobile(verify=True, max_pages=None)
        self.assertEqual(get.call_count, 2)

    def test_insufficient_image_space_preserves_post_text(self):
        post = {"log_no": 101, "title": "공개", "published_at": "2026-10-01", "public": True}
        html = '<div class="se-main-container"><p>본문</p><img class="se-image-resource" src="https://postfiles.pstatic.net/y.png"></div>'
        with tempfile.TemporaryDirectory() as directory, patch.object(public_backup, "BackupClient") as adapter:
            client = adapter.return_value
            client._list_posts_mobile.return_value = [post]
            client.fetch_post_html.return_value = html
            filename = Path(directory) / "text-first.zip"
            with patch.object(public_backup, "has_archive_space", side_effect=lambda _, size: size < 1024):
                result = public_backup.zip_blog("example-blog", None, None, filename, lambda *_: None)
            self.assertEqual(result, {"posts": 1, "skipped_posts": 0, "skipped_images": 1})
            client.image.assert_not_called()
            with ZipFile(filename) as archive:
                self.assertIn("본문", archive.read("2026-10-01-101-공개.md").decode())

    def test_retry_preserves_upstream_backoff(self):
        client = public_backup.BackupClient("example-blog")
        self.addCleanup(client.s.close)
        response = requests.Response()
        response.status_code = 429
        response.headers["Retry-After"] = "7"
        result = (b"public content", "text/plain")
        with patch.object(client, "_download_once", side_effect=[requests.HTTPError(response=response), result]), \
             patch.object(public_backup.time, "sleep") as sleep:
            self.assertEqual(client.download("https://blog.naver.com/example-blog", 1024), result)
        sleep.assert_called_once_with(7)

    def test_job_download_and_rate_limit(self):
        def exporter(blog_id, start, end, filename, progress):
            progress(1, 1)
            with ZipFile(filename, "w") as archive:
                archive.writestr("README.md", blog_id)
            return {"posts": 1, "skipped_posts": 0, "skipped_images": 0}

        app = public_backup.create_app(exporter)
        with app.test_client() as client:
            self.assertIn("ZIP 만들기", client.get("/").get_data(as_text=True))
            job = client.post("/api/jobs", json={"url": "https://blog.naver.com/example-blog"})
            self.assertEqual(job.status_code, 202)
            self.assertEqual(client.post("/api/jobs", json={"url": "blog.naver.com/example-blog"}).status_code, 429)
            self.assertEqual(client.get("/api/jobs/unknown/download").status_code, 404)
            status_url = "/api/jobs/" + job.json["token"]
            for _ in range(100):
                if client.get(status_url).json["state"] == "ready":
                    break
                time.sleep(.01)
            response = client.get(status_url + "/download")
            self.addCleanup(response.close)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertIn("example-blog-blog-backup.zip", response.headers["Content-Disposition"])
            with ZipFile(BytesIO(response.data)) as archive:
                self.assertEqual(archive.read("README.md"), b"example-blog")

    def test_owner_view_uses_existing_sync(self):
        app = blog_archiver.create_app(dict(
            blog_archiver.DEFAULT_CONFIG, blog_id="example-blog",
            managed_pages_publish=True, publish_after_sync=True,
        ))
        with app.test_client() as client:
            body = client.get("/").get_data(as_text=True)
            self.assertIn("내 블로그 글 업데이트", body)
            self.assertIn("mode: 'full'", body)
            self.assertNotIn("<aside>", body)
            self.assertEqual(client.post("/api/sync/start").status_code, 400)
