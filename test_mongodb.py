import streamlit as st
from pymongo import MongoClient

uri = st.secrets["MONGO_URI"]
database_name = st.secrets["MONGO_DATABASE"]

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)

    client.admin.command("ping")

    db = client[database_name]

    print("MongoDB connection successful!")
    print("Database:", db.name)

    client.close()

except Exception as e:
    print("MongoDB connection failed:")
    print(type(e).__name__, str(e))