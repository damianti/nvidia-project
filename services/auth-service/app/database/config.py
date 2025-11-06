from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import DATABASE_URL


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