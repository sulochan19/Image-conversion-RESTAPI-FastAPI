
from datetime import timedelta, datetime
import os

from PIL import Image
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import SessionLocal
from dotenv import load_dotenv
import models
from schemas import User, TokenData


load_dotenv()  # take environment variables from .env

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    """Verify that a plaintext password matches a hashed password.
    
    Arguments:
    plain_password -- the plaintext password to verify
    hashed_password -- the hashed password to compare against
    
    Returns:
    True if the plaintext password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Generate a password hash for a given password.
    
    Arguments:
    password -- the password to generate the hash for
    
    Returns:
    The password hash.
    """
    return pwd_context.hash(password)


def get_user(username: str, db: Session = Depends(get_db)):
    """Retrieve a user from the database by username.
    
    Arguments:
    username -- the username of the user to retrieve
    db -- the database session
    
    Returns:
    The user, if found, or None if no such user exists.
    """
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    """
    Authenticate a user by checking the provided username and password against the database.
    
    Args:
        username (str): the username of the user being authenticated
        password (str): the password of the user being authenticated
        db (Session, optional): a database session object (default value is obtained from the `get_db` function using dependency injection)
    
    Returns:
        user (object): the user object if the provided username and password are valid
        None (NoneType): None if the provided username or password are invalid
    """
    
    # Retrieve the user object from the database
    user = get_user(username,db)
    
    # If the user does not exist or the provided password does not match the hashed password in the database, return None
    if not user or not verify_password(password, user.password):
        return None
    
    # If the username and password are valid, return the user object
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Creates an access token by encoding a dictionary of data and
    an optional expiration time (in seconds).
    
    Args:
        data (dict): A dictionary of data to be encoded in the JWT
        expires_delta (timedelta, optional): An optional expiration time for the JWT, in seconds. If not provided, the default is 15 minutes.
        
    Returns:
        str: The JWT access token
    """
    to_encode = data.copy()
    # if an expiration time is not provided, default to 15 minutes
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    # add the expiration time to the data to be encoded
    to_encode.update({"exp": expire})
    # encode the data using the secret key and specified algorithm
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Retrieves the current user from the provided JWT access token.
    
    Args:
        token (str): The JWT access token
        db (Session): A database session for interacting with the database
        
    Returns:
        User: The current user
        
    Raises:
        HTTPException: If the credentials are invalid or the user cannot be found
    """
    # create an exception to be raised if the credentials are invalid
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # decode the JWT access token using the secret key and specified algorithm
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # get the username from the JWT payload
        username: str = payload.get("sub")
        # if the username is not present in the payload, raise the exception
        if username is None:
            raise credentials_exception
        # create a TokenData object with the username
        token_data = TokenData(username=username)
    except JWTError:
        # if there is an error decoding the JWT, raise the exception
        raise credentials_exception
    # get the user from the database using the username
    user = get_user(username, db)
    # if the user is not found in the database, raise the exception
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Retrieves the current active user.
    
    Args:
        current_user (User): The current user, obtained from the JWT access token
        
    Returns:
        User: The current active user
    """
    return current_user


def save_image(img, file_path):
    """Save an image to a file.
    
    Arguments:
    img -- the image to save
    file_path -- the path of the file to save the image to
    """
    img.save(file_path)

def convert_image(src_path, dest_path):
    """Convert an image from one format to another.
    
    Arguments:
    src_path -- the path of the source image
    dest_path -- the path of the destination image
    """
    src_img = Image.open(src_path)
    dest_img = src_img.convert("RGB")
    save_image(dest_img, dest_path)


def get_conversion_requests(db):
    """Retrieve all conversion requests from the database.
    
    Arguments:
    db -- the database session
    
    Returns:
    A list of conversion requests.
    """
    return db.query(models.Conversion).all()


def create_user_in_db(db, username, hashed_password):
    """Create a new user in the database.
    
    Arguments:
    db -- the database session
    username -- the username of the new user
    hashed_password -- the hashed password of the new user
    """
    user = models.User(username=username, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)


def create_access_token_for_user(user, expires_delta):
    """Create an access token for a user.
    
    Arguments:
    user -- the user to create the access token for
    expires_delta -- the time duration after which the access token will expire
    
    Returns:
    An access token for the user.
    """
    return create_access_token(data={"sub": user.username}, expires_delta=expires_delta)