import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Get database credentials from environment variables
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
SECRET_KEY = os.getenv("SECRET_KEY")

def connect_to_postgres():
    try:
        connection = psycopg2.connect(
            dbname=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT,
        )
        cursor = connection.cursor()
        query = """
        CREATE SCHEMA IF NOT EXISTS SALES_DB;
        SET search_path TO SALES_DB;
        """
        cursor.execute(query)
        cursor.execute("SET TIME ZONE 'GMT-7';")
        connection.commit()
        return connection
    except psycopg2.Error as e:
        return None
