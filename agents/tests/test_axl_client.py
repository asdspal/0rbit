import base64
import pytest
import httpx
from agents.plugins.orbit.axl_client import AXLClient

class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
    def json(self):
        return self._json
    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise httpx.HTTPStatusError("Error", request=None, response=None)

class DummyClient:
    def __init__(self):
        self.posts = []
        self.gets = []
        self.closed = False
    def post(self, url, json):
        self.posts.append((url, json))
        # Echo back the json for test
        return DummyResponse({"sent": json})
    def get(self, url):
        self.gets.append(url)
        if url == "/recv":
            return DummyResponse([{"msg": "hello"}])
        elif url == "/topology":
            return DummyResponse({"peers": ["peer1", "peer2"]})
        return DummyResponse(None, status_code=404)
    def close(self):
        self.closed = True

@pytest.fixture
def axl_client(monkeypatch):
    client = AXLClient()
    dummy = DummyClient()
    monkeypatch.setattr(client, "client", dummy)
    return client

def test_send_with_bytes(axl_client):
    data = b"hello bytes"
    dst = "peer123"
    result = axl_client.send(dst, data)
    # Check base64 encoding
    encoded = base64.b64encode(data).decode('ascii')
    assert result["sent"]["data"] == encoded
    assert result["sent"]["dst_peer_id"] == dst

def test_send_with_str(axl_client):
    data = "hello string"
    dst = "peer456"
    result = axl_client.send(dst, data)
    assert result["sent"]["data"] == data
    assert result["sent"]["dst_peer_id"] == dst

def test_recv(axl_client):
    messages = axl_client.recv()
    assert isinstance(messages, list)
    assert messages[0]["msg"] == "hello"

def test_topology(axl_client):
    topo = axl_client.topology()
    assert "peers" in topo
    assert topo["peers"] == ["peer1", "peer2"]

def test_close(axl_client):
    client = axl_client.client
    axl_client.close()
    assert client.closed

def test_context_manager(monkeypatch):
    client = AXLClient()
    dummy = DummyClient()
    monkeypatch.setattr(client, "client", dummy)
    with client as c:
        assert c is client
    assert dummy.closed
