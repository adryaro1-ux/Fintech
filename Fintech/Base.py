import pytesseract
import mysql.connector
import pyautogui
import customtkinter as ctk
import time
import ctypes
import os
from PIL import Image, ImageDraw

# ==========================================================
# 1. TRUCO MAESTRO PARA LA BARRA DE TAREAS (IDENTIDAD DE APP)
# ==========================================================
try:
    # Esto le dice a Windows que NO es 'python.exe', sino una App única
    # Cambia el ID si alguna vez quieres resetear la caché de iconos
    myappid = 'seguros.horizonte.amp.asistencia.v3' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception as e:
    print(f"Error configurando ID de App: {e}")

# CONFIGURACIÓN OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
ctk.set_appearance_mode("dark")

def generar_logo_ico():
    """Genera un archivo .ico real del logo F-Escudo Cyberpunk en el directorio actual."""
    icon_path = os.path.join(os.getcwd(), "logo_amp.ico")
    
    # Creamos un lienzo grande para alta resolución
    logo = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(logo)
    color_neon = (0, 251, 255) # Cyan Neón
    
    # Dibujamos el Escudo (Diamante)
    puntos_diamante = [(128, 10), (246, 128), (128, 246), (10, 128)]
    d.polygon(puntos_diamante, outline=color_neon, width=15)
    
    # Dibujamos la 'F' Minimalista central
    d.line([(85, 80), (170, 80)], fill=color_neon, width=25)  # Techo
    d.line([(85, 80), (85, 185)], fill=color_neon, width=25)  # Espalda
    d.line([(85, 132), (145, 132)], fill=color_neon, width=25) # Medio
    
    # Guardamos como ICO con múltiples tamaños para que Windows no lo pixele
    logo.save(icon_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return icon_path

def mostrar_notificacion_vip(datos):
    """Interfaz VIP con logo corregido en barra de tareas y animaciones."""
    ventana = ctk.CTk()
    
    # --- APLICAR LOGO A LA BARRA DE TAREAS ---
    ruta_ico = generar_logo_ico()
    try:
        ventana.iconbitmap(ruta_ico) # Método oficial para .ico en Windows
    except:
        pass

    # CONFIGURACIÓN DE VENTANA (SIN BORDES)
    ventana.overrideredirect(True)
    ventana.attributes("-topmost", True)
    ventana.attributes("-alpha", 0.95)

    anchura, altura = 400, 420
    pos_final_x = ventana.winfo_screenwidth() - anchura - 20
    pos_y = ventana.winfo_screenheight() - altura - 60
    pos_inicial_x = ventana.winfo_screenwidth() 
    ventana.geometry(f"{anchura}x{altura}+{pos_inicial_x}+{pos_y}")

    # --- LÓGICA DE ANIMACIÓN ---
    def animar_entrada():
        x = pos_inicial_x
        while x > pos_final_x:
            x -= 20
            ventana.geometry(f"{anchura}x{altura}+{x}+{pos_y}")
            ventana.update()
            time.sleep(0.005)

    def cerrar_con_animacion():
        x = ventana.winfo_x()
        while x < pos_inicial_x:
            x += 25
            ventana.geometry(f"{anchura}x{altura}+{x}+{pos_y}")
            ventana.update()
            time.sleep(0.005)
        ventana.destroy()

    # --- ESTRUCTURA VISUAL (HEADER) ---
    header = ctk.CTkFrame(ventana, fg_color="#1a1a1a", corner_radius=0, height=75)
    header.pack(fill="x", side="top")
    
    img_pil = Image.open(ruta_ico)
    ctk_logo = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(50, 50))
    
    ctk.CTkLabel(header, image=ctk_logo, text="").pack(side="left", padx=(15, 5), pady=10)
    ctk.CTkLabel(header, text="SEGUROS HORIZONTE - AMP", 
                 font=("Roboto Medium", 16, "bold"), text_color="white").pack(side="left")
    
    ctk.CTkButton(header, text="✕", width=30, height=30, fg_color="transparent", 
                  text_color="#00fbff", hover_color="#E74C3C", command=cerrar_con_animacion).pack(side="right", padx=10)

    # --- CUERPO DE DATOS ---
    body = ctk.CTkFrame(ventana, fg_color="transparent")
    body.pack(pady=10, padx=25, fill="both", expand=True)

    ctk.CTkLabel(body, text=datos['nombre'].upper(), 
                 font=("Roboto Medium", 25, "bold"), text_color="#00fbff").pack(pady=(15, 5))
    
    ctk.CTkLabel(body, text=f"Documento: {datos['cedula']}", font=("Arial", 16), text_color="#AAAAAA").pack(pady=2)
    ctk.CTkLabel(body, text=f"📞 {datos['telefono']}", font=("Arial", 15), text_color="#AAAAAA").pack(pady=2)

    # ESTATUS CON GLOW
    es_al_dia = datos['estatus_pago'] == "Al día"
    color_status = "#00ff88" if es_al_dia else "#ff4444"
    
    status_frame = ctk.CTkFrame(body, fg_color="transparent", border_width=2, border_color=color_status, corner_radius=15)
    status_frame.pack(pady=25, padx=40, fill="x")
    ctk.CTkLabel(status_frame, text=datos['estatus_pago'].upper(), 
                 font=("Arial", 20, "bold"), text_color=color_status).pack(pady=15)

    # BOTÓN FINALIZAR (CYAN ORIGINAL)
    ctk.CTkButton(ventana, text="FINALIZAR ASISTENCIA AMP", 
                  font=("Arial", 14, "bold"),
                  corner_radius=20, 
                  fg_color="#00fbff", 
                  text_color="black", 
                  hover_color="#00c8cc",
                  command=cerrar_con_animacion).pack(side="bottom", pady=25, padx=50, fill="x")

    ventana.after(100, animar_entrada)
    ventana.mainloop()

def ejecutar_asistente():
    print("🚀 Motor de IA Seguros Horizonte Activo. Monitoreando Avaya...")
    prefijos = ["0212", "0412", "0424", "0414", "0416", "0426"]
    
    while True:
        try:
            # Captura área de Avaya Workspace
            region = (0, 0, 1000, 450)
            captura = pyautogui.screenshot(region=region)
            texto_raw = pytesseract.image_to_string(captura, config='--psm 6').strip()
            
            # Limpieza de ruido OCR
            texto_limpio = texto_raw.replace('Ø', '0').replace('O', '0').replace('o', '0')
            num_sucio = "".join(filter(str.isdigit, texto_limpio))
            
            num_paciente = None
            for pref in prefijos:
                idx = num_sucio.find(pref)
                if idx != -1:
                    num_paciente = num_sucio[idx : idx + 11]
                    break

            if num_paciente:
                # Conexión DB
                db = mysql.connector.connect(host="localhost", user="root", password="", database="fintech_horizontes")
                cursor = db.cursor(dictionary=True, buffered=True)
                cursor.execute("SELECT * FROM asegurados WHERE telefono = %s", (num_paciente,))
                cliente = cursor.fetchone()

                if cliente:
                    print(f"✅ ¡MATCH! Mostrando ficha de: {cliente['nombre']}")
                    db.close()
                    mostrar_notificacion_vip(cliente)
                    # No hacemos break para que siga escuchando la siguiente llamada
                db.close()
            
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Reintentando... ({e})")
            time.sleep(2)

if __name__ == "__main__":
    ejecutar_asistente()
