
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from file_service import FileService


@pytest.fixture
def service(tmp_path):
    return FileService(tmp_path / "storage")


def make_upload(name, content=b"test file content"):
    return FileStorage(
        stream=BytesIO(content),
        filename=name,
        content_type="application/octet-stream",
    )


def test_storage_directory_is_created(tmp_path):
    storage_path = tmp_path / "new_storage"
    service = FileService(storage_path)

    assert storage_path.exists()
    assert service.stats()["count"] == 0


def test_upload_and_list_file(service):
    saved_name = service.save_upload(make_upload("report.txt"))

    assert saved_name == "report.txt"

    files = service.list_files()

    assert len(files) == 1
    assert files[0]["name"] == "report.txt"
    assert files[0]["category"] == "Document"
    assert files[0]["size"] > 0


def test_duplicate_filename_is_preserved(service):
    first = service.save_upload(make_upload("report.txt", b"first"))
    second = service.save_upload(make_upload("report.txt", b"second"))

    assert first == "report.txt"
    assert second == "report (1).txt"
    assert len(service.list_files()) == 2


def test_stats_count_and_storage_size(service):
    service.save_upload(make_upload("one.txt", b"12345"))
    service.save_upload(make_upload("two.png", b"1234567"))

    stats = service.stats()

    assert stats["count"] == 2
    assert stats["bytes"] == 12
    assert stats["size_mb"] >= 0
    assert stats["documents"] == 1
    assert stats["images"] == 1


def test_rename_file(service):
    service.save_upload(make_upload("old.txt"))

    service.rename("old.txt", "new.txt")

    assert service.resolve_name("old.txt") is None
    assert service.resolve_name("new.txt") == "new.txt"


def test_rename_rejects_existing_destination(service):
    service.save_upload(make_upload("one.txt"))
    service.save_upload(make_upload("two.txt"))

    with pytest.raises(ValueError, match="already exists"):
        service.rename("one.txt", "two.txt")


def test_delete_file(service):
    service.save_upload(make_upload("delete.txt"))

    service.delete("delete.txt")

    assert service.resolve_name("delete.txt") is None
    assert service.stats()["count"] == 0


def test_executable_upload_is_rejected(service):
    with pytest.raises(ValueError, match="not allowed"):
        service.save_upload(make_upload("danger.exe"))


def test_path_traversal_is_rejected(service):
    service.save_upload(make_upload("safe.txt"))

    assert service.resolve_name("../safe.txt") is None
    assert service.resolve_name("..\\safe.txt") is None


def test_clear_removes_workspace_files(service):
    service.save_upload(make_upload("one.txt"))
    service.save_upload(make_upload("two.pdf"))

    deleted = service.clear()

    assert deleted == 2
    assert service.stats()["count"] == 0


def test_empty_filename_is_rejected(service):
    with pytest.raises(ValueError, match="valid filename"):
        service.save_upload(make_upload(""))

