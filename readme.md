To install the project: <br />
    1)Clone the project from github <br />
    2)Create and activate Virtual Environment <br />
    3)Install the dependencies from requirements.txt <br />
    4)create a file name .env and set the following environment variables <br />
        
        SECRET_KEY = " " -> To generate the SECRET_KEY run command : openssl rand -hex 32  <br />
        ALGORITHM = "HS256"
        POSTGRES_USER=
        POSTGRES_PASSWORD=
        POSTGRES_SERVER=
        POSTGRES_DB=

        TEST_POSTGRES_DB=  (separate database to run unittest)<br />
        
    5)Command to run the project-> uvicorn main:app --reload <br />
    6)Go to /docs for all the routes <br />
    7)Command to run the test -> python -m pytest <br />

python version = 3.11.1
