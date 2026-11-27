import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_code"))

import blog_archiver as archiver


class AdminAccessTest(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.origin = "https://archive.example.test"
        self.local_origin = "http://127.0.0.1:8767"
        self.cfg = {**archiver.DEFAULT_CONFIG, "archive_dir": scratch.name}
        self.client = archiver.create_app(self.cfg, admin_origin=self.origin).test_client()

    def stop_sync(self, url, origin=None):
        headers = {"Origin": origin} if origin is not None else {}
        return self.client.post("/api/sync/stop", base_url=url, headers=headers)

    def test_same_origin_writes_are_accepted(self):
        for url in (self.origin, self.local_origin):
            with self.subTest(url=url):
                self.assertEqual(self.stop_sync(url, url).status_code, 200)

    def test_writes_require_a_matching_origin(self):
        for origin in (None, "null", "https://elsewhere.example.test", self.local_origin):
            with self.subTest(origin=origin):
                self.assertEqual(self.stop_sync(self.origin, origin).status_code, 403)

        self.assertEqual(self.stop_sync(self.local_origin, self.origin).status_code, 403)
        self.assertEqual(self.stop_sync("https://elsewhere.example.test", self.origin).status_code, 403)

    def test_admin_responses_are_not_cacheable(self):
        response = self.client.get("/api/sync/status", base_url=self.origin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_local_mode_works_without_admin_configuration(self):
        local_client = archiver.create_app(self.cfg).test_client()
        self.assertEqual(local_client.post("/api/sync/stop").status_code, 200)
