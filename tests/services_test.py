import services
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_verify_password():
    # Hash a password using the pwd_context object
    hashed_password = pwd_context.hash("test_password")

    # Test that the correct plain password verifies correctly
    assert services.verify_password("test_password", hashed_password) == True

    # Test that an incorrect plain password does not verify
    assert services.verify_password("incorrect_password", hashed_password) == False


def test_get_password_hash():
    # Test that the function returns a hashed password
    assert pwd_context.identify(services.get_password_hash("test_password")) == "bcrypt"




