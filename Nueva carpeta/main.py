import pytesseract
import mysql.connector
import pyautogui
import customtkinter as ctk
import tkinter as tk
import os
import pystray
import re
import time
from PIL import Image, ImageTk
import threading
import sys
import ctypes
from ctypes import wintypes
from database import Database
from price_manager import PriceManager

# --- IDENTIDAD DE APP PARA WINDOWS ---
try:
    myappid = 'seguros.horizontes.scanner.ai.v3' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except: pass

# Pre-cargar gestor de precios para validación rápida en consola
try:
    print("[DEBUG] Inicializando Gestor de Precios...")
    pm_global = PriceManager()
except Exception as e:
    print(f"[ERROR] No se pudo inicializar PriceManager: {e}")

# --- CONFIGURACIÓN TESSERACT ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
ctk.set_appearance_mode("dark")

import subprocess

# --- UTILIDAD PARA RUTAS ---
def resource_path(relative_path):
    """ Obtiene la ruta absoluta para recursos, compatible con PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def esta_corriendo_avaya():
    """ Revisa si Avaya está presente usando 4 niveles de redundancia extrema """
    encontrado = [False]
    
    # NIVEL 1: Enumeración de Ventanas (Incluyendo ventanas de sistema/admin)
    def callback(hwnd, extra):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            t = buff.value.lower()
            # Búsqueda ultra flexible
            if "avaya" in t or "communicator" in t or "one-x" in t or "onex" in t:
                encontrado[0] = True
                return False 
        return True

    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(callback)
    ctypes.windll.user32.EnumWindows(cb, 0)
    if encontrado[0]: return True

    # NIVEL 2: Búsqueda en lista de procesos (Búsqueda por cadena parcial)
    try:
        # Buscamos en toda la tabla de procesos sin filtros de nombre para evitar bloqueos
        out = subprocess.check_output('tasklist /NH', shell=True).decode('latin-1', errors='ignore').lower()
        if "avaya" in out or "onex" in out or "communicator" in out:
            return True
    except: pass

    # NIVEL 3: Consulta WMI Simple
    try:
        out_wmi = subprocess.check_output('wmic process get name', shell=True).decode('latin-1', errors='ignore').lower()
        if "avaya" in out_wmi or "onex" in out_wmi or "communicator" in out_wmi:
            return True
    except: pass

    # NIVEL 4: Fallback de seguridad (Intento directo por clase de ventana común en Avaya)
    if ctypes.windll.user32.FindWindowW(None, "Avaya one-X® Communicator"):
        return True
        
    return False

def obtener_hwnd_avaya():
    """ Busca el HWND de la ventana de Avaya de forma ultra flexible """
    target_hwnd = [None]
    def callback(hwnd, extra):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            t = buff.value.lower()
            if "avaya" in t or "communicator" in t or "one-x" in t:
                target_hwnd[0] = hwnd
                return False
        return True
    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(callback)
    ctypes.windll.user32.EnumWindows(cb, 0)
    
    # Si falla, intentamos búsqueda directa por título exacto (con el símbolo ®)
    if not target_hwnd[0]:
        target_hwnd[0] = ctypes.windll.user32.FindWindowW(None, "Avaya one-X® Communicator")
        
    return target_hwnd[0]

def obtener_rect_avaya():
    """ Busca la ventana de Avaya y retorna sus coordenadas mediante su HWND """
    hwnd = obtener_hwnd_avaya()
    if not hwnd:
        return None
    
    rect = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.pointer(rect))
    return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

class EsperarAvaya(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sincronización Fintech")
        self.geometry("400x200")
        self.resizable(False, False)
        # Centrar ventana
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"400x200+{int(sw/2-200)}+{int(sh/2-100)}")
        
        self.icon_path = resource_path("logo_amp.ico")
        if os.path.exists(self.icon_path):
            try: self.iconbitmap(self.icon_path)
            except: pass

        ctk.CTkLabel(self, text="🛡️ ESPERANDO SISTEMA AVAYA", font=("Segoe UI", 16, "bold"), text_color="#3b82f6").pack(pady=(40, 10))
        self.lbl = ctk.CTkLabel(self, text="Inicie 'Avaya one-X® Communicator' para continuar...", font=("Segoe UI", 11))
        self.lbl.pack()
        
        self.prog = ctk.CTkProgressBar(self, orientation="horizontal", width=300)
        self.prog.pack(pady=20)
        self.prog.start()
        
        self.check_loop()

    def check_loop(self):
        if esta_corriendo_avaya():
            self.quit() # Detiene el mainloop de forma segura
        else:
            self.after(2000, self.check_loop)

class SistemaHorizontes(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Definir ruta base para buscar soporte y base de datos
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        # 1. Verificar dependencias antes de iniciar
        self.verificar_dependencias()
        
        # Ruta dinámica del icono
        self.icon_path = resource_path("logo_amp.ico")
        self.setup_window()
        
        # ... resto del init ...
        self.motor_activo = True
        self.ventana_abierta = False
        self.db = Database()
        
        self.build_panel()
        self.arrancar_motores()
        self.protocol("WM_DELETE_WINDOW", self.mandar_al_tray)

    def verificar_dependencias(self):
        """ Revisa si Tesseract está instalado (buscando en rutas de 32 y 64 bits) """
        import tkinter.messagebox as msg
        rutas_tesseract = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        ]
        
        tesseract_bin = next((path for path in rutas_tesseract if os.path.exists(path)), None)
        
        if tesseract_bin:
            # Actualizar la ruta global para asegurar que el OCR use la correcta
            pytesseract.pytesseract.tesseract_cmd = tesseract_bin
            print(f"[DEBUG] Tesseract configurado en: {tesseract_bin}")
        else:
            # Detectamos arquitectura para ofrecer el instalador correcto
            import platform
            es_64bits = platform.machine().endswith('64')
            
            # Nombre del instalador (ajustamos según disponibilidad en tu carpeta support)
            installer_name = "tesseract-ocr-w64-setup-5.5.0.20241111.exe" if es_64bits else "tesseract-ocr-w32-setup-5.5.0.20241111.exe"
            
            ruta_soporte = os.path.join(self.base_dir, "support", installer_name)
            ruta_fija = os.path.join(r"C:\xampp\htdocs\Fintech_IA\support", installer_name)
            
            installer_path = ruta_soporte if os.path.exists(ruta_soporte) else (ruta_fija if os.path.exists(ruta_fija) else None)

            if installer_path:
                resp = msg.askyesno("Dependencia Faltante", 
                                   f"No se detectó Tesseract (Sistema {'64' if es_64bits else '32'} bits).\n\n¿Desea iniciar el instalador automáticamente?")
                if resp:
                    try:
                        os.startfile(installer_path)
                        msg.showinfo("Instalación", "Complete la instalación y reinicie la aplicación.")
                        os._exit(0)
                    except Exception as e:
                        msg.showerror("Error", f"No se pudo ejecutar el instalador: {e}")
            else:
                msg.showwarning("Error Crítico", "Tesseract no instalado y no se encontró instalador en 'support'.")

    def setup_window(self):
        self.title("Horizontes AI - Terminal")
        
        # --- POSICIONAMIENTO TOP-RIGHT ---
        ancho_v = 340
        alto_v = 280
        ancho_p = self.winfo_screenwidth()
        pos_x = ancho_p - ancho_v - 20
        pos_y = 20
        self.geometry(f"{ancho_v}x{alto_v}+{pos_x}+{pos_y}")
        
        self.resizable(False, False)
        
        if os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
                img = Image.open(self.icon_path)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.wm_iconphoto(False, self.icon_photo)
                self.after(250, lambda: self.iconbitmap(self.icon_path))
            except: pass

    def build_panel(self):
        ctk.CTkLabel(self, text="SEGUROS HORIZONTES AI", font=("Segoe UI", 18, "bold"), text_color="#3b82f6").pack(pady=20)
        self.lbl_status = ctk.CTkLabel(self, text="● ASISTENTE ESCANEANDO", text_color="#10b981", font=("Segoe UI", 12, "bold"))
        self.lbl_status.pack()
        self.btn_toggle = ctk.CTkButton(self, text="⏸ PAUSAR ESCANEO", fg_color="#ef4444", hover_color="#dc2626", 
                                        font=("Segoe UI", 12, "bold"), command=self.toggle_scanner)
        self.btn_toggle.pack(pady=25, padx=50, fill="x")
        ctk.CTkLabel(self, text="Asistente de identificación v3.0", font=("Segoe UI", 9), text_color="#4b5563").pack()

    def toggle_scanner(self):
        self.motor_activo = not self.motor_activo
        if self.motor_activo:
            self.lbl_status.configure(text="● ASISTENTE ESCANEANDO", text_color="#10b981")
            self.btn_toggle.configure(text="⏸ PAUSAR ESCANEO", fg_color="#ef4444")
        else:
            self.lbl_status.configure(text="○ ASISTENTE EN PAUSA", text_color="#ef4444")
            self.btn_toggle.configure(text="▶ REANUDAR ESCANEO", fg_color="#3b82f6")

    def arrancar_motores(self):
        t = threading.Thread(target=self.bucle_principal, daemon=True)
        t.start()

    def bucle_principal(self):
        while True:
            # Sincronización con Avaya (Omitimos el cierre forzoso para permitir pruebas globales)
            if not esta_corriendo_avaya():
                 pass # El sistema sigue funcionando aunque Avaya esté cerrado

            if self.motor_activo and not self.ventana_abierta:
                try:
                    # ESCANEO DE PANTALLA COMPLETA
                    print("[DEBUG] Escaneando pantalla en busca de números...")
                    captura = pyautogui.screenshot()
                    
                    # MEJORA DE IMAGEN: Aumentar contraste y pasar a escala de grises para OCR nítido
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(captura)
                    captura_procesada = enhancer.enhance(2.0).convert('L')
                    
                    # PSM 11 es óptimo para buscar texto disperso en una imagen grande
                    texto = pytesseract.image_to_string(captura_procesada, config='--psm 11')
                    
                    # LOG DE DEPURACIÓN: Ver qué está leyendo el sistema en tu consola
                    if texto.strip():
                        print(f"[OCR] Texto detectado (primeros 40 caracteres): {texto.strip()[:40]}...")
                    
                    # REGEX FLEXIBLE: Sin límites estrictos (\b) para evitar fallos por caracteres adyacentes
                    regex_vzla = r'(412|414|424|416|426|212|24[1-69]|251|26[123567]|27[46]|235|28[568])[-.\s]*(\d{3})[-.\s]*(\d{4})'
                    search = re.search(regex_vzla, texto)
                    
                    if search and not self.ventana_abierta:
                        bruto = search.group(0)
                        num_limpio = "".join(filter(str.isdigit, bruto))
                        
                        if not num_limpio.startswith("0"):
                            tel_full = "0" + num_limpio
                        else:
                            tel_full = num_limpio
                            
                        # Guard de seguridad extra: Si ya estamos procesando, ignoramos
                        if not self.ventana_abierta:
                            print(f"✅ ¡DETECTADO!: {tel_full}")
                            self.after(0, lambda t=tel_full: self.evaluar_contacto(t))
                            # Esperamos un poco más tras una detección positiva para no saturar
                            time.sleep(2)
                            
                except Exception as e:
                    print(f"Error OCR: {e}")
            
            time.sleep(1.5)

    def evaluar_contacto(self, tel):
        if self.ventana_abierta:
            return
        self.ventana_abierta = True
        print(f"[DEBUG] Iniciando gestión para {tel}")
        
        try:
            conn = self.db.get_connection()
            # row_factory en database.py ya maneja el formato de diccionario
            res = conn.execute("SELECT * FROM registros WHERE telefono = ?", (tel,)).fetchone()
            cliente = dict(res) if res else None
            self.lanzar_notificacion(cliente, tel)
            conn.close()
        except Exception as e:
            print(f"Error DB: {e}")
            self.ventana_abierta = False

    def lanzar_notificacion(self, cliente, tel):
        notif = ctk.CTkToplevel(self)
        notif.title("Identificación Horizontes")
        
        # --- POSICIONAMIENTO TOP-RIGHT ---
        ancho_v = 380
        alto_v = 420
        ancho_p = self.winfo_screenwidth()
        pos_x = ancho_p - ancho_v - 20
        pos_y = 20
        notif.geometry(f"{ancho_v}x{alto_v}+{pos_x}+{pos_y}")
        
        notif.attributes("-topmost", True)
        notif.resizable(False, False)
        
        if os.path.exists(self.icon_path):
            try:
                notif.iconbitmap(self.icon_path)
                notif.after(300, lambda: notif.iconbitmap(self.icon_path))
            except: pass

        nombre = cliente['nombre'] if cliente else "NUEVO CONTACTO"

        ctk.CTkLabel(notif, text="IDENTIFICACIÓN IA", font=("Segoe UI", 10, "bold"), text_color="gray").pack(pady=(20,0))
        ctk.CTkLabel(notif, text=nombre, font=("Segoe UI", 20, "bold"), text_color="#3b82f6").pack(pady=10)
        ctk.CTkLabel(notif, text=f"TELÉFONO: {tel}", font=("Courier", 12)).pack(pady=(0, 15))

        if not cliente:
            ctk.CTkLabel(notif, text="Este contacto no existe en la base de datos.", font=("Arial", 10), text_color="#9ca3af").pack()
            e_nom = ctk.CTkEntry(notif, placeholder_text="Nombre Completo", width=250)
            e_nom.pack(pady=5)
            e_ced = ctk.CTkEntry(notif, placeholder_text="Cédula / RIF", width=250)
            e_ced.pack(pady=5)
            
            def guardar():
                if e_nom.get() and e_ced.get():
                    if self.db.guardar_asegurado(e_nom.get(), e_ced.get(), tel):
                        notif.destroy()
                        # La bandera ventana_abierta sigue en True hasta que se cierre el mensaje de éxito
                        self.mostrar_mensaje_exito("Registro guardado exitosamente.")
            
            ctk.CTkButton(notif, text="💾 GUARDAR REGISTRO", fg_color="#10b981", command=guardar).pack(pady=15, padx=50, fill="x")
        else:
            if tel.startswith("021"):
                ctk.CTkButton(notif, text="🏥 GESTIÓN MÉDICA (CLÍNICA)", fg_color="#3b82f6", 
                              command=lambda: self.abrir_panel_estudios(tel, notif)).pack(pady=10, padx=50, fill="x")
            else:
                ctk.CTkLabel(notif, text="Llamada móvil - Panel médico restringido.", font=("Arial", 9), text_color="gray").pack(pady=5)

        ctk.CTkButton(notif, text="FINALIZAR ASISTENCIA", fg_color="transparent", border_width=1, 
                      command=lambda: self.cerrar_pop(notif)).pack(pady=10, padx=50, fill="x")

        notif.protocol("WM_DELETE_WINDOW", lambda: self.cerrar_pop(notif))

    def mostrar_mensaje_exito(self, mensaje):
        self.ventana_abierta = True
        pop = ctk.CTkToplevel(self)
        pop.title("Operación Exitosa")
        pop.geometry("320x180")
        pop.attributes("-topmost", True)
        
        def cerrar_exito():
            pop.destroy()
            self.ventana_abierta = False

        if os.path.exists(self.icon_path):
            try: pop.iconbitmap(self.icon_path)
            except: pass
        ctk.CTkLabel(pop, text="✅", font=("Arial", 35)).pack(pady=(20, 5))
        ctk.CTkLabel(pop, text=mensaje, font=("Segoe UI", 12, "bold")).pack(pady=5)
        ctk.CTkButton(pop, text="ACEPTAR", width=120, fg_color="#1e3a8a", command=cerrar_exito).pack(pady=15)
        pop.protocol("WM_DELETE_WINDOW", cerrar_exito)

    def abrir_panel_estudios(self, tel, v_notif):
        self.ventana_abierta = True 
        from gestion_estudios import abrir_ventana_escaneo
        v_notif.destroy()
        v_med = abrir_ventana_escaneo(tel)
        self.wait_window(v_med)
        self.ventana_abierta = False

    def cerrar_pop(self, win):
        win.destroy()
        self.ventana_abierta = False

    def mandar_al_tray(self):
        self.withdraw()
        threading.Thread(target=self.init_system_tray, daemon=True).start()

    def init_system_tray(self):
        img = Image.open(self.icon_path) if os.path.exists(self.icon_path) else Image.new('RGB', (64, 64), color='blue')
        def restore():
            self.tray.stop()
            self.deiconify()
        self.tray = pystray.Icon("Horizontes", img, "Fintech Horizonte", menu=pystray.Menu(
            pystray.MenuItem("Abrir Terminal", restore),
            pystray.MenuItem("Finalizar Todo", lambda: os._exit(0))
        ))
        self.tray.run()

if __name__ == "__main__":
    # Si Avaya NO está corriendo, mostramos la pantalla de espera
    if not esta_corriendo_avaya():
        splash = EsperarAvaya()
        try:
            splash.mainloop()
        finally:
            try: splash.destroy()
            except: pass
    
    # Si llegamos aquí y Avaya está activo, arrancamos Fintech
    if esta_corriendo_avaya():
        app = SistemaHorizontes()
        app.mainloop()
