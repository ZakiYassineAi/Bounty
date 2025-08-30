from sqlmodel import create_engine, SQLModel, Session

# Define the path for the SQLite database file
DATABASE_URL = "sqlite:///bounty_data.db"

# Create the database engine
# `connect_args` is specific to SQLite to disable same-thread checking,
# which is useful for some web frameworks but good practice to have.
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """
    Initializes the database.
    For development, this will drop all tables and recreate them, ensuring
    the schema is always in sync with the models.
    WARNING: This will delete all existing data.
    """
    # Import models here to ensure they are registered with SQLModel's metadata
    from . import models

    # In a real production environment, you would use a migration tool like Alembic.
    # For this project's current stage, we drop and recreate for simplicity.
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Provides a new database session for performing transactions.
    """
    with Session(engine) as session:
        yield session
