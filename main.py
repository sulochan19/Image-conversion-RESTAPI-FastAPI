from fastapi import Depends, FastAPI, HTTPException, status, UploadFile
from schemas import Conversion, UserInDB, User, Token, TokenData
from database import SessionLocal, engine
from typing import List
from PIL import Image
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import logging
import models
import datetime
from datetime import timedelta
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


models.Base.metadata.create_all(bind=engine)

# new code from here
SECRET_KEY = "5bdef4331cc64c5f0686e9cfae40e57c964b063f3fff9bc378af46f2f6d4a8c0"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


# Dependency
db = SessionLocal()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/register-user/", status_code=status.HTTP_201_CREATED)
def create_user(user: UserInDB):
    db_user = models.User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"status": "success! user has been created"}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/list-conversion-requests",response_model = List[Conversion],status_code=200)
def get_all_conversion_requests(current_user: User = Depends(get_current_active_user)):
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logging.info('request made for listing all conversion')
    conversion_requets = db.query(models.Conversion).all()
    return conversion_requets

@app.post("/uploadfile/",status_code=status.HTTP_201_CREATED)
def convert_jpeg_to_png(file: UploadFile, current_user: User = Depends(get_current_active_user)):
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