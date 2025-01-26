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

@app.route('/carrito', methods=['GET'])
def get_carrito():
    # Obtener el carrito como una lista de IDs de productos
    carrito = list(carrito_collection.find({}, {'_id': 0, 'Id_Producto': 1}))
    carrito_ids = [item['Id_Producto'] for item in carrito]  # Extraer solo los IDs de los productos

    productos_completos = []

    for producto_id in carrito_ids:
        # Buscar el producto completo en la base de datos
        producto = productos_collection.find_one({"Id_Producto": producto_id}, {'_id': 0})
        
        if producto:
            # Supongamos que la cantidad está siempre fija (puede ajustarse según los requerimientos)
            producto['Cantidad'] = 1  # O puedes calcular la cantidad de otra forma
            producto['PrecioTotal'] = producto['Precio'] * producto['Cantidad']
            productos_completos.append(producto)

    subtotal = sum(item['PrecioTotal'] for item in productos_completos)
    cantidad_total = sum(item['Cantidad'] for item in productos_completos)

    return jsonify({
        'productos': productos_completos,
        'subtotal': subtotal,
        'cantidad_total': cantidad_total
    })

@app.route('/carrito', methods=['POST'])
def add_to_carrito():
    data = request.get_json()  # Recibir datos en formato JSON
    
    if not data or 'Id_Producto' not in data:
        return jsonify({'error': 'El campo Id_Producto es obligatorio'}), 400
    
    producto_id = data['Id_Producto']
    
    # Verificar si el producto existe en la colección de productos
    producto = productos_collection.find_one({"Id_Producto": producto_id})
    if not producto:
        return jsonify({'error': 'El producto no existe'}), 404
    
    # Agregar el ID del producto al carrito solo si no existe ya
    if carrito_collection.find_one({'Id_Producto': producto_id}):
        return jsonify({'error': 'El producto ya está en el carrito'}), 400
    
    carrito_collection.insert_one({'Id_Producto': producto_id})
    return jsonify({'mensaje': 'Producto agregado al carrito con éxito'}), 201


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





if __name__ == '__main__':
    app.run(debug=True)
