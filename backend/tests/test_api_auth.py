from fastapi.testclient import TestClient


def test_login_succeeds_with_demo_password(client: TestClient):
    response = client.post("/api/auth/login", json={"reg_no": "DEMO001", "password": "campus@123"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["reg_no"] == "DEMO001"
    assert body["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client: TestClient):
    response = client.post("/api/auth/login", json={"reg_no": "DEMO001", "password": "wrong"})
    assert response.status_code == 401


def test_login_fails_for_unknown_user(client: TestClient):
    response = client.post("/api/auth/login", json={"reg_no": "NOBODY", "password": "campus@123"})
    assert response.status_code == 401


def test_me_requires_a_token(client: TestClient):
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_garbage_token(client: TestClient):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_returns_profile_for_valid_token(client: TestClient):
    token = client.post("/api/auth/login", json={"reg_no": "DEMO001", "password": "campus@123"}).json()[
        "access_token"
    ]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["reg_no"] == "DEMO001"


def test_admin_route_rejects_student_token(client: TestClient):
    token = client.post("/api/auth/login", json={"reg_no": "DEMO001", "password": "campus@123"}).json()[
        "access_token"
    ]
    response = client.post("/api/admin/reindex", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_route_allows_admin_token(client: TestClient):
    token = client.post("/api/auth/login", json={"reg_no": "admin", "password": "campus@123"}).json()[
        "access_token"
    ]
    response = client.post("/api/admin/reindex", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
