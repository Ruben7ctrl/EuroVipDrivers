"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from sqlalchemy import select

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)


@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }

    return jsonify(response_body), 200

@api.route('/register', methods=['POST'])
def register():
    try:
        data = request.json

        if not data['email'] or not data['password'] or not data['confirmPassword']:
            raise Exception({"error": 'missind data'})
        if  data['password'] != data['confirmPassword']:
            raise Exception({"error": 'passwords do not match'})
        stm = select(User).where(User.email == data['email'])
        existing_user = db.session.execute(stm).scalar_one_or_none()
        if existing_user:
            raise Exception({"error": 'email taken, try to login'})
        new_user = User(
            email = data['email'],
            password = data['password'],
            confirmPassword = data['confirmPassword'],
            is_active = True
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.serialize()),201


    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": "something went wrong"}),400