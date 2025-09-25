from faker import Faker
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

from api.models import db, Users, Customers, Drivers, Vehicles, Bookings, Payments, BookingCharges

faker = Faker("es_ES")

# ====== USERS ======
def seed_users():
    users = []
    roles = ["admin", "editor", "driver", "customer"]

    for _ in range(10):
        role = random.choice(roles)
        user = Users(
            email=faker.unique.email(),
            password=generate_password_hash("password123"),
            username=faker.user_name(),
            firstname=faker.first_name(),
            lastname=faker.last_name(),
            phone=faker.phone_number(),
            avatar_image=None,
            is_active=True,
            role=role,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        users.append(user)
    return users


# ====== CUSTOMERS ======
def seed_customers(users):
    customers = []
    for u in users:
        if u.role == "customer":
            customer = Customers(
                user_id=u.id,
                created_at=datetime.utcnow()
            )
            customers.append(customer)
    return customers


# ====== DRIVERS ======
def seed_drivers(users):
    drivers = []
    for u in users:
        if u.role == "driver":
            driver = Drivers(
                user_id=u.id,
                hire_date=datetime.utcnow() - timedelta(days=random.randint(30, 500)),
                active=True
            )
            drivers.append(driver)
    return drivers


# ====== VEHICLES ======
def seed_vehicles(drivers):
    vehicles = []
    car_models = ["Toyota Prius", "Ford Focus", "Tesla Model 3", "Mercedes Vito", "Volkswagen Golf"]
    for d in drivers:
        vehicle = Vehicles(
            driver_id=d.id,
            plate_number=faker.license_plate(),
            brand=random.choice(["Toyota", "Ford", "Tesla", "Mercedes", "Volkswagen"]),
            model=random.choice(car_models),
            year=random.randint(2015, 2023),
            capacity=random.choice([4, 5, 7]),
            active=True
        )
        vehicles.append(vehicle)
    return vehicles


# ====== BOOKINGS ======
def seed_bookings(customers, drivers, vehicles):
    bookings = []
    for _ in range(10):
        customer = random.choice(customers)
        driver = random.choice(drivers)
        vehicle = random.choice(vehicles)

        pickup_time = datetime.utcnow() + timedelta(days=random.randint(-10, 10))

        booking = Bookings(
            customer_id=customer.id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            pickup_address=faker.address(),
            dropoff_address=faker.address(),
            scheduled_pickup_at=pickup_time,
            status=random.choice(["pending", "assigned", "completed", "cancelled"]),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        bookings.append(booking)
    return bookings


# ====== PAYMENTS ======
def seed_payments(bookings):
    payments = []
    for b in bookings:
        payment = Payments(
            booking_id=b.id,
            amount=random.uniform(10, 100),
            currency="eur",
            status=random.choice(["paid", "pending", "refunded"]),
            method=random.choice(["card", "paypal", "cash"]),
            created_at=datetime.utcnow()
        )
        payments.append(payment)
    return payments


# ====== BOOKING CHARGES ======
def seed_booking_charges(bookings):
    charges = []
    for b in bookings:
        charge = BookingCharges(
            booking_id=b.id,
            base_fare=random.uniform(5, 15),
            distance_fare=random.uniform(5, 20),
            time_fare=random.uniform(2, 10),
            surcharge=random.uniform(0, 5),
            total=random.uniform(15, 50)
        )
        charges.append(charge)
    return charges


# # ====== MAIN SEED FUNCTION ======
# def run_seed():
#     print("🌱 Starting DriverSpain seed...")

#     # 1. Users
#     users = seed_users()
#     db.session.add_all(users)
#     db.session.commit()

#     # 2. Customers & Drivers
#     customers = seed_customers(users)
#     drivers = seed_drivers(users)
#     db.session.add_all(customers + drivers)
#     db.session.commit()

#     # 3. Vehicles
#     vehicles = seed_vehicles(drivers)
#     db.session.add_all(vehicles)
#     db.session.commit()

#     # 4. Bookings
#     bookings = seed_bookings(customers, drivers, vehicles)
#     db.session.add_all(bookings)
#     db.session.commit()

#     # 5. Payments
#     payments = seed_payments(bookings)
#     db.session.add_all(payments)
#     db.session.commit()

#     # 6. Booking Charges
#     charges = seed_booking_charges(bookings)
#     db.session.add_all(charges)
#     db.session.commit()

#     print("✅ DriverSpain seed complete.")
