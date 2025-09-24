# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import String, Boolean, JSON, DateTime, Enum, ForeignKey
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from datetime import datetime
# from typing import Optional, List

# db = SQLAlchemy()

# class User(db.Model):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String(255), nullable=False)
#     email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
#     role: Mapped[str] = mapped_column(String(200), nullable=False) # Client, Driver, Admin
#     password: Mapped[str] = mapped_column(nullable=False)
#     is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)


#     def serialize(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "email": self.email,
#             "role": self.role,
#             "is_active": self.is_active,
#             # do not serialize the password, it's a security breach
#         }


# class Ride(db.Model):
#     __tablename__ = 'rides'
#     STATUS_ACTIVE = 'active'
#     STATUS_DONE = 'done'
#     STATUS_CANCELED = 'canceled'
#     STATUS_CREATED = 'created'

#     id: Mapped[int] = mapped_column(primary_key=True)
#     pickup: Mapped[dict] = mapped_column(JSON, nullable=True)
#     destination: Mapped[dict] = mapped_column(JSON, nullable=True)
#     parada: Mapped[dict] = mapped_column(JSON, nullable=True)
#     status_value: Mapped[str] = mapped_column(Enum(STATUS_ACTIVE, STATUS_DONE, STATUS_CANCELED, STATUS_CREATED), default=STATUS_CREATED)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

#     driver_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'), nullable=True)
#     customer_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)

#     # Relationships
#     driver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[driver_id])
#     customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id])

#     def serialize(self):
#         return {
#             "id": self.id,
#             "pickup": self.pickup,
#             "destination": self.destination,
#             "parada": self.parada,
#             "status": self.status_value,
#             "status_translation": self.get_ride_status_translation(self.status_value),
#             "created_at": self.created_at.isoformat(),
#             "driver": self.driver.serialize() if self.driver else None,
#             "customer": self.customer.serialize() if self.customer else None
#         }

#     @staticmethod
#     def get_ride_status_translation(status: str) -> str:
#         return {
#             Ride.STATUS_ACTIVE: "activo",
#             Ride.STATUS_DONE: "completado",
#             Ride.STATUS_CANCELED: "cancelado",
#             Ride.STATUS_CREATED: "creado",
#         }.get(status, status)


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional

db = SQLAlchemy()

# =========================
# USUARIOS / PERSONAS
# =========================

class Users(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Valores esperados: admin | editor | driver | customer
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="customer")
    # Valores esperados: active | suspended | deleted
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(350), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    firstname: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    lastname: Mapped[Optional[str]] = mapped_column(String(90), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    avatar_image: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    # Relaciones
    customer_profile: Mapped[Optional["Customers"]] = relationship(back_populates="user", uselist=False)
    driver_profile: Mapped[Optional["Drivers"]] = relationship(back_populates="user", uselist=False)

    notifications: Mapped[List["Notifications"]] = relationship(back_populates="user")
    communications_out: Mapped[List["Communications"]] = relationship(
        "Communications", back_populates="from_user", foreign_keys=lambda: [Communications.from_user_id]
    )
    communications_in: Mapped[List["Communications"]] = relationship(
        "Communications", back_populates="to_user", foreign_keys=lambda: [Communications.to_user_id]
    )

    def serialize(self):
        return {
            "id": self.id,
            "role": self.role,
            "status": self.status,
            "email": self.email,
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "phone": self.phone,
            "avatar_image": self.avatar_image,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Customers(db.Model):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean(), default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    user: Mapped["Users"] = relationship(back_populates="customer_profile")
    bookings: Mapped[List["Bookings"]] = relationship(back_populates="customer")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "marketing_opt_in": self.marketing_opt_in,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class Drivers(db.Model):
    __tablename__ = "drivers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    hire_date: Mapped[Optional[datetime]] = mapped_column(DateTime(), default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    user: Mapped["Users"] = relationship(back_populates="driver_profile")
    vehicle: Mapped[Optional["Vehicles"]] = relationship(back_populates="driver", uselist=False)
    assignments: Mapped[List["BookingAssignments"]] = relationship(back_populates="driver")
    payouts: Mapped[List["DriverPayouts"]] = relationship(back_populates="driver")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "license_number": self.license_number,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "active": self.active,
        }


class Vehicles(db.Model):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), unique=True, nullable=False)  # 1:1
    plate_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    make: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    color: Mapped[Optional[str]] = mapped_column(String(50))
    # standard | executive | van | minibus
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    seats: Mapped[int] = mapped_column(Integer, default=4)
    luggage_large: Mapped[int] = mapped_column(Integer, default=0)
    luggage_small: Mapped[int] = mapped_column(Integer, default=0)
    child_seats: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    driver: Mapped["Drivers"] = relationship(back_populates="vehicle")
    assignments: Mapped[List["BookingAssignments"]] = relationship(back_populates="vehicle")

    def serialize(self):
        return {
            "id": self.id,
            "driver_id": self.driver_id,
            "plate_number": self.plate_number,
            "make": self.make,
            "model": self.model,
            "color": self.color,
            "type": self.type,
            "seats": self.seats,
            "luggage_large": self.luggage_large,
            "luggage_small": self.luggage_small,
            "child_seats": self.child_seats,
            "active": self.active,
        }


