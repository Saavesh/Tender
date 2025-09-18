def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Tender" in response.data

def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"About" in response.data

def test_error_404(client):
    response = client.get("/thispagedoesnotexist")
    assert response.status_code == 404
    assert b"404" in response.data or b"not found" in response.data.lower()

def test_trigger_500(client):
    client.raise_server_exceptions = False
    response = client.get("/trigger-500")
    assert response.status_code == 500
    assert b"something went wrong" in response.data or b"try again later" in response.data.lower()