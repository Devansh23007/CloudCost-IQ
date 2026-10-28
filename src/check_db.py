
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

connection_settings = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5434"),
    "connect_timeout": 5,
}

def main():
    try:
        with psycopg.connect(**connection_settings) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_database(), current_user, version()"
                )
                database, user, version = cur.fetchone()

        print("Database connection successful!")
        print(f"Database: {database}")
        print(f"User: {user}")
        print(f"PostgreSQL: {version.split(',')[0]}")

    except psycopg.Error as error:
        print(f"Database connection failed: {error}")
        raise SystemExit(1) from error

if __name__ == "__main__":
    main()
