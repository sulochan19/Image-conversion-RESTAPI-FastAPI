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


def generate_access_token(username=TEST_USERNAME, password=TEST_PASSWORD):
    """
    Generate an access token for the specified user.
    
    Parameters:
    username (str): The username of the user to authenticate.
    password (str): The password of the user to authenticate.
    
    Returns:
    str: The generated access token, or None if authentication fails.
    """
    # Get the database connection
    db = next(override_get_db())
    
    # Authenticate the user
    user = authenticate_user(username, password, db)
    
    # Return None if authentication fails
    if not user:
        return None
    
    # Set the expiration time for the access token
    access_token_expires = timedelta(minutes=30)
    
    # Create the access token
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return access_token


def test_create_user(username=TEST_USERNAME, password=TEST_PASSWORD):
    """
    Test to create a user 
    
    Parameters:
    username (str): The username of the user to create.
    password (str): The password of the user to create.
    
    Returns:
    json: Generates a json with success key and value
    """
    
    # Send a request to create a new user
    response = client.post(
        "/register-user/",
        json={
            "username": username,
            "password": password
        },
    )
    # Check the response status code and body
    assert response.status_code == 201
    assert response.json() == {"status": "success! user has been created"}


def test_login_for_access_token():
    # Send a POST request to the "/token" endpoint with the test username and password
    response = client.post(
        "/token",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        },)
    # Check that the response status code is 200
    assert response.status_code == 200
    # Check that the response contains a JSON object with the "access_token" and "token_type" fields
    assert "access_token" in response.json()
    assert "token_type" in response.json()


def test_get_all_conversion_requests():
    # Generate an access token
    access_token = generate_access_token()
    # Send a GET request to the "/list-conversion-requests" endpoint with the access token in the headers
    response = client.get("/list-conversion-requests",
                          headers={'Authorization': f'Bearer {access_token}'})
     # Check that the response status code is 200
    assert response.status_code == 200


def test_convert_jpeg_to_png():
    # Generate an access token
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
