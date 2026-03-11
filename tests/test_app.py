"""
Integration & unit tests for the Personal Bookmark Manager.

AI-aided: Test cases were generated and reviewed with GitHub Copilot to ensure
complete coverage of all PRD-specified features.
"""

import os
import tempfile
import pytest

from app import create_app


@pytest.fixture
def app():
    """Create application with a fresh in-memory-style SQLite database per test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    flask_app = create_app({"TESTING": True, "DATABASE_PATH": db_path})
    yield flask_app
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Index page
# ---------------------------------------------------------------------------

class TestIndexPage:
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Bookmark" in resp.data


# ---------------------------------------------------------------------------
# Add bookmark (POST /api/bookmarks)
# ---------------------------------------------------------------------------

class TestAddBookmark:
    def test_add_with_title(self, client):
        resp = client.post(
            "/api/bookmarks",
            json={"url": "https://example.com", "title": "Example Site"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["url"] == "https://example.com"
        assert data["title"] == "Example Site"
        assert data["id"] is not None

    def test_add_without_title_falls_back_to_url(self, client):
        """When title is empty and fetch fails the URL is used as the title."""
        resp = client.post(
            "/api/bookmarks",
            json={"url": "https://does-not-exist.invalid"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "https://does-not-exist.invalid"

    def test_add_requires_url(self, client):
        resp = client.post("/api/bookmarks", json={"title": "No URL here"})
        assert resp.status_code == 400

    def test_add_rejects_non_http_scheme(self, client):
        """Only http/https URLs are accepted — prevents SSRF via file:// or ftp:// etc."""
        resp = client.post("/api/bookmarks", json={"url": "file:///etc/passwd", "title": "Bad"})
        assert resp.status_code == 400

    def test_add_with_tags(self, client):
        resp = client.post(
            "/api/bookmarks",
            json={"url": "https://python.org", "title": "Python", "tags": ["python", "programming"]},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert sorted(data["tags"]) == ["programming", "python"]

    def test_add_tags_as_string(self, client):
        """Tags can be sent as a comma-separated string."""
        resp = client.post(
            "/api/bookmarks",
            json={"url": "https://example.com", "title": "Ex", "tags": "foo, bar"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert sorted(data["tags"]) == ["bar", "foo"]

    def test_tags_are_normalized_to_lowercase(self, client):
        resp = client.post(
            "/api/bookmarks",
            json={"url": "https://example.com", "title": "Ex", "tags": ["Python", "DJANGO"]},
        )
        data = resp.get_json()
        assert sorted(data["tags"]) == ["django", "python"]


# ---------------------------------------------------------------------------
# List bookmarks (GET /api/bookmarks)
# ---------------------------------------------------------------------------

class TestListBookmarks:
    def _add(self, client, url, title, tags=None):
        payload = {"url": url, "title": title}
        if tags:
            payload["tags"] = tags
        return client.post("/api/bookmarks", json=payload)

    def test_empty_list(self, client):
        resp = client.get("/api/bookmarks")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_newest_first(self, client):
        self._add(client, "https://first.com", "First")
        self._add(client, "https://second.com", "Second")
        data = client.get("/api/bookmarks").get_json()
        assert data[0]["title"] == "Second"
        assert data[1]["title"] == "First"

    def test_list_contains_all_bookmarks(self, client):
        for i in range(5):
            self._add(client, f"https://example{i}.com", f"Site {i}")
        data = client.get("/api/bookmarks").get_json()
        assert len(data) == 5

    def test_search_by_title(self, client):
        self._add(client, "https://python.org", "Python")
        self._add(client, "https://django.org", "Django Framework")
        data = client.get("/api/bookmarks?q=python").get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Python"

    def test_search_by_url(self, client):
        self._add(client, "https://flask.palletsprojects.com", "Flask")
        self._add(client, "https://django.org", "Django")
        data = client.get("/api/bookmarks?q=flask").get_json()
        assert len(data) == 1
        assert "flask" in data[0]["url"]

    def test_filter_by_tag(self, client):
        self._add(client, "https://a.com", "A", tags=["python"])
        self._add(client, "https://b.com", "B", tags=["javascript"])
        self._add(client, "https://c.com", "C", tags=["python", "web"])
        data = client.get("/api/bookmarks?tag=python").get_json()
        assert len(data) == 2
        titles = {d["title"] for d in data}
        assert titles == {"A", "C"}

    def test_search_returns_empty_for_no_match(self, client):
        self._add(client, "https://example.com", "Example")
        data = client.get("/api/bookmarks?q=zzznomatch").get_json()
        assert data == []


# ---------------------------------------------------------------------------
# Delete bookmark (DELETE /api/bookmarks/<id>)
# ---------------------------------------------------------------------------

class TestDeleteBookmark:
    def test_delete_existing(self, client):
        add = client.post(
            "/api/bookmarks",
            json={"url": "https://example.com", "title": "To Delete"},
        ).get_json()
        resp = client.delete(f"/api/bookmarks/{add['id']}")
        assert resp.status_code == 200
        data = client.get("/api/bookmarks").get_json()
        assert data == []

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/bookmarks/9999")
        assert resp.status_code == 404

    def test_delete_removes_only_target(self, client):
        a = client.post("/api/bookmarks", json={"url": "https://a.com", "title": "A"}).get_json()
        client.post("/api/bookmarks", json={"url": "https://b.com", "title": "B"})
        client.delete(f"/api/bookmarks/{a['id']}")
        data = client.get("/api/bookmarks").get_json()
        assert len(data) == 1
        assert data[0]["title"] == "B"


# ---------------------------------------------------------------------------
# Tags (GET /api/tags)
# ---------------------------------------------------------------------------

class TestTags:
    def test_empty_tags(self, client):
        resp = client.get("/api/tags")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_tags_listed_after_add(self, client):
        client.post(
            "/api/bookmarks",
            json={"url": "https://a.com", "title": "A", "tags": ["python", "flask"]},
        )
        tags = client.get("/api/tags").get_json()
        names = {t["name"] for t in tags}
        assert names == {"python", "flask"}

    def test_tag_count_increments(self, client):
        client.post("/api/bookmarks", json={"url": "https://a.com", "title": "A", "tags": ["python"]})
        client.post("/api/bookmarks", json={"url": "https://b.com", "title": "B", "tags": ["python"]})
        tags = {t["name"]: t["count"] for t in client.get("/api/tags").get_json()}
        assert tags["python"] == 2

    def test_tags_shared_across_bookmarks(self, client):
        """Same tag name should not be duplicated in the tags table."""
        client.post("/api/bookmarks", json={"url": "https://a.com", "title": "A", "tags": ["shared"]})
        client.post("/api/bookmarks", json={"url": "https://b.com", "title": "B", "tags": ["shared"]})
        tags = client.get("/api/tags").get_json()
        assert len(tags) == 1
        assert tags[0]["name"] == "shared"


# ---------------------------------------------------------------------------
# Persistence: data survives app restart (new create_app with same DB)
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_data_persists_across_app_instances(self):
        _, db_path = tempfile.mkstemp(suffix=".db")
        try:
            app1 = create_app({"TESTING": True, "DATABASE_PATH": db_path})
            with app1.test_client() as c1:
                c1.post("/api/bookmarks", json={"url": "https://persist.com", "title": "Persist"})

            app2 = create_app({"TESTING": True, "DATABASE_PATH": db_path})
            with app2.test_client() as c2:
                data = c2.get("/api/bookmarks").get_json()
            assert len(data) == 1
            assert data[0]["title"] == "Persist"
        finally:
            os.unlink(db_path)
