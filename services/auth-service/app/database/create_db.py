import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.utils.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, SERVICE_NAME
from app.utils.logger import setup_logger

logger = setup_logger(SERVICE_NAME)


def create_database():
    """Create the database if it doesn't exist"""

    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database="postgres"  
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exist = cursor.fetchone()

        if not exist:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info(
                "database.created",
                extra={
                    "event": "database.created",
                    "database_name": DB_NAME,
                    "host": DB_HOST,
                    "port": DB_PORT
                }
            )
        else:
            logger.info(
                "database.exists",
                extra={
                    "event": "database.exists",
                    "database_name": DB_NAME,
                    "host": DB_HOST,
                    "port": DB_PORT
                }
            )
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(
            "database.create_error",
            extra={
                "event": "database.create_error",
                "database_name": DB_NAME,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise

if __name__ == "__main__":
    create_database()