
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "sqlite:///./veysauction.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


# =========================
# CAR
# =========================

class CarDB(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    plate_number = Column(String, nullable=False)
    image = Column(String, nullable=True)


# =========================
# USER
# =========================

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)


# =========================
# BID
# =========================

class BidDB(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    amount = Column(Float, nullable=False)


# =========================
# CREATE TABLES
# =========================

Base.metadata.create_all(bind=engine)

