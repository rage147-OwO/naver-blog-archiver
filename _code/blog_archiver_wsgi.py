"""Gunicorn entry point for the Oracle installation."""

import os
import shlex
from pathlib import Path

import blog_archiver

state = Path(os.environ["STATE_DIRECTORY"])
blog_archiver.CONFIG_PATH = state / "config.json"
blog_archiver.DEFAULT_CONFIG.update(archive_dir=str(state / "archive"), web_port=8767)

credentials = os.environ.get("CREDENTIALS_DIRECTORY")
if credentials:
    key = Path(credentials) / "github-pages.key"
    known_hosts = "/etc/naver-blog-archiver/github_known_hosts"
    os.environ["GIT_SSH_COMMAND"] = (
        f"ssh -F /dev/null -i {shlex.quote(str(key))} -o IdentitiesOnly=yes -o BatchMode=yes "
        f"-o StrictHostKeyChecking=yes -o UserKnownHostsFile={known_hosts} "
        "-o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3"
    )
    os.environ["GIT_TERMINAL_PROMPT"] = "0"

app = blog_archiver.create_app(blog_archiver.load_config())
