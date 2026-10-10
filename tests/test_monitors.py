MONITOR = {"name": "Example", "url": "https://example.com", "interval_seconds": 60}


def test_monitors_require_login(client):
    assert client.get("/monitors").status_code == 401


def test_create_and_list_monitor(client, make_user):
    headers = make_user()
    created = client.post("/monitors", json=MONITOR, headers=headers)
    assert created.status_code == 201
    listed = client.get("/monitors", headers=headers)
    assert [m["name"] for m in listed.json()] == ["Example"]


def test_invalid_url_is_rejected(client, make_user):
    headers = make_user()
    response = client.post(
        "/monitors", json={**MONITOR, "url": "not-a-url"}, headers=headers
    )
    assert response.status_code == 422


def test_update_changes_only_sent_fields(client, make_user):
    headers = make_user()
    monitor_id = client.post("/monitors", json=MONITOR, headers=headers).json()["id"]
    response = client.patch(
        f"/monitors/{monitor_id}", json={"is_active": False}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["name"] == "Example"


def test_delete_monitor(client, make_user):
    headers = make_user()
    monitor_id = client.post("/monitors", json=MONITOR, headers=headers).json()["id"]
    assert client.delete(f"/monitors/{monitor_id}", headers=headers).status_code == 204
    assert client.get(f"/monitors/{monitor_id}", headers=headers).status_code == 404


def test_users_cannot_see_each_others_monitors(client, make_user):
    alice = make_user(email="alice@example.com")
    bob = make_user(email="bob@example.com")
    monitor_id = client.post("/monitors", json=MONITOR, headers=alice).json()["id"]

    assert client.get("/monitors", headers=bob).json() == []
    assert client.get(f"/monitors/{monitor_id}", headers=bob).status_code == 404
    assert (
        client.patch(
            f"/monitors/{monitor_id}", json={"name": "Hacked"}, headers=bob
        ).status_code
        == 404
    )
    assert client.delete(f"/monitors/{monitor_id}", headers=bob).status_code == 404