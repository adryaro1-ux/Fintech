import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self, host="localhost", user="root", password="", database="fintech_horizontes"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.init_db()
    
    def get_connection(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host, user=self.user,
                    password=self.password, database=self.database
                )
            return self.connection
        except Error as e:
            print(f"❌ Error de conexión DB: {e}")
            return None
    
    def init_db(self):
        try:
            conn = mysql.connector.connect(host=self.host, user=self.user, password=self.password)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.execute(f"USE {self.database}")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estudios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_estudio VARCHAR(255) NOT NULL,
                    precio DECIMAL(10, 2) NOT NULL,
                    clinica_emisor VARCHAR(20) DEFAULT 'DESCONOCIDO',
                    fecha_escaneo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS asegurados (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    cedula VARCHAR(20) UNIQUE NOT NULL,
                    telefono VARCHAR(20) NOT NULL,
                    estatus_pago VARCHAR(20) DEFAULT 'Al día'
                )
            ''')
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"❌ Error en init_db: {e}")

    def guardar_asegurado(self, nombre, cedula, telefono):
        """Guarda un nuevo asegurado desde la notificación rápida"""
        try:
            conn = self.get_connection()
            if not conn: return False
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO asegurados (nombre, cedula, telefono, estatus_pago) VALUES (%s, %s, %s, 'Al día')",
                (nombre.upper(), cedula, telefono)
            )
            conn.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Error al guardar asegurado: {e}")
            return False
    
    def agregar_estudio(self, nombre, precio, telefono_clinica="DESCONOCIDO"):
        try:
            conn = self.get_connection()
            if not conn: return False
            cursor = conn.cursor()
            cursor.execute("INSERT INTO estudios (nombre_estudio, precio, clinica_emisor) VALUES (%s, %s, %s)", 
                           (nombre, precio, telefono_clinica))
            conn.commit()
            cursor.close()
            return True
        except Error as e:
            return False
    
    def obtener_estudios(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.id, e.nombre_estudio, IFNULL(a.nombre, e.clinica_emisor), e.precio, 
                       DATE_FORMAT(e.fecha_escaneo, '%d/%m/%Y %H:%i')
                FROM estudios e LEFT JOIN asegurados a ON e.clinica_emisor = a.telefono
                ORDER BY e.id DESC
            ''')
            res = cursor.fetchall()
            cursor.close()
            return res
        except: return []

    def eliminar_estudio(self, estudio_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM estudios WHERE id = %s', (estudio_id,))
            conn.commit()
            cursor.close()
            return True
        except: return False