# =========================
# CATÁLOGOS
# =========================

class Cities(db.Model):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    def serialize(self):
        return {"id": self.id, "name": self.name, "active": self.active}


class ServiceTypes(db.Model):
    __tablename__ = "service_types"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # standard | executive | van | minibus
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    def serialize(self):
        return {"id": self.id, "code": self.code, "display_name": self.display_name}


# =========================
# RESERVAS
# =========================

class Bookings(db.Model):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    service_type_id: Mapped[int] = mapped_column(ForeignKey("service_types.id"), nullable=False)

    # pending | confirmed | in_progress | completed | cancelled | no_show
    status: Mapped[str] = mapped_column(String(30), default="pending")
    source_channel: Mapped[str] = mapped_column(String(20), default="web")  # web | whatsapp | email

    scheduled_pickup_at: Mapped[Optional[datetime]] = mapped_column(DateTime())
    avoid_tolls: Mapped[bool] = mapped_column(Boolean(), default=True)
    passengers_count: Mapped[int] = mapped_column(Integer, default=1)
    luggage_large_count: Mapped[int] = mapped_column(Integer, default=0)
    luggage_small_count: Mapped[int] = mapped_column(Integer, default=0)
    child_seats_required: Mapped[int] = mapped_column(Integer, default=0)
    pets: Mapped[bool] = mapped_column(Boolean(), default=False)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)

    estimated_distance_km: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    estimated_duration_min: Mapped[Optional[int]] = mapped_column(Integer)

    price_currency: Mapped[str] = mapped_column(String(3), default="EUR")
    price_quote_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    min_base_applied: Mapped[bool] = mapped_column(Boolean(), default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    # Relaciones
    customer: Mapped["Customers"] = relationship(back_populates="bookings")
    city: Mapped["Cities"] = relationship()
    service_type: Mapped["ServiceTypes"] = relationship()

    stops: Mapped[List["BookingStops"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    assignment: Mapped[Optional["BookingAssignments"]] = relationship(back_populates="booking", uselist=False)
    status_history: Mapped[List["BookingStatusHistory"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    payments: Mapped[List["Payments"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    invoice: Mapped[Optional["Invoices"]] = relationship(back_populates="booking", uselist=False)
    charges: Mapped[List["BookingCharges"]] = relationship(back_populates="booking", cascade="all, delete-orphan")

    def serialize(self):
        return {
            "id": self.id,
            "status": self.status,
            "source_channel": self.source_channel,
            "customer_id": self.customer_id,
            "city_id": self.city_id,
            "service_type_id": self.service_type_id,
            "scheduled_pickup_at": self.scheduled_pickup_at.isoformat() if self.scheduled_pickup_at else None,
            "passengers_count": self.passengers_count,
            "luggage_large_count": self.luggage_large_count,
            "luggage_small_count": self.luggage_small_count,
            "child_seats_required": self.child_seats_required,
            "pets": self.pets,
            "price_currency": self.price_currency,
            "price_quote_amount": float(self.price_quote_amount) if self.price_quote_amount is not None else None,
            "created_at": self.created_at.isoformat(),
        }


class BookingStops(db.Model):
    __tablename__ = "booking_stops"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)

    seq: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..N
    # pickup | stop | dropoff
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    address_text: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    planned_wait_min: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    booking: Mapped["Bookings"] = relationship(back_populates="stops")

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "seq": self.seq,
            "type": self.type,
            "address_text": self.address_text,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "planned_wait_min": self.planned_wait_min,
        }


class BookingAssignments(db.Model):
    __tablename__ = "booking_assignments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    assigned_by_admin: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    booking: Mapped["Bookings"] = relationship(back_populates="assignment")
    driver: Mapped["Drivers"] = relationship(back_populates="assignments")
    vehicle: Mapped["Vehicles"] = relationship(back_populates="assignments")
    admin: Mapped["Users"] = relationship()

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "driver_id": self.driver_id,
            "vehicle_id": self.vehicle_id,
            "assigned_by_admin": self.assigned_by_admin,
            "assigned_at": self.assigned_at.isoformat(),
        }


class BookingStatusHistory(db.Model):
    __tablename__ = "booking_status_history"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    note: Mapped[Optional[str]] = mapped_column(Text)

    booking: Mapped["Bookings"] = relationship(back_populates="status_history")
    user: Mapped[Optional["Users"]] = relationship()

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat(),
            "note": self.note,
        }


# =========================
# PAGOS / FACTURACIÓN
# =========================

class Payments(db.Model):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # paypal | redsys | crypto
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")  # created|captured|refunded|failed
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime())
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    booking: Mapped["Bookings"] = relationship(back_populates="payments")

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "provider": self.provider,
            "status": self.status,
            "amount": float(self.amount),
            "currency": self.currency,
            "transaction_id": self.transaction_id,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }


class Invoices(db.Model):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    issue_date: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime())
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    taxes: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)

    booking: Mapped["Bookings"] = relationship(back_populates="invoice")

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "number": self.number,
            "issue_date": self.issue_date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "subtotal": float(self.subtotal),
            "taxes": float(self.taxes),
            "total": float(self.total),
            "pdf_url": self.pdf_url,
        }


