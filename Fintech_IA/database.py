import sqlite3
import os
import sys

class Database:
    def __init__(self):
        # El archivo DB se llamará exactamente como solicitaste
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Fintech_horizontes.db")
        self.init_db()
    
    def get_connection(self):
        """ Retorna una conexión SQLite """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"❌ Error de conexión SQLite: {e}")
            return None
    
    def init_db(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabla: estudios (Para los escaneos realizados)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estudios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_estudio TEXT NOT NULL,
                    precio REAL NOT NULL,
                    clinica_emisor TEXT DEFAULT 'DESCONOCIDO',
                    fecha_escaneo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabla: registros (Para validar números guardados de asegurados o clínicas)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cedula TEXT UNIQUE NOT NULL,
                    telefono TEXT NOT NULL,
                    estatus_pago TEXT DEFAULT 'Al día'
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Error en init_db SQLite: {e}")

    def guardar_asegurado(self, nombre, cedula, telefono):
        """ Guarda en la tabla 'registros' """
        try:
            conn = self.get_connection()
            if not conn: return False
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO registros (nombre, cedula, telefono, estatus_pago) VALUES (?, ?, ?, 'Al día')",
                (nombre.upper(), cedula, telefono)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error al guardar en registros: {e}")
            return False
    
    def agregar_estudio(self, nombre, precio, telefono_clinica="DESCONOCIDO"):
        try:
            conn = self.get_connection()
            if not conn: return False
            cursor = conn.cursor()
            cursor.execute("INSERT INTO estudios (nombre_estudio, precio, clinica_emisor) VALUES (?, ?, ?)", 
                           (nombre, precio, telefono_clinica))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False
    
    def obtener_estudios(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Ajustamos la consulta para SQLite (Uniendo con la nueva tabla 'registros')
            cursor.execute('''
                SELECT e.id, e.nombre_estudio, IFNULL(r.nombre, e.clinica_emisor), e.precio, 
                       strftime('%d/%m/%Y %H:%M', e.fecha_escaneo)
                FROM estudios e LEFT JOIN registros r ON e.clinica_emisor = r.telefono
                ORDER BY e.id DESC
            ''')
            res = cursor.fetchall()
            conn.close()
            return res
        except: return []

    def eliminar_estudio(self, estudio_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM estudios WHERE id = ?', (estudio_id,))
            conn.commit()
            conn.close()
            return True
        except: return False
