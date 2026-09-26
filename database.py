from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    UniqueConstraint
)
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
# CARS
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
# USERS
# =========================

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )
    password = Column(String, nullable=False)


# =========================
# BIDS
# =========================

class BidDB(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    amount = Column(Float, nullable=False)


# =========================
# SHOPPING CART
# =========================

class CartItemDB(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_key = Column(String, nullable=False, index=True)
    car_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint(
            "cart_key",
            "car_id",
            name="uq_cart_key_car_id"
        ),
    )


# =========================
# CREATE TABLES
# =========================

Base.metadata.create_all(bind=engine)