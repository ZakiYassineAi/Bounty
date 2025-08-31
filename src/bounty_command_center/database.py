from contextlib import contextmanager
from sqlmodel import create_engine, SQLModel, Session

# Define the path for the SQLite database file
DATABASE_URL = "sqlite:///bounty_data.db"

# Create the database engine
# `connect_args` is specific to SQLite to disable same-thread checking,
# which is useful for some web frameworks but good practice to have.
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """
    Initializes the database and creates all tables defined by SQLModel models.
    This function should be called once when the application starts.
    """
    # The SQLModel.metadata.create_all() function uses the engine to create
    # all the tables that inherit from SQLModel.
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    """
    Provides a new database session for performing transactions.
    This is a context manager, so it should be used with a `with` statement.
    """
    with Session(engine) as session:
        yield session
