from faker import Faker
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

from api.models import db, Users, Customers, Drivers, Vehicles, Bookings, Payments, BookingCharges, Cities, ServiceTypes

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


# ====== MASTER DATA (Cities, Service Types) ======
def seed_master_data():
    cities = [
        Cities(name="Madrid", active=True),
        Cities(name="Barcelona", active=True),
        Cities(name="Valencia", active=True)
    ]
    service_types = [
        ServiceTypes(code="standard", display_name="Standard", description="Coche estándar"),
        ServiceTypes(code="van", display_name="Van", description="Monovolumen/VAN"),
        ServiceTypes(code="luxury", display_name="Luxury", description="Alta gama")
    ]
    return cities, service_types


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
    makes = ["Toyota", "Ford", "Tesla", "Mercedes", "Volkswagen"]
    models = ["Prius", "Focus", "Model 3", "Vito", "Golf"]
    colors = ["Negro", "Blanco", "Gris", "Azul"]
    types = ["standard", "van", "luxury"]
    for d in drivers:
        vehicle = Vehicles(
            driver_id=d.id,
            plate_number=f"{faker.random_uppercase_letter()}{faker.random_uppercase_letter()}{random.randint(1000,9999)}{faker.random_uppercase_letter()}",
            make=random.choice(makes),
            model=random.choice(models),
            color=random.choice(colors),
            type=random.choice(types),
            seats=random.choice([4, 5, 7]),
            luggage_large=random.choice([0, 1, 2]),
            luggage_small=random.choice([0, 1, 2]),
            child_seats=random.choice([0, 1]),
            active=True
        )
        vehicles.append(vehicle)
    return vehicles


# ====== BOOKINGS ======
def seed_bookings(customers, cities, service_types):
    bookings = []
    for _ in range(10):
        customer = random.choice(customers)
        city = random.choice(cities)
        service_type = random.choice(service_types)

        pickup_time = datetime.utcnow() + timedelta(days=random.randint(-10, 10))

        booking = Bookings(
            customer_id=customer.id,
            city_id=city.id,
            service_type_id=service_type.id,
            status=random.choice(["pending", "assigned", "completed", "cancelled"]),
            source_channel=random.choice(["web", "phone", "admin"]),
            scheduled_pickup_at=pickup_time,
            avoid_tolls=random.choice([True, False]),
            passengers_count=random.choice([1, 2, 3, 4]),
            luggage_large_count=random.choice([0, 1, 2]),
            luggage_small_count=random.choice([0, 1, 2]),
            child_seats_required=random.choice([0, 0, 1]),
            pets=random.choice([False, True]),
            special_instructions=None,
            estimated_distance_km=round(random.uniform(3, 25), 2),
            estimated_duration_min=random.randint(10, 60),
            price_currency="EUR",
            price_quote_amount=round(random.uniform(15, 80), 2),
            min_base_applied=random.choice([True, False]),
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
            provider=random.choice(["stripe", "paypal", "cash"]),
            status=random.choice(["paid", "pending", "refunded"]),
            amount=round(random.uniform(10, 100), 2),
            currency="EUR",
            transaction_id=None,
            paid_at=None,
            created_at=datetime.utcnow()
        )
        payments.append(payment)
    return payments


# ====== BOOKING CHARGES ======
def seed_booking_charges(bookings):
    charges = []
    for b in bookings:
        quantity = 1
        unit_price = round(random.uniform(10, 30), 2)
        charge = BookingCharges(
            booking_id=b.id,
            code="BASE",
            description="Tarifa base",
            quantity=quantity,
            unit_price=unit_price,
            total_amount=round(quantity * unit_price, 2)
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
