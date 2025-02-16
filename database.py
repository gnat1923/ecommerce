from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from objects import Base

# SQLite database URL
DATABASE_URL = "sqlite:///ecommerce.db"

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)

# Create all tables
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)

# function to get a db session
def get_session():
    return Session()