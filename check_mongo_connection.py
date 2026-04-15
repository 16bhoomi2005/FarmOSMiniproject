import pymongo
import sys

# Connection String from data_loader.py
MONGO_URI = "mongodb+srv://bhoomivaishya06_db_user:GuysqjmNsQjvgZuj@cluster0.wqfcwpe.mongodb.net/?appName=Cluster0"

print("🔄 Testing MongoDB Connection...")
print(f"📡 Connecting to: {MONGO_URI.split('@')[1]}") # Print only the host part for privacy

try:
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Trigger a connection
    client.admin.command('ping')
    print("✅ Connection Successful! MongoDB is reachable.")
except pymongo.errors.ServerSelectionTimeoutError as e:
    print("\n❌ Connection Failed: Server Selection Timeout")
    print("------------------------------------------------")
    print("🔍 DIAGNOSIS: This is likely an IP Whitelist issue.")
    print("------------------------------------------------")
    print("1. Your current IP address is not authorized to access this MongoDB cluster.")
    print("2. Go to MongoDB Atlas Console -> Network Access.")
    print("3. Add your current IP address (or 0.0.0.0/0 for testing).")
    print(f"\nDetailed Error: {e}")
except Exception as e:
    print(f"\n❌ Connection Failed: {e}")
