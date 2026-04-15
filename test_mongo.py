import pymongo
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.environ.get('MONGO_URI')

print(f"🔍 Testing connection to: {uri[:20]}...")
try:
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Connection Successful!")
    print(f"Databases: {client.list_database_names()}")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
