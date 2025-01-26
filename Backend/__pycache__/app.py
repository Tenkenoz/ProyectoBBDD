from flask import Flask, request, jsonify  # Permite manejar archivos JSON
from pymongo import MongoClient  # Para conectarnos a la base de datos
from flask_cors import CORS  # Para habilitar CORS

app = Flask(__name__)  # Definir el nombre de nuestra aplicación

# Credenciales de la base de datos.
mongo_uri = "mongodb+srv://pobando:patricio7@cluster0.f3tc9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# Conectamos con el cluster que habíamos creado en MongoDB Atlas
client = MongoClient(mongo_uri)
db = client['espe']
students_collection = db['estudiantes']

# Habilitamos CORS para todas las rutas
CORS(app)

# Definición de rutas
@app.route('/students', methods=['GET'])  # La ruta con el método GET
def get_students():
    students = list(students_collection.find({}, {'_id': 0}))
    return jsonify(students)

@app.route('/students/<student_id>', methods=['GET'])
def get_students_by_id(student_id):
    student = students_collection.find_one({"student_id": student_id}, {'_id': 0})
    if student:
        return jsonify(student)
    else:
        return jsonify({"message": "Estudiante no encontrado en la base de datos"}), 404

@app.route('/students/', methods=['POST'])
def add_student():
    student = request.json
    if not student.get('student_id') or students_collection.find_one({"student_id": student["student_id"]}):
        return jsonify({"message": "El ID del estudiante es obligatorio y debe ser único"}), 400  # Código del error

    students_collection.insert_one(student)
    return jsonify({"message": "Estudiante insertado"}), 200

@app.route('/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    result = students_collection.delete_one({"student_id": student_id})  # Se borra un ID específico

    if result.deleted_count:
        return jsonify({"message": "Estudiante eliminado de la base de datos"}), 200  # Mensaje de estudiante eliminado con el código 200
    else:
        return jsonify({"message": "No se pudo encontrar un estudiante"}), 404

@app.route('/students/<student_id>', methods=['PUT'])
def put_student(student_id):
    student = request.json
    result = students_collection.update_one({"student_id": student_id}, {"$set": student})

    if result.modified_count:
        return jsonify({"message": "Estudiante actualizado"}), 200
    else:
        return jsonify({"message": "No se pudo encontrar un estudiante"}), 404

if __name__ == '__main__':
    app.run(debug=True)
