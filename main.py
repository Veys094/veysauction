from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta

from database import SessionLocal, CarDB, UserDB, BidDB


app = FastAPI(title="VeysAuction API")


# =========================================================
# DATABASE
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/database-test")
def database_test(db=Depends(get_db)):
    cars_count = db.query(CarDB).count()
    users_count = db.query(UserDB).count()

    return {
        "database": "connected",
        "cars_count": cars_count,
        "users_count": users_count
    }


# =========================================================
# TEMPLATES / STATIC
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")


# =========================================================
# PYDANTIC MODELS
# =========================================================

class Car(BaseModel):
    brand: str
    model: str
    year: int
    price: float
    plate_number: str


class User(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    username: str
    password: str


class Bid(BaseModel):
    car_id: int
    username: str
    amount: float


# =========================================================
# AUCTION DATA
# =========================================================

auction_end = datetime.now() + timedelta(days=1)

cars = [
    {
        "id": 1,
        "brand": "BMW",
        "model": "X5",
        "year": 2020,
        "price": 25000,
        "plate_number": "10 OO 001",
        "image": "bmw.jpg"
    },
    {
        "id": 2,
        "brand": "Toyota",
        "model": "Camry",
        "year": 2021,
        "price": 22000,
        "plate_number": "10 TO 002",
        "image": "toyota.jpg"
    },
    {
        "id": 3,
        "brand": "Hyundai",
        "model": "Elantra",
        "year": 2017,
        "price": 15000,
        "plate_number": "77 QZ094",
        "image": "elantra.jpg"
    }
]


def load_cars_to_database():
    db = SessionLocal()

    try:
        if db.query(CarDB).count() == 0:

            for car in cars:
                new_car = CarDB(
                    id=car["id"],
                    brand=car["brand"],
                    model=car["model"],
                    year=car["year"],
                    price=car["price"],
                    plate_number=car["plate_number"],
                    image=car["image"]
                )

                db.add(new_car)

            db.commit()

    finally:
        db.close()


load_cars_to_database()


# Bids are currently stored in memory
bids = []


# =========================================================
# HELPER
# =========================================================

def get_car_from_memory(car_id: int):

    for car in cars:
        if car["id"] == car_id:
            return car

    return None


def sync_car_price(car_id: int, price: float):

    car = get_car_from_memory(car_id)

    if car:
        car["price"] = price


# =========================================================
# MAIN PAGE
# =========================================================

@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "cars": cars,
            "bids": bids,
            "auction_end": auction_end
        }
    )


# =========================================================
# CAR API
# =========================================================

@app.get("/cars")
def get_cars(db=Depends(get_db)):

    cars_from_db = db.query(CarDB).all()

    return [
        {
            "id": car.id,
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "price": car.price,
            "plate_number": car.plate_number,
            "image": car.image
        }
        for car in cars_from_db
    ]


@app.get("/cars/{car_id}")
def get_car(
    car_id: int,
    db=Depends(get_db)
):

    car = (
        db.query(CarDB)
        .filter(CarDB.id == car_id)
        .first()
    )

    if not car:
        raise HTTPException(
            status_code=404,
            detail="Car not found"
        )

    return {
        "id": car.id,
        "brand": car.brand,
        "model": car.model,
        "year": car.year,
        "price": car.price,
        "plate_number": car.plate_number,
        "image": car.image
    }


@app.post("/cars")
def create_car(
    car: Car,
    db=Depends(get_db)
):

    new_car = CarDB(
        brand=car.brand,
        model=car.model,
        year=car.year,
        price=car.price,
        plate_number=car.plate_number,
        image=""
    )

    db.add(new_car)
    db.commit()
    db.refresh(new_car)

    return {
        "id": new_car.id,
        "brand": new_car.brand,
        "model": new_car.model,
        "year": new_car.year,
        "price": new_car.price,
        "plate_number": new_car.plate_number,
        "image": new_car.image
    }


@app.put("/cars/{car_id}")
def update_car(
    car_id: int,
    car: Car,
    db=Depends(get_db)
):

    existing_car = (
        db.query(CarDB)
        .filter(CarDB.id == car_id)
        .first()
    )

    if not existing_car:
        raise HTTPException(
            status_code=404,
            detail="Car not found"
        )

    existing_car.brand = car.brand
    existing_car.model = car.model
    existing_car.year = car.year
    existing_car.price = car.price
    existing_car.plate_number = car.plate_number

    db.commit()
    db.refresh(existing_car)

    sync_car_price(
        car_id,
        car.price
    )

    return {
        "id": existing_car.id,
        "brand": existing_car.brand,
        "model": existing_car.model,
        "year": existing_car.year,
        "price": existing_car.price,
        "plate_number": existing_car.plate_number,
        "image": existing_car.image
    }


