from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from urllib.parse import urlparse
from app.utils.config import DATABASE_URL, SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


def validate_database_url(url: str) -> None:
    """Validate DATABASE_URL format and components."""
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure it before starting the service."
        )

    if not url.startswith(("postgresql://", "postgresql+psycopg2://")):
        raise ValueError(
            f"DATABASE_URL must be a PostgreSQL connection string. "
            f"Got: {url[:30]}..."
        )

    try:
        parsed = urlparse(url)
        if not parsed.hostname:
            raise ValueError("DATABASE_URL must include a hostname")
        if not parsed.path or parsed.path == "/":
            raise ValueError("DATABASE_URL must include a database name")
    except Exception as e:
        raise ValueError(f"Invalid DATABASE_URL format: {str(e)}")


validate_database_url(DATABASE_URL)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
