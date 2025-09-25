"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request
from flask_cors import CORS
from sqlalchemy import select, or_, func
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from decimal import Decimal

from api.models import (
    db,
    Users, Customers, Drivers, Vehicles,
    Cities, ServiceTypes,
    Bookings, BookingStops, BookingAssignments, BookingStatusHistory,
    Payments, Invoices, BookingCharges, DriverPayouts,
    PricingProfiles, PricingItems, CapacityLimits,
    CourtesyPolicies, CancellationPolicies, MinNoticePolicies,
    Communications, ContactMessages, Notifications
)

api = Blueprint('api', __name__)
CORS(api)

# =========================
# Helpers
# =========================

def _decimal(v, places=2):
    if v is None:
        return None
    return float(Decimal(v).quantize(Decimal(10) ** -places))

def _now():
    return datetime.utcnow()

def compute_quote_km(distance_km: float, service_code: str, airport_min: bool=False):
    """
    Regla mínima viable basada en lo que nos pasaste.
    - Base 25€ hasta 15km, luego 0.98€/km extra.
    - Mínimos aeropuerto por servicio si airport_min=True:
      * standard=35, executive=50, van=65
    """
    distance_km = float(distance_km or 0)
    base = 25.0
    per_km = 0.98
    extra = 0.0
    if distance_km > 15:
        extra = (distance_km - 15) * per_km
    total = base + extra

    if airport_min:
        mins = {"standard": 35.0, "executive": 50.0, "van": 65.0}
        total = max(total, mins.get(service_code, base))
    return round(total, 2), (distance_km <= 15)

def check_min_notice(city_id: int, when: datetime) -> bool:
    """ True si cumple antelación mínima (default 60 min) """
    policy = db.session.execute(
        select(MinNoticePolicies).where(MinNoticePolicies.city_id == city_id, MinNoticePolicies.active == True)
    ).scalars().first()
    mins = policy.min_notice_min if policy else 60
    return when >= (_now() + timedelta(minutes=mins))

def check_capacity(city_id: int, service_type_id: int, when: datetime) -> bool:
    """
    Verifica número de reservas confirmadas en ventana (default 90 min)
    vs capacidad (ej. 15/5/5).
    """
    cap = db.session.execute(
        select(CapacityLimits).where(
            CapacityLimits.city_id == city_id,
            CapacityLimits.service_type_id == service_type_id
        )
    ).scalars().first()
    if not cap:
        return True  # sin límite configurado
    window = timedelta(minutes=cap.window_minutes or 90)
    start = when - window/2
    end = when + window/2
    count = db.session.execute(
        select(func.count(Bookings.id)).where(
            Bookings.city_id == city_id,
            Bookings.service_type_id == service_type_id,
            Bookings.status.in_(["confirmed", "in_progress"]),
            Bookings.scheduled_pickup_at >= start,
            Bookings.scheduled_pickup_at <= end
        )
    ).scalar_one()
    return count < cap.max_concurrent

def add_status(booking_id: int, to_status: str, user_id: int | None, note: str | None = None, from_status: str | None = None):
    hist = BookingStatusHistory(
        booking_id=booking_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=user_id,
        changed_at=_now(),
        note=note
    )
    db.session.add(hist)

# =========================
# AUTH y Usuarios
# =========================