@app.delete("/cars/{car_id}")
def delete_car(
    car_id: int,
    db=Depends(get_db)
):

    car = (
        db.query(CarDB)
        .filter(CarDB.id == car_id)
        .first()
    )

    if not car:
        raise HTTPException(
            status_code=404,
            detail="Car not found"
        )

    db.delete(car)
    db.commit()

    memory_car = get_car_from_memory(car_id)

    if memory_car:
        cars.remove(memory_car)

    return {
        "message": "Car deleted successfully"
    }


# =========================================================
# CAR DETAILS
# =========================================================

@app.get("/cars/{car_id}/details")
def car_details(
    car_id: int,
    request: Request
):

    car = get_car_from_memory(car_id)

    if not car:
        raise HTTPException(
            status_code=404,
            detail="Car not found"
        )

    car_bids = [
        bid
        for bid in bids
        if bid["car_id"] == car_id
    ]

    return templates.TemplateResponse(
        request=request,
        name="car_detail.html",
        context={
            "request": request,
            "car": car,
            "bids": car_bids
        }
    )


# =========================================================
# BID PAGE
# =========================================================

@app.get("/cars/{car_id}/bid")
def bid_page(
    car_id: int,
    request: Request
):

    car = get_car_from_memory(car_id)

    if not car:
        raise HTTPException(
            status_code=404,
            detail="Car not found"
        )

    return templates.TemplateResponse(
        request=request,
        name="bid.html",
        context={
            "request": request,
            "car": car,
            "error": None
        }
    )


# =========================================================
# MAKE BID
# =========================================================

@app.post("/cars/{car_id}/bid")
def make_bid(
    car_id: int,
    request: Request,
    username: str = Form(...),
    amount: float = Form(...)
):

    if datetime.now() >= auction_end:
        raise HTTPException(
            status_code=400,
            detail="Auction has ended"
        )

    car = get_car_from_memory(car_id)

    if not car:
        raise HTTPException(
            status_code=404,
            detail="Car not found"
        )

    # =====================================================
    # BUG #3 — SYSTEM ACCEPTS NEGATIVE BID
    # =====================================================

    if amount < 0:

        return templates.TemplateResponse(
            request=request,
            name="bid.html",
            context={
                "request": request,
                "car": car,
                "error": "negative"
            },
            status_code=200
        )

    # =====================================================
    # BUG #2 — SYSTEM ACCEPTS BID LOWER THAN CURRENT PRICE
    # =====================================================

    if amount <= car["price"]:

        return templates.TemplateResponse(
            request=request,
            name="bid.html",
            context={
                "request": request,
                "car": car,
                "error": True
            },
            status_code=200
        )

    new_bid = {
        "car_id": car_id,
        "username": username,
        "amount": amount
    }

    bids.append(new_bid)

    car["price"] = amount

    return RedirectResponse(
        url=f"/cars/{car_id}/details",
        status_code=303
    )


# =========================================================
# WINNER
# =========================================================

@app.get("/cars/{car_id}/winner")
def get_winner(car_id: int):

    car = get_car_from_memory(car_id)

    if not car:
        raise HTTPException(
            status_code=404,
            detail="Car not found"
        )

    car_bids = [
        bid
        for bid in bids
        if bid["car_id"] == car_id
    ]

    if not car_bids:
        return {
            "message": "No bids for this car"
        }

    winner = max(
        car_bids,
        key=lambda bid: bid["amount"]
    )

    return {
        "car_id": car_id,
        "winner": winner["username"],
        "winning_bid": winner["amount"]
    }


# =========================================================
# REGISTER PAGE
# =========================================================

@app.get("/register")
def register_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "request": request
        }
    )


# =========================================================
# REGISTER USER
# =========================================================

@app.post("/register")
def register_user(
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):

    existing_user = (
        db.query(UserDB)
        .filter(UserDB.username == username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    new_user = UserDB(
        username=username,
        password=password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(
        url="/login",
        status_code=303
    )


# =========================================================
# USERS API
# =========================================================

@app.post("/users")
def create_user(
    user: User,
    db=Depends(get_db)
):

    existing_user = (
        db.query(UserDB)
        .filter(UserDB.username == user.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    new_user = UserDB(
        username=user.username,
        password=user.password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    users_count = db.query(UserDB).count()

    return {
        "id": new_user.id,
        "username": new_user.username,
        "password": new_user.password,
        "users_in_database": users_count
    }


@app.get("/users")
def get_users(db=Depends(get_db)):

    users_from_db = db.query(UserDB).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "password": user.password
        }
        for user in users_from_db
    ]


@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    db=Depends(get_db)
):

    user = (
        db.query(UserDB)
        .filter(UserDB.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user.id,
        "username": user.username,
        "password": user.password
    }


# =========================================================
# LOGIN PAGE
# =========================================================

@app.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": None
        }
    )


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):

    user = (
        db.query(UserDB)
        .filter(UserDB.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # =====================================================
    # BUG #1 — INTENTIONALLY CREATED FOR QA TRAINING
    # =====================================================

    if user.password != password:

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": True
            },
            status_code=200
        )

    return RedirectResponse(
        url="/",
        status_code=303
    )