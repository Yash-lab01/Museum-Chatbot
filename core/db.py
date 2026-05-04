import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

dbconfig = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="museum_pool",
    pool_size=5,
    pool_reset_session=True,
    **dbconfig
)

def get_db_connection():
    """Returns a connection from the MySQL connection pool."""
    try:
        return pool.get_connection()
    except mysql.connector.Error as err:
        print(f"Error getting connection from pool: {err}")
        raise