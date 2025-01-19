from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)

# Conexión a la base de datos
mongo_uri = "mongodb+srv://pobando:patricio7@cluster0.f3tc9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client['tienda']
productos_collection = db['productos']  # Colección de productos

# Habilitar CORS
CORS(app)

# Definición de rutas

# Obtener todos los productos
@app.route('/productos', methods=['GET'])
def get_productos():
    productos = list(productos_collection.find({}, {'_id': 0}))
    return jsonify(productos)

# Obtener un producto por su ID
@app.route('/productos/<id_producto>', methods=['GET'])
def get_producto_by_id(id_producto):
    producto = productos_collection.find_one({"Id_Producto": id_producto}, {'_id': 0})
    if producto:
        return jsonify(producto)
    else:
        return jsonify({"message": "Producto no encontrado"}), 404

# Agregar un nuevo producto
@app.route('/productos', methods=['POST'])
def add_producto():
    producto = request.json
    if not producto.get('Id_Producto') or productos_collection.find_one({"Id_Producto": producto["Id_Producto"]}):
        return jsonify({"message": "El ID del producto es obligatorio y debe ser único"}), 400
    productos_collection.insert_one(producto)
    return jsonify({"message": "Producto insertado"}), 200

# Eliminar un producto por su ID
@app.route('/productos/<id_producto>', methods=['DELETE'])
def delete_producto(id_producto):
    result = productos_collection.delete_one({"Id_Producto": id_producto})
    if result.deleted_count:
        return jsonify({"message": "Producto eliminado"}), 200
    else:
        return jsonify({"message": "Producto no encontrado"}), 404

# Actualizar un producto por su ID
@app.route('/productos/<id_producto>', methods=['PUT'])
def put_producto(id_producto):
    producto = request.json
    result = productos_collection.update_one({"Id_Producto": id_producto}, {"$set": producto})
    if result.modified_count:
        return jsonify({"message": "Producto actualizado"}), 200
    else:
        return jsonify({"message": "Producto no encontrado"}), 404

if __name__ == '__main__':
    app.run(debug=True)
