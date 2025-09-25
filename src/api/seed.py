import sys
import os

# Agrega el directorio 'src' al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from api.models import db
from .seed_data import (
    seed_users,
    seed_customers,
    seed_drivers,
    seed_vehicles,
    seed_master_data,
    seed_bookings,
    seed_payments,
    seed_booking_charges
)

with app.app_context():
    # ⚠️ En desarrollo: reset completo de la DB
    db.drop_all()
    db.create_all()

    # 1. Users
    users = seed_users()
    db.session.add_all(users)
    db.session.commit()

    # 2. Customers
    customers = seed_customers(users)
    db.session.add_all(customers)
    db.session.commit()

    # 3. Drivers
    drivers = seed_drivers(users)
    db.session.add_all(drivers)
    db.session.commit()

    # 4. Vehicles
    vehicles = seed_vehicles(drivers)
    db.session.add_all(vehicles)
    db.session.commit()

    # 5. Catálogos (Ciudades y Tipos de Servicio)
    cities, service_types = seed_master_data()
    db.session.add_all(cities + service_types)
    db.session.commit()

    # 6. Bookings
    bookings = seed_bookings(customers, cities, service_types)
    db.session.add_all(bookings)
    db.session.commit()

    # 7. Payments
    payments = seed_payments(bookings)
    db.session.add_all(payments)
    db.session.commit()

    # 8. Booking Charges
    charges = seed_booking_charges(bookings)
    db.session.add_all(charges)
    db.session.commit()

    print("✅ Datos de prueba de DriverSpain generados exitosamente.")
