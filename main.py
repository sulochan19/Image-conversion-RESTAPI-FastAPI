from database import engine
from datetime import timedelta
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from PIL import Image
from schemas import Conversion, UserInDB, User, Token
from sqlalchemy.orm import Session
from typing import List
import datetime
import logging
import models
import services
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ACCESS_TOKEN_EXPIRE_MINUTES = 30


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/register-user/", status_code=status.HTTP_201_CREATED)
def create_user(user: UserInDB, db: Session = Depends(services.get_db)):
    db_user = models.User(username=user.username, hashed_password=services.get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"status": "success! user has been created"}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(services.get_db)):
    user = services.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = services.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/uploadfile/",status_code=status.HTTP_201_CREATED)
def convert_jpeg_to_png(file: UploadFile, current_user: User = Depends(services.get_current_active_user), db: Session = Depends(services.get_db)):
    print("current user is ", current_user)
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('request made for uploading file for conversion')
    source_file_url = ''
    png_url = ''
    with Image.open(file.file) as img:
        try:
            #save the user input jpeg image
            img.save(os.path.join(BASE_DIR,"static/media/")+file.filename,"jpeg")
            # Convert the image to PNG
            png_img = img.convert("RGB")
            png_img.save(os.path.join(BASE_DIR,"static/media/")+file.filename.split('.')[0]+".png")

            source_file_url += "static/media/"+file.filename
            png_url += "static/media/"+file.filename.split('.')[0]+".png"
            logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
            logging.info("Image has been successfully converted and saved")
        except:
            logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.ERROR)
            logging.error("Error occurred in converting the image")
        
    try:
        # storing the request in database
        new_conversion=models.Conversion(
        source_file = source_file_url,
        png_url = png_url,
        status = "success",
        created_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )
        db.add(new_conversion)
        db.commit()
        db.refresh(new_conversion)
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        logging.info("Request for image conversion has been successfully stored in database")
    except:
        db.close()
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.ERROR)
        logging.error("Request for image conversion could not be stored in database")   
    return {"png-url" : png_url, "status" : "Success"}


@app.get("/list-conversion-requests",response_model = List[Conversion],status_code=200)
def get_all_conversion_requests(current_user: User = Depends(services.get_current_active_user), db: Session = Depends(services.get_db)):
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('request made for listing all conversion')
    conversion_requets = db.query(models.Conversion).all()
    return conversion_requets