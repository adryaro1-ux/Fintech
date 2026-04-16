import mysql.connector
from mysql.connector import Error
from datetime import datetime

class Database:
    def __init__(self, host="localhost", user="root", password="", database="fintech_horizontes"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.init_db()
    
    def get_connection(self):
        """Establece conexión con la base de datos unificada"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
            return self.connection
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None
    
    def init_db(self):
        """Inicializa el esquema unificado con las tablas de Asegurados y Estudios"""
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()
            
            # Crear base de datos unificada
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.execute(f"USE {self.database}")
            
            # 1. Tabla de Estudios (Para el escaneo médico)
            # Cambiado 'nombre' a 'nombre_estudio' para evitar conflictos de palabras clave
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estudios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_estudio VARCHAR(255) UNIQUE NOT NULL,
                    precio DECIMAL(10, 2) NOT NULL,
                    fecha_escaneo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 2. Tabla de Asegurados (Para el monitoreo de main.py)
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
            print(f"[OK] Base de datos {self.database} inicializada correctamente")
            
        except Error as e:
            print(f"Error al inicializar base de datos: {e}")
    
    def agregar_estudio(self, nombre, precio, telefono_clinica="DESCONOCIDO"):
        """Agrega un nuevo estudio vinculado a la clínica detectada"""
        try:
            conn = self.get_connection()
            if conn is None: return False
            
            cursor = conn.cursor()
            # Añadimos la columna clinica_emisor al INSERT
            cursor.execute('''
                INSERT IGNORE INTO estudios (nombre_estudio, precio, clinica_emisor)
                VALUES (%s, %s, %s)
            ''', (nombre, precio, telefono_clinica))
            
            conn.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error al agregar estudio: {e}")
            return False
    
    def obtener_estudios(self):
        """Obtiene estudios uniendo la tabla con asegurados para mostrar el nombre de la clínica"""
        try:
            conn = self.get_connection()
            if conn is None: return []
            
            cursor = conn.cursor()
            # Usamos LEFT JOIN para que, si el número coincide con la tabla asegurados, 
            # nos traiga el nombre de la clínica.
            cursor.execute('''
                SELECT 
                    e.id, 
                    e.nombre_estudio, 
                    IFNULL(a.nombre, e.clinica_emisor) as clinica, 
                    e.precio, 
                    DATE_FORMAT(e.fecha_escaneo, '%d/%m/%Y %H:%i') as fecha
                FROM estudios e
                LEFT JOIN asegurados a ON e.clinica_emisor = a.telefono
                ORDER BY e.id DESC
            ''')
            
            resultados = cursor.fetchall()
            cursor.close()
            return resultados
        except Error as e:
            print(f"Error al obtener estudios: {e}")
            return []
    
    def obtener_totales(self):
        """Calcula el resumen para el panel lateral de gestión"""
        try:
            conn = self.get_connection()
            if conn is None: return (0, 0)
            
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*), COALESCE(SUM(precio), 0) FROM estudios')
            resultado = cursor.fetchone()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error al obtener totales: {e}")
            return (0, 0)

    def estudio_existe(self, nombre):
        """Valida si el estudio ya fue procesado para evitar duplicados"""
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM estudios WHERE nombre_estudio = %s', (nombre,))
            existe = cursor.fetchone() is not None
            cursor.close()
            return existe
        except Error as e:
            return False
    
    def eliminar_estudio(self, estudio_id):
        """Elimina un registro específico del panel de liquidación"""
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute('DELETE FROM estudios WHERE id = %s', (estudio_id,))
            conn.commit()
            cursor.close()
            return True
        except Error as e:
            return False
    
    def close_connection(self):
        """Cierra el acceso a MySQL de forma segura"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[OK] Sesión de base de datos finalizada")