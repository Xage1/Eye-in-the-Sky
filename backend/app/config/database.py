from pymongo import MongoClient
from app.config.settings import settings


client = MongoClient(settings.MONGO_URI)
db = client['Eye-in-the-Sky']