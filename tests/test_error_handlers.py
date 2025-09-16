# tests/test_error_handlers.py

def test_404_page(client):
    response = client.get("/nonexistent-page")
    assert response.status_code == 404
    assert b"404" in response.data or b"not found" in response.data.lower()


def test_500_page(client):
    # This disables raising exceptions during tests
    client.raise_server_exceptions = False

    try:
        response = client.get("/trigger-500")
    except Exception:
        # If an exception still gets raised, app didn't handle it
        assert False, "500 error was not handled by Flask error handler"
    else:
        assert response.status_code == 500
        assert b"something went wrong" in response.data.lower()