import datetime
import logging
import os

import models
import services
from PIL import Image
from datetime import timedelta
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

from database import engine
from schemas import Conversion, Token, User, UserInDB

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ACCESS_TOKEN_EXPIRE_MINUTES = 30


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/register-user/", status_code=status.HTTP_201_CREATED)
def create_user(user: UserInDB, db: Session = Depends(services.get_db)):
    """Create a new user.
    
    Arguments:
    user -- the user to create
    db -- the database session
    
    Returns:
    A dictionary containing the status of the user creation.
    """
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('Request made for creating user')
    services.create_user_in_db(db, user.username, services.get_password_hash(user.password))
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('User has been created successfully')
    return {"status": "success! user has been created"}


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(services.get_db)):
    """Log in a user and return an access token.
    
    Arguments:
    form_data -- the login form data
    db -- the database session
    
    Returns:
    A dictionary containing the access token and the token type.
    
    Raises:
    HTTPException -- if the login fails
    """
    user = services.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = services.create_access_token_for_user(user, access_token_expires)
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('Access token has been generated')
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/uploadfile/", status_code=status.HTTP_201_CREATED)
def convert_jpeg_to_png(file: UploadFile, current_user: User = Depends(services.get_current_active_user), db: Session = Depends(services.get_db)):
    """Convert a JPEG image to a PNG image.
    
    Arguments:
    file -- the JPEG image to convert
    current_user -- the currently logged in user
    db -- the database session
    
    Returns:
    A dictionary containing the URL of the converted PNG image and the status of the conversion.
    """
    
    logging.info("Received request to convert JPEG to PNG")
    
    # Save the user input JPEG image
    jpeg_file_path = "static/media/" + file.filename
    services.save_image(Image.open(file.file), jpeg_file_path)
    
    # Convert the image to PNG
    png_file_path =  "static/media/" + file.filename.split('.')[0] + ".png"
    services.convert_image(jpeg_file_path, png_file_path)
    
    # Store the conversion request in the database
    new_conversion = models.Conversion(
        source_file=jpeg_file_path,
        png_url= "static/media/" + file.filename.split('.')[0] + ".png",
        status="success",
        created_at=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )
    db.add(new_conversion)
    db.commit()
    db.refresh(new_conversion)
    
    logging.info("Completed JPEG to PNG conversion")
    return {"png-url": png_file_path, "status": "Success"}


@app.get("/list-conversion-requests",response_model = List[Conversion],status_code=200)
def get_all_conversion_requests(current_user: User = Depends(services.get_current_active_user), db: Session = Depends(services.get_db)):
    """Retrieve a list of all conversion requests.
    
    Arguments:
    db -- the database session
    
    Returns:
    A list of all conversion requests.
    """
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('Request made for listing all conversion')
    return services.get_conversion_requests(db)


