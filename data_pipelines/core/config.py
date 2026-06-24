import os

from dotenv import load_dotenv

load_dotenv()

BACK_END_URL = os.getenv("BACK_END")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "etl")
SOURCE_ID_FIELD = os.getenv("SOURCE_ID_FIELD", "id")
RECIPES_COLLECTION = os.getenv("RECIPES_COLLECTION", "recipes")
KEYWORDS_COLLECTION = os.getenv("KEYWORDS_COLLECTION","keywords")
AUDIT_LOGS_COLLECTION = os.getenv("AUDIT_LOGS_COLLECTION", "audit_logs")
AUDITS_COLLECTION = "audit_logs"

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
