import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/uptime_test"


def create_test_database():
    admin_engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'uptime_test'")
        )
        if not exists:
            conn.execute(text("CREATE DATABASE uptime_test"))
    admin_engine.dispose()


create_test_database()
engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(client):
    def _make_user(email="user@example.com", password="testpass123"):
        client.post("/auth/register", json={"email": email, "password": password})
        response = client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make_user