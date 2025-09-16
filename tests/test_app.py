# tests/test_app.py

def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' route is requested (GET)
    THEN check that the response is valid
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b"Start Swiping Now!" in response.data # Check for some text from homepage