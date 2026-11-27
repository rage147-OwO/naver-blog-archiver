import sys
import tempfile
import time
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

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
