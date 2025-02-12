import os
import psycopg2, psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, request
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

app.run()