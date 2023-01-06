from fastapi import FastAPI, status, UploadFile
from schemas import Conversion
from database import SessionLocal, engine
from typing import List
from PIL import Image
from fastapi.staticfiles import StaticFiles
import logging
import models
import datetime
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency
db = SessionLocal()


@app.get("/list-conversion-requests",response_model = List[Conversion],status_code=200)
def get_all_conversion_requests():
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('request made for listing all conversion')
    conversion_requets = db.query(models.Conversion).all()
    return conversion_requets

@app.post("/uploadfile/",status_code=status.HTTP_201_CREATED)
def convert_jpeg_to_png(file: UploadFile):
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('request made for uploading file for conversion')
    with Image.open(file.file) as img:
        try:
            #save the user input jpeg image
            img.save(os.path.join(BASE_DIR,"static/media/")+file.filename,"jpeg")
            # Convert the image to PNG
            png_img = img.convert("RGB")
            png_img.save(os.path.join(BASE_DIR,"static/media/")+file.filename.split('.')[0]+".png")

            source_file_url = str("static/media/"+file.filename)
            png_url = str("static/media/"+file.filename.split('.')[0]+".png")
            logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
            logging.info("Image has been successfully converted and saved")
        except:
            logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.ERROR)
            logging.error("Error occurred in converting the image")
        
        #storing the request in database
        new_conversion=models.Conversion(
        source_file = source_file_url,
        png_url = png_url,
        status = "success",
        created_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )
        
        try:
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