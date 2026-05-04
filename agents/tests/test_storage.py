from __future__ import annotations

import os
from pathlib import Path

import pytest

from agents.plugins.orbit.storage import DEFAULT_ENDPOINT, StorageClient, StorageError


class _FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _make_client(tmp_path: Path) -> StorageClient:
    script = tmp_path / "0g_upload.js"
    script.write_text("console.log('noop');")
    return StorageClient(script_path=script, node_binary="node", endpoint=DEFAULT_ENDPOINT)


def test_upload_file_success(monkeypatch, tmp_path):
    client = _make_client(tmp_path)
    upload_file = tmp_path / "payload.bin"
    upload_file.write_bytes(b"hello")

    captured = {}

    def fake_run(cmd, capture_output, text, env, timeout, check):
        captured["cmd"] = cmd
        captured["env"] = env
        return _FakeCompletedProcess(stdout="merkle-root\n")

    monkeypatch.setattr("agents.plugins.orbit.storage.subprocess.run", fake_run)

    root = client.upload_file(str(upload_file))

    assert root == "merkle-root"
    assert captured["cmd"][0] == "node"
    assert captured["cmd"][1].endswith("0g_upload.js")
    assert captured["cmd"][2] == str(upload_file.resolve())
    assert captured["env"]["OG_STORAGE_URL"] == DEFAULT_ENDPOINT


def test_upload_bytes_writes_temp_file(monkeypatch, tmp_path):
    client = _make_client(tmp_path)

    written = {"path": None, "contents": None}

    def fake_run(cmd, capture_output, text, env, timeout, check):
        temp_path = cmd[2]
        written["path"] = temp_path
        with open(temp_path, "rb") as fh:
            written["contents"] = fh.read()
        return _FakeCompletedProcess(stdout="abc123\n")

    monkeypatch.setattr("agents.plugins.orbit.storage.subprocess.run", fake_run)

    root = client.upload_bytes(b"payload")

    assert root == "abc123"
    assert written["contents"] == b"payload"
    assert not os.path.exists(written["path"])


def test_upload_failure_raises_storage_error(monkeypatch, tmp_path):
    client = _make_client(tmp_path)
    upload_file = tmp_path / "payload.bin"
    upload_file.write_bytes(b"boom")

    def fake_run(*_, **__):
        return _FakeCompletedProcess(returncode=1, stderr="bad things")

    monkeypatch.setattr("agents.plugins.orbit.storage.subprocess.run", fake_run)

    with pytest.raises(StorageError) as exc:
        client.upload_file(str(upload_file))

    assert "bad things" in str(exc.value)


def test_missing_file_raises_storage_error(tmp_path):
    client = _make_client(tmp_path)

    with pytest.raises(StorageError):
        client.upload_file(str(tmp_path / "missing.bin"))
