from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# Database Connection
mongo_uri = "mongodb+srv://pobando:patricio7@cluster0.f3tc9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client['tienda']
productos_collection = db['productos']
carrito_collection = db['carrito']
cliente_collection = db['cliente']
compra_collection = db['compra']
tarjeta_collection = db['tarjeta']

# Enable CORS with more specific configuration
CORS(app, resources={r"/*": {"origins": "*"}})

def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj

# Obtener todos los productos
@app.route('/productos', methods=['GET'])
def get_productos():
    try:
        productos = list(productos_collection.find({}, {'_id': 0}))
        return jsonify(productos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Obtener un producto por su ID
@app.route('/productos/<id_producto>', methods=['GET'])
def get_producto_by_id(id_producto):
    try:
        producto = productos_collection.find_one({"Id_Producto": int(id_producto)}, {'_id': 0})
        if producto:
            return jsonify(producto)
        else:
            return jsonify({"message": "Producto no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Buscar productos
@app.route('/productos/buscar', methods=['GET'])
def buscar_productos():
    query = request.args.get('q', '').lower()
    try:
        productos = list(productos_collection.find({
            "$or": [
                {"Nombre": {"$regex": query, "$options": "i"}},
                {"Descripcion": {"$regex": query, "$options": "i"}},
                {"Categoria": {"$regex": query, "$options": "i"}}
            ]
        }, {'_id': 0}))
        return jsonify(productos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Agregar un nuevo producto
@app.route('/productos', methods=['POST'])
def add_producto():
    try:
        producto = request.json
        if not producto.get('Id_Producto') or productos_collection.find_one({"Id_Producto": producto["Id_Producto"]}):
            return jsonify({"message": "El ID del producto es obligatorio y debe ser único"}), 400
        productos_collection.insert_one(producto)
        return jsonify({"message": "Producto insertado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Eliminar un producto por su ID
@app.route('/productos/<id_producto>', methods=['DELETE'])
def delete_producto(id_producto):
    try:
        result = productos_collection.delete_one({"Id_Producto": int(id_producto)})
        if result.deleted_count:
            return jsonify({"message": "Producto eliminado"}), 200
        else:
            return jsonify({"message": "Producto no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Actualizar un producto por su ID
@app.route('/productos/<id_producto>', methods=['PUT'])
def put_producto(id_producto):
    try:
        producto = request.json
        result = productos_collection.update_one({"Id_Producto": int(id_producto)}, {"$set": producto})
        if result.modified_count:
            return jsonify({"message": "Producto actualizado"}), 200
        else:
            return jsonify({"message": "Producto no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Gestión del carrito
@app.route('/carrito', methods=['GET'])
def get_carrito():
    try:
        carrito = list(carrito_collection.find({}, {'_id': 0, 'Id_Producto': 1}))
        carrito_ids = [item['Id_Producto'] for item in carrito]

        productos_completos = []
        subtotal = 0
        cantidad_total = 0

        for producto_id in carrito_ids:
            producto = productos_collection.find_one({"Id_Producto": producto_id}, {'_id': 0})
            
            if producto:
                producto['Cantidad'] = 1
                producto['PrecioTotal'] = producto['Precio'] * producto['Cantidad']
                productos_completos.append(producto)
                subtotal += producto['PrecioTotal']
                cantidad_total += 1

        return jsonify({
            'productos': productos_completos,
            'subtotal': subtotal,
            'cantidad_total': cantidad_total
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/carrito', methods=['POST'])
def add_to_carrito():
    try:
        data = request.get_json()
        
        if not data or 'Id_Producto' not in data:
            return jsonify({'error': 'El campo Id_Producto es obligatorio'}), 400
        
        producto_id = data['Id_Producto']
        
        producto = productos_collection.find_one({"Id_Producto": producto_id})
        if not producto:
            return jsonify({'error': 'El producto no existe'}), 404
        
        if carrito_collection.find_one({'Id_Producto': producto_id}):
            return jsonify({'error': 'El producto ya está en el carrito'}), 400
        
        carrito_collection.insert_one({'Id_Producto': producto_id})
        return jsonify({'mensaje': 'Producto agregado al carrito con éxito'}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Otras rutas (compra, cliente, tarjeta) permanecen igual que en tu código original

if __name__ == '__main__':
    app.run(debug=True, port=5000)