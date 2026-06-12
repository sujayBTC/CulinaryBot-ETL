import os

from dotenv import load_dotenv

load_dotenv()

BACK_END_URL = os.getenv("BACK_END")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "etl")
SOURCE_ID_FIELD = os.getenv("SOURCE_ID_FIELD", "id")
RECIPES_COLLECTION = os.getenv("RECIPES_COLLECTION", "recipes")

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("APIKEY")
MODEL = os.getenv("MODEL")
