from fastapi.testclient import TestClient
from dotenv import load_dotenv
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from services import get_db, authenticate_user, create_access_token
from database import Base
import os

# take environment variables from .env
load_dotenv()

# Extract environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
TEST_POSTGRES_DB = os.getenv("TEST_POSTGRES_DB")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{TEST_POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# Drop and create all tables in the test database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

TEST_USERNAME = "test_user"
TEST_PASSWORD = "testuser"

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def generate_access_token():
    db = next(override_get_db())
    user = authenticate_user(TEST_USERNAME, TEST_PASSWORD, db)
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return access_token


def test_create_user():
    response = client.post(
        "/register-user/",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        },
    )
    assert response.status_code == 201
    assert response.json() == {"status": "success! user has been created"}


def test_login_for_access_token():
    response = client.post(
        "/token",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        },)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()


def test_get_all_conversion_requests():
    access_token = generate_access_token()
    response = client.get("/list-conversion-requests",
                          headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200


def test_convert_jpeg_to_png():
    access_token = generate_access_token()
    # opening a test image
    with open("tests/_117310488_16.jpg", "rb") as imageFile:
        # Send a request to the convert_jpeg_to_png endpoint with the test JPEG image
        response = client.post("/uploadfile/", files={"file": imageFile}, headers={
                               'Authorization': f'Bearer {access_token}'})
    # Assert that the response status code is 201 CREATED
    assert response.status_code == 201
    # Assert that the response contains the URL of the converted PNG image
    assert "png-url" in response.json()
    # Assert that the response contains the status of the conversion
    assert "status" in response.json()
    # Assert that the status of the conversion is "Success"
    assert response.json()["status"] == "Success"