class BookingCharges(db.Model):
    __tablename__ = "booking_charges"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # BASE_25, PER_KM_0_98, WAIT_PER_MIN_0_28, CLEANING_120, etc.
    description: Mapped[Optional[str]] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    booking: Mapped["Bookings"] = relationship(back_populates="charges")

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "code": self.code,
            "description": self.description,
            "quantity": float(self.quantity),
            "unit_price": float(self.unit_price),
            "total_amount": float(self.total_amount),
            "calculated_at": self.calculated_at.isoformat(),
        }


class DriverPayouts(db.Model):
    __tablename__ = "driver_payouts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | paid | rejected
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime())
    notes: Mapped[Optional[str]] = mapped_column(Text)

    driver: Mapped["Drivers"] = relationship(back_populates="payouts")

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "driver_id": self.driver_id,
            "amount": float(self.amount),
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "notes": self.notes,
        }


# =========================
# POLÍTICAS / CAPACIDAD (mínimo viable)
# =========================

class PricingProfiles(db.Model):
    __tablename__ = "pricing_profiles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    service_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("service_types.id"))
    active: Mapped[bool] = mapped_column(Boolean(), default=True)
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime())
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime())

    items: Mapped[List["PricingItems"]] = relationship(back_populates="profile")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "city_id": self.city_id,
            "service_type_id": self.service_type_id,
            "active": self.active,
        }


