import pathlib
import pandas as pd
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# from .supertrend_client import Supertrend  # ImportError no parent package
# import supertrend_client  # Works!
from supertrend_client import Supertrend

# import .supertrend_client.Supertrend

# NOTE fastapi-airtable/backend/src/app.py
BASE_DIR = pathlib.Path(__file__).parent  # src


# ===== Schemas
class TextArea(BaseModel):
    content: str


class User(BaseModel):
    id: int
    name: str


class Signup(BaseModel):
    email: str


app = FastAPI()

# Allow CORS for FE/BE communication
# https://fastapi.tiangolo.com/tutorial/cors/?h=cors
origins = ["http://localhost", "http://localhost:3000"]  # Vue

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"message": "Hello, World"}


@app.get("/supertrend")
def read_supertrend(response: Response):
    # Create new instance of Supertrend Client
    # sp_client = supertrend_client.Supertrend(
    #     symbols=["ETH/USDT"], timeframe="1d", limit=100
    # )

    sp_client = Supertrend(symbols=["ETH/USDT"], timeframe="1d", limit=100)

    # Use client and its fetch_data method to return Pandas DF
    # Q: Do I set args to instance vars? eg. symbol=supertrend_client.symbols[0] ?
    # A: Seems to work!
    df = sp_client.fetch_data(
        symbol=sp_client.symbols[0],
        timeframe=sp_client.timeframe,
        limit=sp_client.limit,
    )
    # Seems redundant to pass args again like below...
    # df = sp_client.fetch_data(symbol="ETH/USDT", timeframe="1d", limit=100)

    # Convert to JSON
    # df_json = pd.DataFrame.to_json(df)

    # Pass the retrieved DF into supertrend method
    supertrend_data = sp_client.supertrend(df)
    # Convert to JSON to pass back
    # Q: Converting to JSON necessary?
    # A: I believe so otherwise it's a Pandas DF
    supertrend_json = pd.DataFrame.to_json(supertrend_data)

    response.body = {"data": supertrend_json}
    # return {
    #     "response": response,
    #     "fruit": "apple",
    #     "status_code": response.status_code,
    #     # "df_json": df_json,  # Works
    #     "supertrend_json": supertrend_json,
    # }  # Works
    return {
        "response": response,
    }  # Works as well
