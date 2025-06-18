import pytest
from app import app, allowed_file, rooms, last_updates


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_allowed_file_valid_extensions():
    valid_files = ["slide.png", "photo.jpg", "doc.jpeg", "anim.gif", "report.pdf"]
    for filename in valid_files:
        assert allowed_file(filename)


def test_allowed_file_invalid_extensions():
    invalid_files = ["malware.exe", "note.txt", "image", "archive.zip"]
    for filename in invalid_files:
        assert not allowed_file(filename)


def test_check_updates_has_updates(client):
    test_room = "pytest_room"
    rooms.append(test_room)
    last_updates[test_room] = 100

    # client timestamp older than server timestamp -> updates available
    resp = client.get(f"/api/check_updates/{test_room}?timestamp=50000")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["hasUpdates"] is True

    # client timestamp equal to server timestamp -> no updates
    resp = client.get(f"/api/check_updates/{test_room}?timestamp=100000")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["hasUpdates"] is False

    rooms.remove(test_room)
    del last_updates[test_room]
