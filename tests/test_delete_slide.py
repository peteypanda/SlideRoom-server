import time
import app


def test_delete_slide_negative_index(monkeypatch):
    # Bypass authentication
    monkeypatch.setattr(app, 'check_auth', lambda: True)
    # Avoid modifying files
    monkeypatch.setattr(app, 'save_rooms', lambda *args, **kwargs: None)
    
    # Prepare test data
    app.rooms = ['test_room']
    app.slides = {'test_room': ['/tmp/nofile.png']}
    app.last_updates = {'test_room': time.time()}

    client = app.app.test_client()
    response = client.post('/delete_slide/test_room/-1')
    assert response.status_code == 404
