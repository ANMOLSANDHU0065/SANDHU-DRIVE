
from io import BytesIO

import pytest

import app as app_module
from file_service import FileService


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_service = FileService(tmp_path / "test_storage")
    monkeypatch.setattr(app_module, "service", test_service)

    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        MAX_CONTENT_LENGTH=500 * 1024 * 1024,
    )

    with app_module.app.test_client() as test_client:
        yield test_client


def test_home_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Sandhu Drive" in response.data


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["app"] == "Sandhu Drive"


def test_stats_endpoint(client):
    response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.json["count"] == 0
    assert response.json["size_mb"] == 0


def test_upload_file(client):
    response = client.post(
        "/upload",
        data={
            "files": (
                BytesIO(b"hello from test"),
                "hello.txt",
            )
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"uploaded successfully" in response.data
    assert app_module.service.resolve_name("hello.txt") == "hello.txt"


def test_upload_without_file_shows_error(client):
    response = client.post(
        "/upload",
        data={},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"select at least one file" in response.data


def test_search_finds_matching_filename(client):
    app_module.service.save_upload(
        __import__("werkzeug").datastructures.FileStorage(
            stream=BytesIO(b"alpha"),
            filename="alpha.txt",
        )
    )
    app_module.service.save_upload(
        __import__("werkzeug").datastructures.FileStorage(
            stream=BytesIO(b"beta"),
            filename="beta.txt",
        )
    )

    response = client.get("/?q=alpha")

    assert response.status_code == 200
    assert b"alpha.txt" in response.data
    assert b"beta.txt" not in response.data


def test_category_filter(client):
    from werkzeug.datastructures import FileStorage

    app_module.service.save_upload(
        FileStorage(stream=BytesIO(b"picture"), filename="photo.png")
    )
    app_module.service.save_upload(
        FileStorage(stream=BytesIO(b"document"), filename="notes.txt")
    )

    response = client.get("/?type=image")

    assert response.status_code == 200
    assert b"photo.png" in response.data
    assert b"notes.txt" not in response.data


def test_download_file(client):
    from werkzeug.datastructures import FileStorage

    app_module.service.save_upload(
        FileStorage(stream=BytesIO(b"download me"), filename="download.txt")
    )

    response = client.get("/download/download.txt")

    assert response.status_code == 200
    assert response.data == b"download me"


def test_missing_download_returns_404(client):
    response = client.get("/download/missing.txt")

    assert response.status_code == 404


def test_rename_route(client):
    from werkzeug.datastructures import FileStorage

    app_module.service.save_upload(
        FileStorage(stream=BytesIO(b"rename me"), filename="before.txt")
    )

    response = client.post(
        "/rename",
        data={"old_name": "before.txt", "new_name": "after.txt"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert app_module.service.resolve_name("after.txt") == "after.txt"


def test_delete_route(client):
    from werkzeug.datastructures import FileStorage

    app_module.service.save_upload(
        FileStorage(stream=BytesIO(b"delete me"), filename="remove.txt")
    )

    response = client.post(
        "/delete",
        data={"name": "remove.txt"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert app_module.service.resolve_name("remove.txt") is None


def test_clear_route(client):
    from werkzeug.datastructures import FileStorage

    app_module.service.save_upload(
        FileStorage(stream=BytesIO(b"file"), filename="clear-me.txt")
    )

    response = client.post("/clear", follow_redirects=True)

    assert response.status_code == 200
    assert app_module.service.stats()["count"] == 0
