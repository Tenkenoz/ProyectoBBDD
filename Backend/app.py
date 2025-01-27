from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Conexión a MongoDB
try:
    mongo_uri = "mongodb+srv://pobando:patricio7@cluster0.f3tc9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(mongo_uri)
    db = client['tienda']
    productos_collection = db['productos']
    carrito_collection = db['carrito']
    cliente_collection = db['cliente']
    compra_collection = db['compra']
    tarjeta_collection = db['tarjeta']
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")

# Función auxiliar para convertir ObjectId a string
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
    productos = list(productos_collection.find({}, {'_id': 0}))
    return jsonify(productos)

# Obtener un producto por ID
@app.route('/productos/<id_producto>', methods=['GET'])
def get_producto_by_id(id_producto):
    producto = productos_collection.find_one({"Id_Producto": id_producto}, {'_id': 0})
    if producto:
        return jsonify(producto)
    return jsonify({"message": "Producto no encontrado"}), 404

# Agregar un producto
@app.route('/productos', methods=['POST'])
def add_producto():
    producto = request.json
    if not producto.get('Id_Producto') or productos_collection.find_one({"Id_Producto": producto["Id_Producto"]}):
        return jsonify({"message": "El ID del producto es obligatorio y debe ser único"}), 400
    productos_collection.insert_one(producto)
    return jsonify({"message": "Producto insertado"}), 201

# Eliminar un producto
@app.route('/productos/<id_producto>', methods=['DELETE'])
def delete_producto(id_producto):
    result = productos_collection.delete_one({"Id_Producto": id_producto})
    return jsonify({"message": "Producto eliminado" if result.deleted_count else "Producto no encontrado"}), 200

# Actualizar un producto
@app.route('/productos/<id_producto>', methods=['PUT'])
def put_producto(id_producto):
    producto = request.json
    result = productos_collection.update_one({"Id_Producto": id_producto}, {"$set": producto})
    return jsonify({"message": "Producto actualizado" if result.modified_count else "Producto no encontrado"}), 200

# Registrar cliente con contraseña encriptada
@app.route('/cliente', methods=['POST'])
def add_cliente():
    try:
        data = request.get_json()
        if not all(key in data for key in ['Nombre', 'Edad', 'Correo', 'Telefono', 'Contraseña']):
            return jsonify({"error": "Todos los campos son obligatorios"}), 400

        # Verificar si el correo o teléfono ya existe
        if cliente_collection.find_one({"Correo": data['Correo']}) or cliente_collection.find_one({"Telefono": data['Telefono']}):
            return jsonify({"error": "El correo o teléfono ya está registrado"}), 400

        # Hashear la contraseña antes de guardarla
        data['Contraseña'] = generate_password_hash(data['Contraseña'])
        data['Carrito'] = []
        cliente_collection.insert_one(data)

        return jsonify({"mensaje": "Cliente registrado con éxito"}), 201
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Login de cliente
@app.route('/cliente/login', methods=['POST'])
def login_cliente():
    data = request.get_json()
    correo = data.get('Correo')
    contraseña = data.get('Contraseña')

    cliente = cliente_collection.find_one({"Correo": correo})
    if cliente and check_password_hash(cliente['Contraseña'], contraseña):
        return jsonify(convert_objectid_to_str(cliente)), 200
    return jsonify({"error": "Correo o contraseña incorrectos"}), 401

# Agregar producto al carrito
@app.route("/carrito/agregar", methods=["POST"])
def agregar_al_carrito():
    data = request.json
    cliente_id = data.get("cliente_id")
    producto_id = data.get("producto_id")

    if not cliente_id or not producto_id:
        return jsonify({"error": "Faltan datos"}), 400

    cliente = cliente_collection.find_one({"_id": ObjectId(cliente_id)})
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    producto = productos_collection.find_one({"Id_Producto": producto_id})
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    # Evitar duplicados
    if producto_id not in cliente.get("Carrito", []):
        cliente_collection.update_one({"_id": ObjectId(cliente_id)}, {"$addToSet": {"Carrito": producto_id}})

    return jsonify({"mensaje": "Producto agregado al carrito"}), 200

# Obtener productos en el carrito
@app.route('/carrito/<cliente_id>', methods=['GET'])
def get_carrito(cliente_id):
    cliente = cliente_collection.find_one({"_id": ObjectId(cliente_id)})
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    carrito_ids = cliente.get("Carrito", [])
    productos_carrito = list(productos_collection.find({"Id_Producto": {"$in": carrito_ids}}, {'_id': 0}))

    return jsonify({"productos": productos_carrito}), 200

# Confirmar compra
@app.route('/compra', methods=['POST'])
def confirmar_compra():
    try:
        data = request.json
        if not all(key in data for key in ['productos', 'subtotal', 'impuestos', 'total', 'cliente_id']):
            return jsonify({'error': 'Faltan datos en la solicitud'}), 400

        cliente_id = data['cliente_id']
        cliente = cliente_collection.find_one({"_id": ObjectId(cliente_id)})
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404

        compra = {
            "cliente_id": cliente_id,
            "productos": data['productos'],
            "subtotal": data['subtotal'],
            "impuestos": data['impuestos'],
            "total": data['total'],
            "fecha": datetime.now()
        }

        compra_collection.insert_one(compra)
        cliente_collection.update_one({"_id": ObjectId(cliente_id)}, {"$set": {"Carrito": []}})

        return jsonify({"mensaje": "Compra realizada con éxito"}), 200
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
