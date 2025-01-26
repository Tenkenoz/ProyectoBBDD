from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import json_util
import json


app = Flask(__name__)
CORS(app)

# MongoDB connection
try:
    mongo_uri = "mongodb+srv://jjjaguaco:20030706Jq@dbapi.nfarw.mongodb.net/?retryWrites=true&w=majority&appName=DBAPI"
    client = MongoClient(mongo_uri)
    db = client['Amazon']
    productos_collection = db['Productos']
    print("Successful MongoDB connection.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Get all products
@app.route('/productos', methods=['GET'])
def obtener_productos():
    try:
        productos = list(productos_collection.find({}))
        productos_json = json.loads(json_util.dumps(productos))
        return jsonify(productos_json)
    except Exception as e:
        print(f"Error getting products: {e}")
        return jsonify({"error": str(e)}), 500

# Get product by ID
@app.route('/productos/<string:producto_id>', methods=['GET'])
def obtener_producto(producto_id):
    try:
        producto = productos_collection.find_one({"productolD": producto_id})
        if producto:
            producto_json = json.loads(json_util.dumps(producto))
            return jsonify(producto_json)
        else:
            return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        print(f"Error getting product: {e}")
        return jsonify({"error": str(e)}), 500

# Add a new product
@app.route('/productos', methods=['POST'])
def agregar_producto():
    try:
        producto = request.json
        if not producto.get("productolD"):
            return jsonify({"error": "productolD is required"}), 400

        if productos_collection.find_one({"productolD": producto["productolD"]}):
            return jsonify({"error": "Product with this ID already exists"}), 400

        productos_collection.insert_one(producto)
        return jsonify({"message": "Product added successfully"}), 201
    except Exception as e:
        print(f"Error adding product: {e}")
        return jsonify({"error": str(e)}), 500

# Delete a product by ID
@app.route('/productos/<string:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    try:
        result = productos_collection.delete_one({"productolD": producto_id})
        if result.deleted_count > 0:
            return jsonify({"message": "Product deleted successfully"}), 200
        else:
            return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        print(f"Error deleting product: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)