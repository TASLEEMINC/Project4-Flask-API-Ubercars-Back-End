from auth_middleware import token_required
import bcrypt
import jwt
import psycopg2, psycopg2.extras
from dotenv import load_dotenv
import os
from flask import Flask, jsonify, request, g
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)
def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        database='ubercars_db',
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD']
    )
    return connection

@app.route('/')
def index():
  return "Hello, world!"

@app.route('/ubercars')
def ubercars_index():
  try:
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM ubercars;")
    ubercars = cursor.fetchall()
    connection.close()
    return ubercars
  except:
    return "Application Error", 500

@app.route('/ubercars', methods=['POST'])
def create_ubercar():
  try:
    new_ubercar = request.json
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("INSERT INTO ubercars (model, year, make) VALUES (%s, %s, %s) RETURNING *", 
                   (new_ubercar['model'], new_ubercar['year'], new_ubercar['make']))
    created_ubercar = cursor.fetchone()
    connection.commit()
    connection.close()
    return created_ubercar, 201
  except Exception as e:
     return str(e), 500
  
@app.route('/ubercars/<ubercar_id>', methods=['GET'])
def show_ubercar(ubercar_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM ubercars WHERE id = %s", (ubercar_id,))
        ubercar = cursor.fetchone()
        if ubercar is None:
            connection.close()
            return "Ubercar Not Found", 404
        connection.close()
        return ubercar, 200
    except Exception as e:
        return str(e), 500
    
@app.route('/ubercars/<ubercar_id>', methods=['DELETE'])
def delete_ubercar(ubercar_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("DELETE FROM ubercars WHERE id = %s", (ubercar_id,))
        if cursor.rowcount == 0:
            return "Ubercar not found", 404
        connection.commit()
        cursor.close()
        return "Ubercar deleted successfully", 204
    except Exception as e:
        return str(e), 500
    
@app.route('/ubercars/<ubercar_id>', methods=['PUT'])
def update_ubercar(ubercar_id):
    try:
      connection = get_db_connection()
      cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
      cursor.execute("UPDATE ubercars SET model = %s, year = %s, make = %s WHERE id = %s RETURNING *", (request.json['model'], request.json['year'], request.json['make'], ubercar_id))
      updated_ubercar = cursor.fetchone()
      if updated_ubercar is None:
        return "Ubercar Not Found", 404
      connection.commit()
      connection.close()
      return updated_ubercar, 202
    except Exception as e:
      return str(e), 500

@app.route('/sign-token', methods=['GET'])
def sign_token():
    user = {
        "id": 1,
        "username": "test",
        "password": "test"
    }
    token = jwt.encode(user, os.getenv('JWT_SECRET'), algorithm="HS256")
    return jsonify({"token": token})

@app.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
        return jsonify({"user": decoded_token})
    except Exception as err:
       return jsonify({"err": err.message})

@app.route('/auth/sign-up', methods=['POST'])
def sign_up():
    try:
        # Get data from form
        new_user_data = request.get_json()

        # Find user in DB
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s;", (new_user_data["username"],))
        existing_user = cursor.fetchone()

        # Dont create a duplicate account
        if existing_user:
            cursor.close()
            return jsonify({"error": "Username already taken"}), 400

        # Encrypt the raw password
        hashed_password = bcrypt.hashpw(bytes(new_user_data["password"], 'utf-8'), bcrypt.gensalt())

        # Create the new user in DB
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id, username", (new_user_data["username"], hashed_password.decode('utf-8')))
        created_user = cursor.fetchone()
        connection.commit()
        connection.close()

        # Construct the payload
        payload = {"username": created_user["username"], "id": created_user["id"]}
        # Create the token, attaching the payload
        token = jwt.encode({ "payload": payload }, os.getenv('JWT_SECRET'))
        # Send the token instead of the user
        return jsonify({"token": token}), 201
    except Exception as err:
        return jsonify({"err": str(err)}), 401


@app.route('/auth/sign-in', methods=["POST"])
def sign_in():
    try:
        sign_in_form_data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s;", (sign_in_form_data["username"],))
        existing_user = cursor.fetchone()
        if existing_user is None:
            return jsonify({"err": "Invalid credentials."}), 401
        password_is_valid = bcrypt.checkpw(bytes(sign_in_form_data["password"], 'utf-8'), bytes(existing_user["password"], 'utf-8'))
        if not password_is_valid:
            return jsonify({"err": "Invalid credentials."}), 401
        

        # Construct the payload
        payload = {"username": existing_user["username"], "id": existing_user["id"]}
        # Create the token, attaching the payload
        token = jwt.encode({ "payload": payload }, os.getenv('JWT_SECRET'))
        # Send the token instead of the user
        return jsonify({"token": token}), 200
    
    except Exception as err:
        return jsonify({"err": err.message}), 500
    finally:
        connection.close()

@app.route('/users')
@token_required
def users_index():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, username FROM users;")
    users = cursor.fetchall()
    connection.close()
    return jsonify(users), 200

@app.route('/users/<user_id>')
@token_required
def users_id(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, username FROM users WHERE id = %s;", (user_id))
    user = cursor.fetchone()
    connection.close()
    if user is None:
        return jsonify({"err": "User not found"}), 404
    return jsonify(user), 200

app.run()