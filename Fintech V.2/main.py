import pytesseract
import mysql.connector
import pyautogui
import customtkinter as ctk
import time
import ctypes
import os
from PIL import Image, ImageTk 

# --- 1. CONFIGURACIÓN DE IDENTIDAD Y ENTORNO ---
try:
    myappid = 'seguros.horizonte.amp.asistencia.v3' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except: pass

# Verifica que esta ruta sea correcta en tu PC
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
ctk.set_appearance_mode("dark")

icon_path = r"C:\xampp\htdocs\Fintech\logo_amp.ico"
root_oculta = ctk.CTk()
root_oculta.withdraw() 

# Regla de Oro: Icono Maestro
if os.path.exists(icon_path):
    try:
        img_pil_master = Image.open(icon_path)
        root_oculta.app_icon = ImageTk.PhotoImage(img_pil_master)
        root_oculta.iconphoto(True, root_oculta.app_icon)
    except: pass

ventana_abierta = False

# --- 2. FUNCIONES DE APOYO ---
def cerrar_manual(v):
    global ventana_abierta
    ventana_abierta = False
    v.destroy()

def guardar_asegurado(ventana_reg, telefono, entry_nombre, entry_cedula):
    nombre = entry_nombre.get().strip().upper()
    cedula = entry_cedula.get().strip()

    if not nombre or not cedula:
        print("⚠️ Datos incompletos.")
        return

    try:
        db = mysql.connector.connect(host="localhost", user="root", password="", database="fintech_horizontes")
        cursor = db.cursor()
        query = "INSERT INTO asegurados (nombre, cedula, telefono, estatus_pago) VALUES (%s, %s, %s, 'Al día')"
        cursor.execute(query, (nombre, cedula, telefono))
        db.commit()
        db.close()
        print(f"✅ {nombre} registrado en Fintech.")
        cerrar_manual(ventana_reg)
    except Exception as e:
        print(f"❌ Error SQL: {e}")

# --- 3. VENTANAS DE INTERFAZ ---
def ventana_registro_rapido(telefono, ventana_notificacion):
    ventana_notificacion.destroy()
    reg_win = ctk.CTkToplevel(root_oculta)
    reg_win.title("Registro Fintech")
    reg_win.geometry("400x480")
    reg_win.attributes("-topmost", True)
    
    ctk.CTkLabel(reg_win, text="REGISTRO DE ASEGURADO", font=("Roboto", 18, "bold"), text_color="#00fbff").pack(pady=20)
    ctk.CTkLabel(reg_win, text="Teléfono:").pack()
    e_tel = ctk.CTkEntry(reg_win, width=250); e_tel.insert(0, telefono); e_tel.configure(state="disabled"); e_tel.pack(pady=5)
    ctk.CTkLabel(reg_win, text="Nombre:").pack()
    e_nom = ctk.CTkEntry(reg_win, width=250); e_nom.pack(pady=5)
    ctk.CTkLabel(reg_win, text="Cédula:").pack()
    e_ced = ctk.CTkEntry(reg_win, width=250); e_ced.pack(pady=5)

    ctk.CTkButton(reg_win, text="GUARDAR", fg_color="#00ff88", text_color="black", command=lambda: guardar_asegurado(reg_win, telefono, e_nom, e_ced)).pack(pady=20)
    ctk.CTkButton(reg_win, text="CANCELAR", fg_color="transparent", border_width=1, command=lambda: cerrar_manual(reg_win)).pack()

def abrir_gestion_y_cerrar(ventana_notificacion, datos_cliente):
    global ventana_abierta
    telefono = datos_cliente.get('telefono', '')
    ventana_notificacion.destroy()
    ventana_abierta = False 
    if str(telefono).startswith("0212"):
        try:
            from gestion_estudios import abrir_ventana_escaneo
            abrir_ventana_escaneo(telefono) 
        except Exception as e: print(f"❌ Error: {e}")

