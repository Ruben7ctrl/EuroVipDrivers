
import os
from flask_admin import Admin
from .models import (
    db, 
    Users, Customers, Drivers, Vehicles, 
    Bookings, Payments, BookingCharges
)
from flask_admin.contrib.sqla import ModelView


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='DriverSpain Admin', template_mode='bootstrap3')

    # ======================
    # Modelos principales
    # ======================
    admin.add_view(ModelView(Users, db.session))
    admin.add_view(ModelView(Customers, db.session))
    admin.add_view(ModelView(Drivers, db.session))
    admin.add_view(ModelView(Vehicles, db.session))
    admin.add_view(ModelView(Bookings, db.session))
    admin.add_view(ModelView(Payments, db.session))
    admin.add_view(ModelView(BookingCharges, db.session))

    # Aquí puedes añadir cualquier modelo nuevo en el futuro
    # admin.add_view(ModelView(YourModelName, db.session))
