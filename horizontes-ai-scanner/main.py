import pytesseract
import mysql.connector
import pyautogui
import customtkinter as ctk
import os
import pystray
import re
from PIL import Image, ImageTk
import threading
import sys
import ctypes
from database import Database

# --- IDENTIDAD DE APP PARA WINDOWS ---
try:
    myappid = 'seguros.horizontes.scanner.ai.v3' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except: pass

# --- CONFIGURACIÓN TESSERACT ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
ctk.set_appearance_mode("dark")

class SistemaHorizontes(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.icon_path = r"C:\xampp\htdocs\horizontes-ai-scanner\logo_amp.ico"
        self.setup_window()
        
        self.motor_activo = True
        self.ventana_abierta = False
        self.db = Database()
        
        self.build_panel()
        self.arrancar_motores()
        self.protocol("WM_DELETE_WINDOW", self.mandar_al_tray)

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
            if self.motor_activo and not self.ventana_abierta:
                try:
                    # Escaneamos casi toda la mitad superior para no fallar
                    captura = pyautogui.screenshot(region=(0,0, 1400, 700))
                    # Usamos PSM 3 (Auto) que es más robusto para capturas de pantalla
                    texto = pytesseract.image_to_string(captura, config='--psm 3')
                    
                    # PATRÓN ULTRA-FLEXIBLE: Busca 10 números que empiecen por 4 o 212
                    # Detecta: 412-999-8877, 4129998877, 412 999 8877, etc.
                    search = re.search(r'(4\d{2}|212)[-\s.]?\d{3}[-\s.]?\d{4}', texto)
                    
                    if search:
                        match_str = search.group(0)
                        # Limpiamos y normalizamos
                        num_limpio = "".join(filter(str.isdigit, match_str))
                        tel_final = "0" + num_limpio
                        
                        if len(tel_final) == 11:
                            self.after(0, lambda t=tel_final: self.evaluar_contacto(t))
                            
                except Exception as e:
                    print(f"Error OCR: {e}")
            
            import time
            time.sleep(2.0)

    def evaluar_contacto(self, tel):
        if self.ventana_abierta: return
        self.ventana_abierta = True
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM asegurados WHERE telefono = %s", (tel,))
            cliente = cursor.fetchone()
            self.lanzar_notificacion(cliente, tel)
        except Exception as e:
            print(f"Error DB: {e}")
            self.ventana_abierta = False # IMPORTANTE: Liberamos el estado si hay error

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
        status_txt = cliente['estatus_pago'] if cliente else "SIN REGISTRO"
        color_status = "#F1C40F" if not cliente else ("#00ff88" if cliente['estatus_pago'] == "Al día" else "#ff4444")

        ctk.CTkLabel(notif, text="IDENTIFICACIÓN IA", font=("Segoe UI", 10, "bold"), text_color="gray").pack(pady=(20,0))
        ctk.CTkLabel(notif, text=nombre, font=("Segoe UI", 20, "bold"), text_color="#3b82f6").pack(pady=10)
        ctk.CTkLabel(notif, text=f"TELÉFONO: {tel}", font=("Courier", 12)).pack()
        
        chip = ctk.CTkFrame(notif, fg_color="transparent", border_width=2, border_color=color_status, corner_radius=10)
        chip.pack(pady=15, padx=50, fill="x")
        ctk.CTkLabel(chip, text=status_txt.upper(), font=("Arial", 14, "bold"), text_color=color_status).pack(pady=5)

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
                        self.ventana_abierta = False
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
        pop = ctk.CTkToplevel(self)
        pop.title("Operación Exitosa")
        pop.geometry("320x180")
        pop.attributes("-topmost", True)
        if os.path.exists(self.icon_path):
            try: pop.iconbitmap(self.icon_path)
            except: pass
        ctk.CTkLabel(pop, text="✅", font=("Arial", 35)).pack(pady=(20, 5))
        ctk.CTkLabel(pop, text=mensaje, font=("Segoe UI", 12, "bold")).pack(pady=5)
        ctk.CTkButton(pop, text="ACEPTAR", width=120, fg_color="#1e3a8a", command=pop.destroy).pack(pady=15)

    def abrir_panel_estudios(self, tel, v_notif):
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
    app = SistemaHorizontes()
    app.mainloop()