def mostrar_notificacion_vip(datos):
    global ventana_abierta
    if ventana_abierta: return
    ventana_abierta = True
    
    ventana = ctk.CTkToplevel(root_oculta)
    ventana.overrideredirect(True)
    ventana.attributes("-topmost", True)
    ventana.geometry(f"400x480+{ventana.winfo_screenwidth()-420}+{ventana.winfo_screenheight()-540}")

    # Header con Logo
    header = ctk.CTkFrame(ventana, fg_color="#1a1a1a", height=70, corner_radius=0); header.pack(fill="x")
    if os.path.exists(icon_path):
        img_pil = Image.open(icon_path).resize((30, 30), Image.LANCZOS)
        logo_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(30, 30))
        ctk.CTkLabel(header, image=logo_ctk, text="").pack(side="left", padx=15)
    ctk.CTkLabel(header, text="SEGUROS HORIZONTE", font=("Roboto", 14, "bold")).pack(side="left")

    # Datos y Estatus
    ctk.CTkLabel(ventana, text=datos['nombre'].upper(), font=("Roboto Medium", 22, "bold"), text_color="#00fbff").pack(pady=(30, 10))
    es_nuevo = datos['estatus_pago'] == "SIN REGISTRO"
    color = "#F1C40F" if es_nuevo else ("#00ff88" if datos['estatus_pago'] == "Al día" else "#ff4444")
    
    f_status = ctk.CTkFrame(ventana, fg_color="transparent", border_width=2, border_color=color, corner_radius=15)
    f_status.pack(pady=20, padx=40, fill="x")
    ctk.CTkLabel(f_status, text=datos['estatus_pago'].upper(), font=("Arial", 18, "bold"), text_color=color).pack(pady=10)

    # Botones
    if es_nuevo:
        ctk.CTkButton(ventana, text="REGISTRAR EN FINTECH", fg_color="#00ff88", text_color="black", command=lambda: ventana_registro_rapido(datos['telefono'], ventana)).pack(pady=5, padx=40, fill="x")
    else:
        ctk.CTkButton(ventana, text="PROCEDER A ESCANEO", fg_color="#00fbff", text_color="black", command=lambda: abrir_gestion_y_cerrar(ventana, datos)).pack(pady=5, padx=40, fill="x")
    
    ctk.CTkButton(ventana, text="OMITIR ASISTENCIA", fg_color="transparent", border_width=1, command=lambda: cerrar_manual(ventana)).pack(pady=10, padx=40, fill="x")

# --- 4. MOTOR DE DETECCIÓN (EL CORAZÓN DEL SCRIPT) ---
def ejecutar_asistente():
    print("🚀 Sistema Fintech Activo - Escaneando pantalla...")
    prefijos = ["0212", "0412", "0424", "0414", "0416", "0426"]
    
    while True:
        try:
            if not ventana_abierta:
                # Captura la zona donde suele aparecer el número en Avaya
                region = (0, 0, 1000, 500) 
                captura = pyautogui.screenshot(region=region)
                texto = pytesseract.image_to_string(captura, config='--psm 6')
                
                # Extraer solo dígitos
                num_sucio = "".join(filter(str.isdigit, texto))
                
                num_encontrado = None
                for pref in prefijos:
                    idx = num_sucio.find(pref)
                    if idx != -1:
                        num_encontrado = num_sucio[idx : idx + 11]
                        break

                if num_encontrado:
                    print(f"🔎 Número detectado: {num_encontrado}")
                    db = mysql.connector.connect(host="localhost", user="root", password="", database="fintech_horizontes")
                    cursor = db.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM asegurados WHERE telefono = %s", (num_encontrado,))
                    cliente = cursor.fetchone()
                    db.close()

                    if cliente:
                        mostrar_notificacion_vip(cliente)
                    else:
                        mostrar_notificacion_vip({'nombre': 'DESCONOCIDO', 'telefono': num_encontrado, 'estatus_pago': 'SIN REGISTRO'})
            
            root_oculta.update()
            time.sleep(1.5) # Pausa para no saturar el procesador
        except Exception as e:
            print(f"Err: {e}")
            time.sleep(2)

if __name__ == "__main__":
    ejecutar_asistente()