"""Auth env-var honoring for the Apache Jena Fuseki client (get_client)."""

from jena_mcp.auth import get_client


def test_get_client_honors_apache_jena_url(monkeypatch):
    """The deployed convention APACHE_JENA_URL/APACHE_JENA_TOKEN must win."""
    for var in ("JENA_FUSEKI_URL", "JENA_URL", "JENA_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("APACHE_JENA_URL", "http://jena.arpa")
    monkeypatch.setenv("APACHE_JENA_TOKEN", "tok")

    client = get_client()

    assert client.base_url.rstrip("/") == "http://jena.arpa"
    assert client.token == "tok"


def test_get_client_falls_back_to_localhost(monkeypatch):
    """With no URL var set, the client defaults to localhost:3030."""
    for var in ("APACHE_JENA_URL", "JENA_FUSEKI_URL", "JENA_URL"):
        monkeypatch.delenv(var, raising=False)

    client = get_client()

    assert client.base_url.rstrip("/") == "http://localhost:3030"
