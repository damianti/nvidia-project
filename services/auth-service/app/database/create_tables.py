from app.database.config import engine
from app.database.models import Base
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME
from sqlalchemy import inspect

logger = setup_logger(SERVICE_NAME)


def create_tables():
    """Create all tables in the database"""

    try:
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(
            "database.tables.created",
            extra={
                "event": "database.tables.created",
                "tables": tables,
                "table_count": len(tables),
            },
        )
    except Exception as e:
        logger.error(
            "database.tables.create_error",
            extra={
                "event": "database.tables.create_error",
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


if __name__ == "__main__":
    create_tables()
