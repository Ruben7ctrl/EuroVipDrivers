from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False) # Client, Driver, Admin
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)


    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            # do not serialize the password, it's a security breach
        }


class Ride(db.Model):
    __tablename__ = 'rides'
    STATUS_ACTIVE = 'active'
    STATUS_DONE = 'done'
    STATUS_CANCELED = 'canceled'
    STATUS_CREATED = 'created'

    id: Mapped[int] = mapped_column(primary_key=True)
    pickup: Mapped[dict] = mapped_column(JSON, nullable=True)
    destination: Mapped[dict] = mapped_column(JSON, nullable=True)
    parada: Mapped[dict] = mapped_column(JSON, nullable=True)
    status_value: Mapped[str] = mapped_column(Enum(STATUS_ACTIVE, STATUS_DONE, STATUS_CANCELED, STATUS_CREATED), default=STATUS_CREATED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    city_id: Mapped[int] = mapped_column(ForeignKey('cities.id'), nullable=False)
    driver_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    status_id: Mapped[Optional[int]] = mapped_column(ForeignKey('ride_statuses.id'), nullable=True)
    service_requested_id: Mapped[Optional[int]] = mapped_column(ForeignKey('vehicle_categories.id'), nullable=True)

    city: Mapped["City"] = relationship("City", back_populates="rides")
    driver: Mapped["User"] = relationship("User", foreign_keys=[driver_id], back_populates="rides_as_driver")
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id], back_populates="rides_as_customer")
    status: Mapped["RideStatus"] = relationship("RideStatus", back_populates="rides")
    extras: Mapped[List["RideExtra"]] = relationship("RideExtra", secondary=ride_extras_pivot)
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="ride")

    def serialize(self):
        return {
            "id": self.id,
            "pickup": self.pickup,
            "destination": self.destination,
            "parada": self.parada,
            "status": self.status_value,
            "status_translation": self.get_ride_status_translation(self.status_value),
            "created_at": self.created_at.isoformat(),
            "city": self.city.serialize() if self.city else None,
            "driver": self.driver.serialize() if self.driver else None,
            "customer": self.customer.serialize() if self.customer else None,
            "extras": [extra.serialize() for extra in self.extras]
        }

    @staticmethod
    def get_ride_status_translation(status: str) -> str:
        return {
            Ride.STATUS_ACTIVE: "activo",
            Ride.STATUS_DONE: "completado",
            Ride.STATUS_CANCELED: "cancelado",
            Ride.STATUS_CREATED: "creado",
        }.get(status, status)

