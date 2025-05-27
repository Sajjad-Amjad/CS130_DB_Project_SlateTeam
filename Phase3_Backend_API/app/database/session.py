from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import DATABASE_URL

# Create SQLAlchemy engine with SQL Server specific configuration
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    # Add these SQL Server specific configurations
    connect_args={
        "autocommit": False,
    },
    # Use StaticPool to avoid connection issues
    poolclass=StaticPool,
    # Disable implicit returning for SQL Server compatibility
    implicit_returning=False
)

# Add event listener to handle SQL Server specific settings
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # This ensures proper handling of transactions
    pass

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()