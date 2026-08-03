def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Build Your PC API"}


def test_docs(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
