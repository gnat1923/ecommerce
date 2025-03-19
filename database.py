from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

# SQLite database URL
DATABASE_URL = "sqlite:///ecommerce.db"

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)

# Define the Base for declarative models
Base = declarative_base()

# Create all tables
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)

# function to get a db session, with context manager
@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()