class PricingItems(db.Model):
    __tablename__ = "pricing_items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("pricing_profiles.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # PER_KM_0_98, BASE_25_UPTO_15KM, etc.
    description: Mapped[Optional[str]] = mapped_column(Text)
    calc_type: Mapped[str] = mapped_column(String(20), nullable=False)  # flat | per_km | per_min | threshold
    threshold_km: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    amount: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    min_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    airport_only: Mapped[bool] = mapped_column(Boolean(), default=False)

    profile: Mapped["PricingProfiles"] = relationship(back_populates="items")

    def serialize(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "code": self.code,
            "calc_type": self.calc_type,
            "threshold_km": float(self.threshold_km) if self.threshold_km is not None else None,
            "amount": float(self.amount),
            "min_amount": float(self.min_amount) if self.min_amount is not None else None,
            "airport_only": self.airport_only,
        }


class CapacityLimits(db.Model):
    __tablename__ = "capacity_limits"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    service_type_id: Mapped[int] = mapped_column(ForeignKey("service_types.id"), nullable=False)
    max_concurrent: Mapped[int] = mapped_column(Integer, nullable=False)  # p.ej. 15 / 5 / 5
    window_minutes: Mapped[int] = mapped_column(Integer, default=90)

    def serialize(self):
        return {
            "id": self.id,
            "city_id": self.city_id,
            "service_type_id": self.service_type_id,
            "max_concurrent": self.max_concurrent,
            "window_minutes": self.window_minutes,
        }


class CourtesyPolicies(db.Model):
    __tablename__ = "courtesy_policies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    context: Mapped[str] = mapped_column(String(50), nullable=False)  # train | bus | airport | airport_t4 | general
    free_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    noshow_charge_code: Mapped[Optional[str]] = mapped_column(String(50))

    def serialize(self):
        return {
            "id": self.id,
            "city_id": self.city_id,
            "context": self.context,
            "free_minutes": self.free_minutes,
            "noshow_charge_code": self.noshow_charge_code,
        }


class CancellationPolicies(db.Model):
    __tablename__ = "cancellation_policies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    free_before_hours: Mapped[int] = mapped_column(Integer, default=12)
    late_fee_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=7.50)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    def serialize(self):
        return {
            "id": self.id,
            "free_before_hours": self.free_before_hours,
            "late_fee_amount": float(self.late_fee_amount),
            "currency": self.currency,
            "active": self.active,
        }


class MinNoticePolicies(db.Model):
    __tablename__ = "min_notice_policies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    min_notice_min: Mapped[int] = mapped_column(Integer, default=60)
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    def serialize(self):
        return {
            "id": self.id,
            "city_id": self.city_id,
            "min_notice_min": self.min_notice_min,
            "active": self.active,
        }


# =========================
# COMUNICACIONES / SOPORTE
# =========================

class Communications(db.Model):
    __tablename__ = "communications"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    booking_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bookings.id"))
    channel: Mapped[str] = mapped_column(String(20), default="email")         # email | whatsapp | web
    direction: Mapped[str] = mapped_column(String(20), default="outbound")    # inbound | outbound

    to_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    from_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    to_address: Mapped[Optional[str]] = mapped_column(String(255))
    from_address: Mapped[Optional[str]] = mapped_column(String(255))
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    booking: Mapped[Optional["Bookings"]] = relationship()
    to_user: Mapped[Optional["Users"]] = relationship(foreign_keys=[to_user_id], back_populates="communications_in")
    from_user: Mapped[Optional["Users"]] = relationship(foreign_keys=[from_user_id], back_populates="communications_out")

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "channel": self.channel,
            "direction": self.direction,
            "to_user_id": self.to_user_id,
            "from_user_id": self.from_user_id,
            "to_address": self.to_address,
            "from_address": self.from_address,
            "subject": self.subject,
            "message": self.message,
            "sent_at": self.sent_at.isoformat(),
        }


class ContactMessages(db.Model):
    __tablename__ = "contact_messages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }


class Notifications(db.Model):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(50))
    payload: Mapped[Optional[str]] = mapped_column(Text)  # puedes usar JSON como string
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime())
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    user: Mapped["Users"] = relationship(back_populates="notifications")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "payload": self.payload,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat(),
        }
 