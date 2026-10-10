USER = {"email": "alice@example.com", "password": "testpass123"}


def test_register_returns_user_without_password(client):
    response = client.post("/auth/register", json=USER)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client):
    client.post("/auth/register", json=USER)
    response = client.post("/auth/register", json=USER)
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post("/auth/register", json={**USER, "password": "short"})
    assert response.status_code == 422


def test_login_with_wrong_password_fails(client, make_user):
    make_user(email="alice@example.com")
    response = client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "wrongpass123"},
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user(client, make_user):
    headers = make_user(email="alice@example.com")
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"