@api.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    role = data.get("role", "customer")  # admin|editor|driver|customer

    if not email or not password or not confirm_password:
        return jsonify({"error": "Missing email/password/confirm_password"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if db.session.execute(select(Users).where(Users.email == email)).scalar_one_or_none():
        return jsonify({"error": "Email already registered"}), 409

    new_user = Users(
        email=email,
        password=generate_password_hash(password),
        username=data.get("username"),
        firstname=data.get("firstname"),
        lastname=data.get("lastname"),
        phone=data.get("phone"),
        avatar_image=data.get("avatar_image"),
        is_active=True,
        role=role,
        status="active",
        created_at=_now(),
        updated_at=_now()
    )
    db.session.add(new_user)
    db.session.commit()

    # Si es customer/driver, crea perfil asociado
    if role == "customer":
        db.session.add(Customers(user_id=new_user.id, created_at=_now()))
    elif role == "driver":
        db.session.add(Drivers(user_id=new_user.id, hire_date=_now(), active=True))
    db.session.commit()

    return jsonify(new_user.serialize()), 201


@api.route('/signin', methods=['POST'])
def signin():
    data = request.get_json() or {}
    identify = data.get("identify")
    password = data.get("password")

    if not identify or not password:
        return jsonify({"error": "Missing identify/password"}), 400

    user = db.session.execute(
        select(Users).where(or_(Users.email == identify, Users.username == identify))
    ).scalar_one_or_none()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"success": False, "error": "Wrong email/username or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"success": True, "token": token, "user": user.serialize()}), 200


@api.route('/token', methods=['GET'])
@jwt_required()
def check_token():
    user_id = get_jwt_identity()
    user = db.session.get(Users, user_id)
    if not user:
        return jsonify({"success": False}), 401
    return jsonify({"success": True, "user": user.serialize()}), 200


@api.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    uid = get_jwt_identity()
    user = db.session.get(Users, uid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Si es cliente, traemos sus reservas
    bookings_data = {}
    if user.role == "customer":
        customer = db.session.execute(
            select(Customers).where(Customers.user_id == user.id)
        ).scalar_one_or_none()
        if customer:
            now = datetime.utcnow()
            bookings = customer.bookings

            upcoming = [b.serialize() for b in bookings if b.scheduled_pickup_at > now and b.status not in ("completed", "cancelled")]
            past = [b.serialize() for b in bookings if b.scheduled_pickup_at <= now or b.status in ("completed", "cancelled")]

            bookings_data = {
                "upcoming": upcoming,
                "past": past
            }

    profile = user.serialize()
    if bookings_data:
        profile["bookings"] = bookings_data

    return jsonify(profile), 200



@api.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    uid = get_jwt_identity()
    user = db.session.get(Users, uid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}

    # Datos básicos editables
    for f in ("email", "username", "firstname", "lastname", "phone", "avatar_image"):
        if f in data:
            setattr(user, f, data[f])

    # Actualización de contraseña con confirmación
    if data.get("password"):
        if not data.get("confirm_password"):
            return jsonify({"error": "confirm_password required"}), 400
        if data["password"] != data["confirm_password"]:
            return jsonify({"error": "Passwords do not match"}), 400
        user.password = generate_password_hash(data["password"])

    user.updated_at = _now()
    db.session.commit()
    return jsonify(user.serialize()), 200


@api.route('/reset-password', methods=['PUT'])
@jwt_required()
def reset_password():
    """Resetear contraseña desde un token válido"""
    uid = get_jwt_identity()
    user = db.session.get(Users, uid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    new_password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not new_password or not confirm_password:
        return jsonify({"error": "Password and confirm_password are required"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    user.password = generate_password_hash(new_password)
    user.updated_at = _now()
    db.session.commit()

    return jsonify({"success": True, "msg": "Password updated successfully"}), 200


# =========================
# Catálogos: Cities & ServiceTypes
# =========================

@api.route('/cities', methods=['GET'])
def list_cities():
    items = db.session.execute(select(Cities)).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/cities', methods=['POST'])
@jwt_required()
def create_city():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error":"name is required"}), 400
    item = Cities(name=name, active=bool(data.get("active", True)))
    db.session.add(item); db.session.commit()
    return jsonify(item.serialize()), 201

@api.route('/service-types', methods=['GET'])
def list_service_types():
    items = db.session.execute(select(ServiceTypes)).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/service-types', methods=['POST'])
@jwt_required()
def create_service_type():
    data = request.get_json() or {}
    code = data.get("code")
    if not code:
        return jsonify({"error":"code is required"}), 400
    st = ServiceTypes(code=code, display_name=data.get("display_name"), description=data.get("description"))
    db.session.add(st); db.session.commit()
    return jsonify(st.serialize()), 201


# =========================
# Drivers & Vehicles
# =========================

@api.route('/drivers', methods=['GET'])
@jwt_required()
def list_drivers():
    items = db.session.execute(select(Drivers)).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/drivers/<int:id>', methods=['GET'])
@jwt_required()
def get_driver(id):
    d = db.session.get(Drivers, id)
    if not d: return jsonify({"error":"Driver not found"}), 404
    return jsonify(d.serialize()), 200

@api.route('/drivers', methods=['POST'])
@jwt_required()
def create_driver():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error":"user_id is required"}), 400
    drv = Drivers(user_id=user_id, license_number=data.get("license_number"), hire_date=_now(), active=True)
    db.session.add(drv); db.session.commit()
    return jsonify(drv.serialize()), 201

@api.route('/vehicles', methods=['GET'])
@jwt_required()
def list_vehicles():
    items = db.session.execute(select(Vehicles)).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/vehicles', methods=['POST'])
@jwt_required()
def create_vehicle():
    data = request.get_json() or {}
    required = ("driver_id","plate_number","type")
    if not all(k in data for k in required):
        return jsonify({"error":"driver_id, plate_number, type are required"}), 400
    v = Vehicles(
        driver_id=data["driver_id"],
        plate_number=data["plate_number"],
        make=data.get("make"), model=data.get("model"), color=data.get("color"),
        type=data["type"], seats=data.get("seats",4),
        luggage_large=data.get("luggage_large",0), luggage_small=data.get("luggage_small",0),
        child_seats=data.get("child_seats",0), active=bool(data.get("active", True))
    )
    db.session.add(v); db.session.commit()
    return jsonify(v.serialize()), 201


# =========================
# Customers
# =========================

@api.route('/customers', methods=['GET'])
@jwt_required()
def list_customers():
    items = db.session.execute(select(Customers)).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/customers', methods=['POST'])
@jwt_required()
def create_customer():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error":"user_id is required"}), 400
    c = Customers(user_id=user_id, marketing_opt_in=bool(data.get("marketing_opt_in", False)), notes=data.get("notes"), created_at=_now())
    db.session.add(c); db.session.commit()
    return jsonify(c.serialize()), 201


# =========================
# Bookings core
# =========================

@api.route('/bookings', methods=['GET'])
@jwt_required()
def list_bookings():
    q = db.session.execute(select(Bookings).order_by(Bookings.created_at.desc()))
    items = q.scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/bookings/<int:id>', methods=['GET'])
@jwt_required()
def get_booking(id):
    b = db.session.get(Bookings, id)
    if not b: return jsonify({"error":"Booking not found"}), 404
    data = b.serialize()
    data["stops"] = [s.serialize() for s in b.stops]
    data["assignment"] = b.assignment.serialize() if b.assignment else None
    data["charges"] = [c.serialize() for c in b.charges]
    data["payments"] = [p.serialize() for p in b.payments]
    return jsonify(data), 200

@api.route('/bookings/quote', methods=['POST'])
def quote_booking():
    """
    Espera: { service_code, distance_km, airport_min (bool) }
    Devuelve: total y si aplicó min_base_applied.
    """
    data = request.get_json() or {}
    total, min_base = compute_quote_km(
        distance_km=float(data.get("distance_km", 0)),
        service_code=data.get("service_code", "standard"),
        airport_min=bool(data.get("airport_min", False))
    )
    return jsonify({"quote_amount": total, "min_base_applied": min_base}), 200

@api.route('/bookings', methods=['POST'])
def create_booking():
    """
    Crea la reserva (pendiente) y sus paradas.
    Valida antelación mínima y capacidad si trae scheduled_pickup_at.
    """
    data = request.get_json() or {}
    required = ("customer_id","city_id","service_type_id","scheduled_pickup_at","stops")
    if not all(k in data for k in required):
        return jsonify({"error":"customer_id, city_id, service_type_id, scheduled_pickup_at, stops[] required"}), 400

    sched = datetime.fromisoformat(data["scheduled_pickup_at"])
    if not check_min_notice(data["city_id"], sched):
        return jsonify({"error":"Minimum notice not satisfied"}), 422
    if not check_capacity(data["city_id"], data["service_type_id"], sched):
        return jsonify({"error":"Capacity limit reached for that slot"}), 409

    b = Bookings(
        customer_id=data["customer_id"],
        city_id=data["city_id"],
        service_type_id=data["service_type_id"],
        status="pending",
        source_channel=data.get("source_channel","web"),
        scheduled_pickup_at=sched,
        avoid_tolls=bool(data.get("avoid_tolls", True)),
        passengers_count=data.get("passengers_count",1),
        luggage_large_count=data.get("luggage_large_count",0),
        luggage_small_count=data.get("luggage_small_count",0),
        child_seats_required=data.get("child_seats_required",0),
        pets=bool(data.get("pets", False)),
        special_instructions=data.get("special_instructions"),
        estimated_distance_km=data.get("estimated_distance_km"),
        estimated_duration_min=data.get("estimated_duration_min"),
        price_currency=data.get("price_currency","EUR"),
        price_quote_amount=data.get("price_quote_amount"),
        min_base_applied=bool(data.get("min_base_applied", False)),
        created_at=_now(), updated_at=_now(),
    )
    db.session.add(b); db.session.flush()

    # Stops
    for i, st in enumerate(data.get("stops", []), start=1):
        s = BookingStops(
            booking_id=b.id, seq=st.get("seq", i),
            type=st.get("type","stop"),
            address_text=st.get("address_text",""),
            latitude=st.get("latitude"), longitude=st.get("longitude"),
            planned_wait_min=st.get("planned_wait_min",0),
            created_at=_now()
        )
        db.session.add(s)

    add_status(b.id, "pending", data.get("changed_by"), note="Booking created")

    db.session.commit()
    return jsonify(b.serialize()), 201

@api.route('/bookings/<int:id>', methods=['PUT'])
@jwt_required()
def update_booking(id):
    b = db.session.get(Bookings, id)
    if not b: return jsonify({"error":"Booking not found"}), 404
    data = request.get_json() or {}
    # Campos editables básicos
    for f in ("avoid_tolls","passengers_count","luggage_large_count","luggage_small_count","child_seats_required","pets","special_instructions"):
        if f in data:
            setattr(b, f, data[f])
    if "scheduled_pickup_at" in data:
        when = datetime.fromisoformat(data["scheduled_pickup_at"])
        if not check_min_notice(b.city_id, when):
            return jsonify({"error":"Minimum notice not satisfied"}), 422
        if not check_capacity(b.city_id, b.service_type_id, when):
            return jsonify({"error":"Capacity limit reached"}), 409
        b.scheduled_pickup_at = when
    b.updated_at = _now()
    db.session.commit()
    return jsonify(b.serialize()), 200

@api.route('/bookings/<int:id>/stops', methods=['POST'])
@jwt_required()
def add_stop(id):
    b = db.session.get(Bookings, id)
    if not b: return jsonify({"error":"Booking not found"}), 404
    data = request.get_json() or {}
    s = BookingStops(
        booking_id=b.id, seq=data.get("seq", (len(b.stops)+1)),
        type=data.get("type","stop"),
        address_text=data.get("address_text",""),
        latitude=data.get("latitude"), longitude=data.get("longitude"),
        planned_wait_min=data.get("planned_wait_min",0),
        created_at=_now()
    )
    db.session.add(s); db.session.commit()
    return jsonify(s.serialize()), 201

@api.route('/bookings/<int:id>/assign', methods=['POST'])
@jwt_required()
def assign_booking(id):
    b = db.session.get(Bookings, id)
    if not b: return jsonify({"error":"Booking not found"}), 404
    data = request.get_json() or {}
    driver_id = data.get("driver_id"); vehicle_id = data.get("vehicle_id"); admin_id = get_jwt_identity()
    if not all([driver_id, vehicle_id]):
        return jsonify({"error":"driver_id and vehicle_id required"}), 400
    # 1:1 driver<->vehicle ya garantizado por modelo. Creamos/actualizamos asignación:
    if b.assignment:
        b.assignment.driver_id = driver_id
        b.assignment.vehicle_id = vehicle_id
        b.assignment.assigned_by_admin = admin_id
        b.assignment.assigned_at = _now()
    else:
        a = BookingAssignments(
            booking_id=b.id, driver_id=driver_id, vehicle_id=vehicle_id,
            assigned_by_admin=admin_id, assigned_at=_now()
        )
        db.session.add(a)
    # cambia estado a confirmed si estaba pending
    prev = b.status
    if b.status == "pending":
        b.status = "confirmed"
        add_status(b.id, "confirmed", admin_id, note="Vehicle assigned", from_status=prev)
    db.session.commit()
    return jsonify({"ok": True, "booking": b.serialize()}), 200

@api.route('/bookings/<int:id>/status', methods=['POST'])
@jwt_required()
def change_status(id):
    b = db.session.get(Bookings, id)
    if not b: return jsonify({"error":"Booking not found"}), 404
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in ["pending","confirmed","in_progress","completed","cancelled","no_show"]:
        return jsonify({"error":"invalid status"}), 400
    prev = b.status
    b.status = new_status
    add_status(b.id, new_status, get_jwt_identity(), note=data.get("note"), from_status=prev)
    db.session.commit()
    return jsonify(b.serialize()), 200

@api.route('/bookings/<int:id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(id):
    b = db.session.get(Bookings, id)
    if not b: return jsonify({"error":"Booking not found"}), 404
    data = request.get_json() or {}
    # Política: gratis si >= 12h antes (o lo definido)
    pol = db.session.execute(select(CancellationPolicies).where(CancellationPolicies.active == True)).scalars().first()
    free_hours = pol.free_before_hours if pol else 12
    late_fee = float(pol.late_fee_amount) if pol else 7.5
    diff = (b.scheduled_pickup_at - _now()) if b.scheduled_pickup_at else timedelta(hours=0)
    fee = 0.0
    if diff < timedelta(hours=free_hours):
        fee = late_fee
        db.session.add(BookingCharges(
            booking_id=b.id, code="CANCEL_LATE_FEE",
            description=f"Late cancel (<{free_hours}h)",
            quantity=1, unit_price=fee, total_amount=fee, calculated_at=_now()
        ))
    prev = b.status
    b.status = "cancelled"
    add_status(b.id, "cancelled", get_jwt_identity(), note=data.get("note","customer/admin cancel"), from_status=prev)
    db.session.commit()
    return jsonify({"cancel_fee": fee, "currency": "EUR", "booking": b.serialize()}), 200


# =========================
# Payments / Invoices / Charges
# =========================

@api.route('/bookings/<int:id>/charges', methods=['GET'])
@jwt_required()
def list_charges(id):
    items = db.session.execute(select(BookingCharges).where(BookingCharges.booking_id == id)).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/bookings/<int:id>/charges', methods=['POST'])
@jwt_required()
def add_charge(id):
    data = request.get_json() or {}
    code = data.get("code")
    if not code:
        return jsonify({"error":"code required"}), 400
    qty = Decimal(str(data.get("quantity", 1)))
    unit = Decimal(str(data.get("unit_price", 0)))
    ch = BookingCharges(
        booking_id=id, code=code, description=data.get("description"),
        quantity=qty, unit_price=unit, total_amount=qty*unit, calculated_at=_now()
    )
    db.session.add(ch); db.session.commit()
    return jsonify(ch.serialize()), 201

@api.route('/bookings/<int:id>/payments', methods=['POST'])
@jwt_required()
def create_payment(id):
    data = request.get_json() or {}
    amount = Decimal(str(data.get("amount", 0)))
    p = Payments(
        booking_id=id, provider=data.get("provider","manual"),
        status=data.get("status","created"),
        amount=amount, currency=data.get("currency","EUR"),
        transaction_id=data.get("transaction_id"),
        paid_at=datetime.fromisoformat(data["paid_at"]) if data.get("paid_at") else None,
        created_at=_now()
    )
    db.session.add(p); db.session.commit()
    return jsonify(p.serialize()), 201

@api.route('/bookings/<int:id>/invoice', methods=['POST'])
@jwt_required()
def create_invoice(id):
    data = request.get_json() or {}
    inv = Invoices(
        booking_id=id, number=data.get("number"),
        issue_date=_now(), due_date=data.get("due_date") and datetime.fromisoformat(data["due_date"]),
        subtotal=Decimal(str(data.get("subtotal", 0))), taxes=Decimal(str(data.get("taxes", 0))),
        total=Decimal(str(data.get("total", 0))), pdf_url=data.get("pdf_url")
    )
    db.session.add(inv); db.session.commit()
    return jsonify(inv.serialize()), 201


# =========================
# Pricing & Policies
# =========================

@api.route('/pricing/profiles', methods=['GET'])
@jwt_required()
def pricing_profiles():
    items = db.session.execute(select(PricingProfiles)).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/pricing/profiles', methods=['POST'])
@jwt_required()
def create_pricing_profile():
    d = request.get_json() or {}
    p = PricingProfiles(
        name=d.get("name","Default"),
        city_id=d.get("city_id"), service_type_id=d.get("service_type_id"),
        active=bool(d.get("active", True)),
        effective_from=d.get("effective_from") and datetime.fromisoformat(d["effective_from"]),
        effective_to=d.get("effective_to") and datetime.fromisoformat(d["effective_to"]),
    )
    db.session.add(p); db.session.commit()
    return jsonify(p.serialize()), 201

@api.route('/pricing/items', methods=['POST'])
@jwt_required()
def create_pricing_item():
    d = request.get_json() or {}
    if not d.get("profile_id") or not d.get("code") or not d.get("calc_type"):
        return jsonify({"error":"profile_id, code, calc_type required"}), 400
    it = PricingItems(
        profile_id=d["profile_id"], code=d["code"], description=d.get("description"),
        calc_type=d["calc_type"], threshold_km=d.get("threshold_km"),
        amount=d.get("amount", 0), min_amount=d.get("min_amount"), airport_only=bool(d.get("airport_only", False))
    )
    db.session.add(it); db.session.commit()
    return jsonify(it.serialize()), 201

@api.route('/capacity', methods=['POST'])
@jwt_required()
def set_capacity():
    d = request.get_json() or {}
    cap = CapacityLimits(
        city_id=d["city_id"], service_type_id=d["service_type_id"],
        max_concurrent=d.get("max_concurrent", 10), window_minutes=d.get("window_minutes", 90)
    )
    db.session.add(cap); db.session.commit()
    return jsonify({"ok": True}), 201

@api.route('/policies/courtesy', methods=['POST'])
@jwt_required()
def set_courtesy():
    d = request.get_json() or {}
    pol = CourtesyPolicies(
        city_id=d["city_id"], context=d.get("context","general"),
        free_minutes=d.get("free_minutes", 25),
        noshow_charge_code=d.get("noshow_charge_code","BASE_MIN")
    )
    db.session.add(pol); db.session.commit()
    return jsonify({"ok": True}), 201

@api.route('/policies/cancellation', methods=['POST'])
@jwt_required()
def set_cancellation():
    d = request.get_json() or {}
    pol = CancellationPolicies(
        free_before_hours=d.get("free_before_hours", 12),
        late_fee_amount=d.get("late_fee_amount", 7.5),
        currency=d.get("currency","EUR"),
        active=bool(d.get("active", True))
    )
    db.session.add(pol); db.session.commit()
    return jsonify({"ok": True}), 201

@api.route('/policies/min-notice', methods=['POST'])
@jwt_required()
def set_min_notice():
    d = request.get_json() or {}
    pol = MinNoticePolicies(
        city_id=d["city_id"],
        min_notice_min=d.get("min_notice_min", 60),
        active=bool(d.get("active", True))
    )
    db.session.add(pol); db.session.commit()
    return jsonify({"ok": True}), 201


# =========================
# Comunicaciones / Contacto / Notifs
# =========================

@api.route('/contact', methods=['POST'])
def contact_message():
    d = request.get_json() or {}
    if not d.get("name") or not d.get("email") or not d.get("message"):
        return jsonify({"error":"name, email, message required"}), 400
    c = ContactMessages(name=d["name"], email=d["email"], phone=d.get("phone"), message=d["message"], created_at=_now())
    db.session.add(c); db.session.commit()
    return jsonify(c.serialize()), 201

@api.route('/communications', methods=['POST'])
@jwt_required()
def create_comm():
    d = request.get_json() or {}
    m = Communications(
        booking_id=d.get("booking_id"),
        channel=d.get("channel","email"), direction=d.get("direction","outbound"),
        to_user_id=d.get("to_user_id"), from_user_id=get_jwt_identity(),
        to_address=d.get("to_address"), from_address=d.get("from_address"),
        subject=d.get("subject"), message=d.get("message"),
        sent_at=_now()
    )
    db.session.add(m); db.session.commit()
    return jsonify(m.serialize()), 201

@api.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    uid = get_jwt_identity()
    items = db.session.execute(select(Notifications).where(Notifications.user_id == uid).order_by(Notifications.created_at.desc())).scalars().all()
    return jsonify([i.serialize() for i in items]), 200

@api.route('/notifications/<int:id>/read', methods=['POST'])
@jwt_required()
def read_notification(id):
    n = db.session.get(Notifications, id)
    if not n: return jsonify({"error":"Not found"}), 404
    n.read_at = _now()
    db.session.commit()
    return jsonify(n.serialize()), 200


# =========================
# Dashboards sencillos
# =========================

@api.route('/dashboard/customer/<int:user_id>', methods=['GET'])
@jwt_required()
def dashboard_customer(user_id):
    cust = db.session.execute(select(Customers).where(Customers.user_id == user_id)).scalars().first()
    if not cust: return jsonify({"error":"Customer profile not found"}), 404
    bookings = db.session.execute(select(Bookings).where(Bookings.customer_id == cust.id).order_by(Bookings.created_at.desc())).scalars().all()
    return jsonify([b.serialize() for b in bookings]), 200

@api.route('/dashboard/driver/<int:user_id>', methods=['GET'])
@jwt_required()
def dashboard_driver(user_id):
    drv = db.session.execute(select(Drivers).where(Drivers.user_id == user_id)).scalars().first()
    if not drv: return jsonify({"error":"Driver profile not found"}), 404
    # viajes asignados + métricas simples
    assigns = db.session.execute(select(BookingAssignments).where(BookingAssignments.driver_id == drv.id)).scalars().all()
    data = []
    for a in assigns:
        b = db.session.get(Bookings, a.booking_id)
        if b:
            row = b.serialize()
            row["assigned_at"] = a.assigned_at.isoformat()
            data.append(row)
    # históricos y payout
    payouts = db.session.execute(select(DriverPayouts).where(DriverPayouts.driver_id == drv.id)).scalars().all()
    return jsonify({"trips": data, "payouts": [p.serialize() for p in payouts]}), 200
