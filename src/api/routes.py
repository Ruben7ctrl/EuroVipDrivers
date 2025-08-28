"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from sqlalchemy import select
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from api.mail.mailer import send_mail
from flask import current_app
from datetime import datetime
import os

import stripe

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)


@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }

    return jsonify(response_body), 200

# @api.route('/register', methods=['POST'])
# def register():
#     try:
#         data = request.json

#         if not data['email'] or not data['password'] or not data['confirmPassword']:
#             raise Exception({"error": 'missind data'})
#         if  data['password'] != data['confirmPassword']:
#             raise Exception({"error": 'passwords do not match'})
#         stm = select(User).where(User.email == data['email'])
#         existing_user = db.session.execute(stm).scalar_one_or_none()
#         if existing_user:
#             raise Exception({"error": 'email taken, try to login'})
#         new_user = User(
#             email = data['email'],
#             password = data['password'],
#             confirmPassword = data['confirmPassword'],
#             is_active = True
#         )
#         db.session.add(new_user)
#         db.session.commit()
#         return jsonify(new_user.serialize()),201


#     except Exception as e:
#         print(e)
#         db.session.rollback()
#         return jsonify({"error": "something went wrong"}),400



@api.route('/register', methods=['POST'])
def register():
    try:
        data = request.json

        # Validar que los campos requeridos estén presentes
        if not data.get('email') or not data.get('password') or not data.get('confirmPassword'):
            return jsonify({"error": "Missing data"}), 400

        # Validar que las contraseñas coincidan
        if data['password'] != data['confirmPassword']:
            return jsonify({"error": "Passwords do not match"}), 400

        # Verificar si el usuario ya existe
        stm = select(User).where(User.email == data['email'])
        existing_user = db.session.execute(stm).scalar_one_or_none()
        if existing_user:
            return jsonify({"error": "Email already taken, try to login"}), 400

        # Crear un nuevo usuario con la contraseña hasheada
        new_user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),  # Hashear la contraseña
            is_active=True
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify(new_user.serialize()), 201

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        return jsonify({"error": "Something went wrong"}), 500
    
    
@api.route('/users', methods=['GET'])
def get_users():

    stmt = select(User)
    users = db.session.execute(stmt).scalars().all()
    return jsonify([user.serialize() for user in users]), 200


@api.route('/users/<int:id>', methods=['GET'])
def get_oneUser(id):

    stmt = select(User).where(User.id == id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({"error": "User not found"}), 400

    return jsonify(user.serialize()), 200


@api.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()

        if not data["email"] or not data["password"]:
            raise Exception({"error": "Missing Data"})

        stmt = select(User).where(User.email == data["email"])
        existing_user = db.session.execute(stmt).scalar_one_or_none()

        if existing_user:
            raise Exception({"error": "Existing email, try to SignIn"})

        hashed_password = generate_password_hash(data["password"])

        new_user = User(
            email=data["email"],
            password=hashed_password,
            name=data.get("name"),
            is_active=True
        )

        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.serialize()), 201

    except Exception as e:
        print(e)

        db.session.rollback()
        return jsonify({"error": "somthing went wrong"}), 400


@api.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.get_json()

        if not data.get("password") or not data.get("identify"):
            return jsonify({"error": "missing data"})

        stmt = select(User).where(
            or_(User.email == data["identify"], Users.username == data["identify"]))
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user:
            raise Exception({"error": "Email/Username not found"})

        if not check_password_hash(user.password, data["password"]):
            return jsonify({"success": False, "error": "wrong email/password"})

        token = create_access_token(identity=str(user.id))

        return jsonify({"success": True, "token": token, "msg": "SignIn OK", "user": user.serialize()}), 201

    except Exception as e:
        print(e)

        db.session.rollback()
        return jsonify({"error": "somthing went wrong"}), 400