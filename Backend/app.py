from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)

# Conexión a la base de datos
mongo_uri = "mongodb+srv://pobando:patricio7@cluster0.f3tc9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client['tienda']
productos_collection = db['productos']  # Colección de productos
carrito_collection = db['carrito']
cliente_collection = db['cliente']
compra_collection = db['compra']
tarjeta_collection = db['tarjeta']

# Habilitar CORS
CORS(app)

# Definición de rutas

# Obtener todos los productos
@app.route('/productos', methods=['GET'])
def get_productos():
    productos = list(productos_collection.find({}, {'_id': 0}))
    return jsonify(productos)


from bson import ObjectId

# Función que convierte los ObjectId a string
def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj


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

@app.route('/compra', methods=['POST'])
def confirmar_compra():
    try:
        data = request.json

        # Validación de datos recibidos
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400

        if not all(key in data for key in ['productos', 'subtotal', 'impuestos', 'total']):
            return jsonify({'error': 'Faltan datos en la solicitud'}), 400

        productos = data['productos']
        subtotal = data['subtotal']
        impuestos = data['impuestos']
        total = data['total']

        # Validar estructura de productos
        if not isinstance(productos, list) or not all('Id_Producto' in p and 'PrecioTotal' in p for p in productos):
            return jsonify({'error': 'La lista de productos tiene un formato inválido'}), 400

        # Crear el documento para guardar en la base de datos
        compra = {
            "productos": productos,
            "subtotal": subtotal,
            "impuestos": impuestos,
            "total": total,
            "fecha": datetime.now()
        }

        # Insertar la compra en la colección
        compra_collection.insert_one(compra)

        return jsonify({"mensaje": "Compra realizada con éxito"}), 200

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

@app.route('/tarjeta', methods=['POST'])
def add_tarjeta():
    data = request.get_json()

    # Validar los datos obligatorios
    campos_obligatorios = ['Numero_Tarjeta', 'Nombre_Titular', 'Fecha_Expiracion', 'CVV']
    for campo in campos_obligatorios:
        if campo not in data:
            return jsonify({"error": f"El campo {campo} es obligatorio"}), 400

    # Verificar si la tarjeta ya existe
    if tarjeta_collection.find_one({"Numero_Tarjeta": data['Numero_Tarjeta']}):
        return jsonify({"error": "La tarjeta ya está registrada"}), 400

    # Insertar la tarjeta en la base de datos
    tarjeta_collection.insert_one(data)
    return jsonify({"mensaje": "Tarjeta registrada con éxito"}), 201

# Ruta para registrar un cliente
@app.route('/cliente', methods=['POST'])
def add_cliente():
    try:
        # Obtener los datos del cliente desde la solicitud
        data = request.get_json()

        # Validar que los campos necesarios estén presentes
        nombre = data.get('Nombre')
        edad = data.get('Edad')
        correo = data.get('Correo')
        telefono = data.get('Telefono')
        contraseña = data.get('Contraseña')

        if not all([nombre, edad, correo, telefono, contraseña]):
            return jsonify({"error": "Todos los campos son obligatorios"}), 400

        # Verificar si el correo o teléfono ya existe
        if cliente_collection.find_one({"Correo": correo}) or cliente_collection.find_one({"Telefono": telefono}):
            return jsonify({"error": "El correo o teléfono ya está registrado"}), 400

        # Insertar el cliente en la colección
        cliente_collection.insert_one({
            "Nombre": nombre,
            "Edad": edad,
            "Correo": correo,
            "Telefono": telefono,
            "Contraseña": contraseña,
            "Carrito": [],
            "Pago": []
        })

        return jsonify({"mensaje": "Cliente registrado con éxito"}), 201

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

@app.route('/cliente/login', methods=['POST'])
def login_cliente():
    data = request.get_json()

    # Validar que se recibieron los datos necesarios
    correo = data.get('Correo')
    contraseña = data.get('Contraseña')

    if not correo or not contraseña:
        return jsonify({"error": "Correo y contraseña son requeridos"}), 400

    # Buscar al cliente en la base de datos
    cliente = cliente_collection.find_one({"Correo": correo, "Contraseña": contraseña})

    if cliente:
        # Convertir el ObjectId a string si es necesario
        cliente = convert_objectid_to_str(cliente)
        return jsonify(cliente), 200
    else:
        return jsonify({"error": "Correo o contraseña incorrectos"}), 401

@app.route("/carrito/agregar", methods=["POST"])
def agregar_al_carrito():
    data = request.json
    cliente_id = data.get("cliente_id")  # ID del cliente logueado
    producto_id = data.get("producto_id")  # ID del producto que se va a agregar

    if not cliente_id or not producto_id:
        return jsonify({"error": "Faltan datos"}), 400

    # Convertir el producto_id a entero
    try:
        producto_id = int(producto_id)  # Convertir a entero
    except ValueError:
        return jsonify({"error": "El producto_id debe ser un número entero válido"}), 400

    # Buscar al cliente por su ID
    cliente = cliente_collection.find_one({"_id": ObjectId(cliente_id)})
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # Verificar si el producto existe en la base de datos
    producto = productos_collection.find_one({"Id_Producto": producto_id})
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    # Obtener el carrito del cliente
    carrito = cliente.get("Carrito",[])

    # Evitar duplicados
    if producto_id not in carrito:
        carrito.append(producto_id)
        # Actualizar el carrito del cliente en la base de datos
        cliente_collection.update_one({"_id": ObjectId(cliente_id)}, {"$set": {"Carrito": carrito}})

    return jsonify({"mensaje": "Producto agregado al carrito"}), 200

# Obtener los productos en el carrito de un cliente
@app.route('/carrito/<cliente_id>', methods=['GET'])
def get_carrito(cliente_id):
    cliente = cliente_collection.find_one({"_id": ObjectId(cliente_id)})
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # Obtener los IDs de los productos en el carrito del cliente
    carrito_ids = cliente.get("Carrito", [])

    # Buscar los productos correspondientes
    productos_carrito = []
    for producto_id in carrito_ids:
        producto = productos_collection.find_one({"Id_Producto": producto_id}, {'_id': 0})
        if producto:
            productos_carrito.append(producto)

    return jsonify({"productos": productos_carrito}), 200



if __name__ == '__main__':
    app.run(debug=True)
