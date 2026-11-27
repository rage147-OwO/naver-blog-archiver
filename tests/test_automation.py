import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_code"))

import blog_archiver as archiver
from pages_publish import PagesRepository, publish_public


def git(path, *args):
    command = ["git", "-C", str(path), *args]
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise subprocess.CalledProcessError(
            result.returncode, command, result.stdout, result.stderr
        ) from RuntimeError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


class PagesPublicationTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        root = Path(self.scratch.name)
        self.remote = root / "remote.git"
        self.checkout = root / "original"
        self.remote.mkdir()
        self.checkout.mkdir()
        git(self.remote, "init", "--bare", "--initial-branch=master")
        git(self.checkout, "init", "--initial-branch=master")
        git(self.checkout, "config", "user.name", "Fixture")
        git(self.checkout, "config", "user.email", "fixture@example.test")
        identity = {
            "GIT_AUTHOR_NAME": "Fixture", "GIT_COMMITTER_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.test", "GIT_COMMITTER_EMAIL": "fixture@example.test",
        }
        for name, value in identity.items():
            if name in os.environ:
                self.addCleanup(os.environ.__setitem__, name, os.environ[name])
            else:
                self.addCleanup(os.environ.pop, name, None)
            os.environ[name] = value

        self.cfg = {
            **archiver.DEFAULT_CONFIG, "blog_id": "example", "pages_blog_id": "example",
            "archive_dir": str(root / "archive"), "jekyll_repo_dir": str(root / "cache.git"),
            "pages_git_url": self.remote.as_uri(), "managed_pages_publish": True,
            "jekyll_image_base_url": "https://raw.githubusercontent.com/acct/blog/master/_images",
        }
        self.old = {}
        for log_no, title in [(101, "Old title"), (102, "Fetch failure"), (103, "Removed")]:
            filename = f"_posts/NaverBackup/2025-01-01-{title}.md"
            self.old[log_no] = filename
            self.write(filename, f'---\ntitle: "{title}"\ndate: 2025-01-01\ncategories:\n'
                       f' - Saved\nnaver_url: https://blog.naver.com/example/{log_no}\n---\n\n{title}\n')
        self.write("_images/103/picture.png", b"previous image")
        self.write("_posts/hand-written.md", "Unrelated")
        git(self.checkout, "add", ".")
        git(self.checkout, "commit", "-m", "Initial posts")
        git(self.checkout, "push", self.remote.as_uri(), "master")

    def write(self, relative, content):
        file = self.checkout / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            file.write_bytes(content)
        else:
            file.write_text(content, encoding="utf-8")

    def add_post(self, log_no, title, markdown):
        with closing(archiver.open_db(self.cfg)) as database, database:
            database.execute("""INSERT INTO posts(log_no,blog_id,title,category,published_at,url,html_raw,markdown)
                VALUES(?, 'example', ?, 'Saved', '2025-01-01', ?, '<p>Body</p>', ?)""",
                             (log_no, title, f"https://blog.naver.com/example/{log_no}", markdown))

    def show(self, path):
        return git(self.remote, "show", f"master:{path}").decode()

    def publish(self):
        return publish_public(self.cfg, {101, 102, 104}, {102}, log=lambda _: None)

    def test_body_change_failed_post_new_post_removal_and_noop(self):
        self.add_post(101, "Updated title", "Updated below preview")
        self.add_post(104, "New post", "Brand new")
        first = self.publish()
        self.assertTrue(first["pushed"])
        self.assertEqual(first["removed"], 1)
        self.assertIn("Updated below preview", self.show(self.old[101]))
        self.assertIn("Fetch failure", self.show(self.old[102]))
        self.assertIn("Brand new", self.show("_posts/NaverBackup/2025-01-01-New post.md"))
        self.assertEqual(self.show("_posts/hand-written.md"), "Unrelated")
        with self.assertRaises(subprocess.CalledProcessError):
            self.show(self.old[103])
        with self.assertRaises(subprocess.CalledProcessError):
            self.show("_images/103/picture.png")
        with closing(archiver.open_db(self.cfg)) as database, database:
            archived = database.execute("SELECT status, markdown FROM posts WHERE log_no=103").fetchone()
            self.assertEqual(archived["status"], "missing")
            self.assertIn("Removed", archived["markdown"])
        self.assertEqual((archiver.blog_paths(self.cfg)["images"] / "103/picture.png").read_bytes(),
                         b"previous image")

        first_tip = git(self.remote, "rev-parse", "master")
        second = self.publish()
        self.assertFalse(second["pushed"])
        self.assertEqual(second["changed"], 0)
        self.assertEqual(git(self.remote, "rev-parse", "master"), first_tip)

    def test_failed_push_is_retried_on_next_run(self):
        self.add_post(101, "Updated title", "Retry this change")
        previous_tip = git(self.remote, "rev-parse", "master")
        original = PagesRepository.git

        def fail_push(repository, *args, **kwargs):
            if args[0] == "push":
                raise RuntimeError("injected push failure")
            return original(repository, *args, **kwargs)

        with patch.object(PagesRepository, "git", fail_push):
            with self.assertRaisesRegex(RuntimeError, "injected push failure"):
                self.publish()
        self.assertEqual(git(self.remote, "rev-parse", "master"), previous_tip)
        self.assertTrue(self.publish()["pushed"])
        self.assertIn("Retry this change", self.show(self.old[101]))


class SyncTest(unittest.TestCase):
    def test_mismatched_naver_lists_fail_before_publication(self):
        client = archiver.NaverClient("example")
        with patch.object(client, "_list_posts_mobile", return_value=[{"log_no": 101, "public": True}]), \
             patch.object(client, "_list_posts_desktop", return_value=[{"log_no": 102}]):
            with self.assertRaisesRegex(RuntimeError, "불일치"):
                client.list_public_posts()

    def test_two_web_syncs_cannot_run_at_the_same_time(self):
        done = threading.Event()
        started = threading.Event()

        def sync(*_):
            started.set()
            done.wait(5)
            return {"added": 0}

        app = archiver.create_app(archiver.DEFAULT_CONFIG.copy())
        with app.test_client() as client, patch.object(archiver, "_run_sync", sync):
            try:
                accepted = client.post("/api/sync/start", json={"mode": "full"})
                self.assertEqual(accepted.status_code, 200)
                self.assertTrue(started.wait(1))
                self.assertEqual(client.post("/api/sync/start", json={"mode": "full"}).status_code, 409)
            finally:
                done.set()
            for _ in range(100):
                state = client.get("/api/sync/status").json
                if not state["running"]:
                    break
                time.sleep(0.01)
            self.assertFalse(state["running"])
            self.assertEqual(state["run_id"], accepted.json["run_id"])
            self.assertEqual(state["result"], {"added": 0})


if __name__ == "__main__":
    unittest.main()
