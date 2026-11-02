import os
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "cine_paradiso"),
        connection_timeout=5,
    )
