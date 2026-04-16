import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from escaner import EscanerEstudios
from PIL import Image, ImageTk  # Importación vital para el icono
import os

class AplicacionEstudios:
    def __init__(self, ventana_hija, telefono_clinica="0000"):
        self.root = ventana_hija
        self.clinica_actual = telefono_clinica 
        
        # --- CONFIGURACIÓN DE ICONO CON PILLOW (Solución Definitiva) ---
        icon_path = r"C:\xampp\htdocs\Fintech\logo_amp.ico"
        try:
            if os.path.exists(icon_path):
                # Abrimos con PIL para asegurar compatibilidad total
                img_pil = Image.open(icon_path)
                self.root.icon_img = ImageTk.PhotoImage(img_pil)
                # Aplicamos a la ventana y forzamos herencia a sub-ventanas con True
                self.root.iconphoto(True, self.root.icon_img)
                print("✅ Icono del Panel de Gestión cargado con Pillow.")
            else:
                print(f"❌ No se encontró el icono en: {icon_path}")
        except Exception as e:
            print(f"⚠️ Error al cargar el icono: {e}")

        # Configuración de ventana
        self.root.title(f"GESTIÓN DE ESTUDIOS - EMISOR: {self.clinica_actual}")
        self.root.geometry("1200x750")
        self.root.configure(bg='#f0f2f5')
        
        self.colores = {
            'primary': '#2c7da0',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'text': '#2c3e50',
            'bg': '#f0f2f5'
        }
        
        self.db = Database() 
        self.escaner = EscanerEstudios()
        
        self.configurar_estilos()
        self.crear_interfaz()
        self.cargar_estudios()

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Treeview", 
                        background="white", 
                        foreground="#2c3e50", 
                        rowheight=35, 
                        fieldbackground="white",
                        font=('Segoe UI', 10))
        style.configure("Custom.Treeview.Heading", 
                        background="#2c7da0", 
                        foreground="white", 
                        font=('Segoe UI', 10, 'bold'))
        style.map("Custom.Treeview", background=[('selected', '#3498db')])

    def crear_interfaz(self):
        main_frame = tk.Frame(self.root, bg=self.colores['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(main_frame, bg=self.colores['primary'], height=70)
        header.pack(fill=tk.X, pady=(0, 20))
        tk.Label(header, text="🏥 PANEL DE LIQUIDACIÓN DE ESTUDIOS", 
                 font=('Segoe UI', 16, 'bold'), bg=self.colores['primary'], fg='white').pack(pady=15)

        # Cuerpo
        cuerpo = tk.Frame(main_frame, bg=self.colores['bg'])
        cuerpo.pack(fill=tk.BOTH, expand=True)

        # --- SECCIÓN TABLA ---
        tabla_frame = tk.Frame(cuerpo, bg='white', bd=1)
        tabla_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        columnas = ('id', 'estudio', 'clinica', 'precio', 'fecha')
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show='headings', style="Custom.Treeview")
        
        self.tree.heading('id', text='ID')
        self.tree.heading('estudio', text='ESTUDIO MÉDICO')
        self.tree.heading('clinica', text='CLÍNICA SOLICITANTE')
        self.tree.heading('precio', text='PRECIO (USD)')
        self.tree.heading('fecha', text='REGISTRO')
        
        self.tree.column('id', width=40, anchor=tk.CENTER)
        self.tree.column('estudio', width=300)
        self.tree.column('clinica', width=200)
        self.tree.column('precio', width=100, anchor=tk.E)
        self.tree.column('fecha', width=150, anchor=tk.CENTER)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(cuerpo, bg=self.colores['bg'], width=280)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Resumen
        resumen = tk.Frame(sidebar, bg='white', bd=1, pady=15)
        resumen.pack(fill=tk.X, pady=(0, 15))
        self.lbl_total = tk.Label(resumen, text="$0.00", font=('Segoe UI', 20, 'bold'), 
                                  bg='white', fg=self.colores['success'])
        self.lbl_total.pack()
        self.lbl_conteo = tk.Label(resumen, text="0 estudios", bg='white', fg=self.colores['text'])
        self.lbl_conteo.pack()

        # Botones
        tk.Button(sidebar, text="🔍 ESCANEAR PANTALLA", bg=self.colores['primary'], fg='white', 
                  font=('Segoe UI', 10, 'bold'), height=2, command=self.escanear).pack(fill=tk.X, pady=5)
        
        tk.Button(sidebar, text="🗑️ ELIMINAR SELECCIÓN", bg='white', fg=self.colores['danger'], 
                  command=self.eliminar).pack(fill=tk.X, pady=5)
        
        tk.Button(sidebar, text="📄 EXPORTAR CSV", bg='white', fg=self.colores['success'], 
                  command=self.exportar).pack(fill=tk.X, pady=5)

    def cargar_estudios(self):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
            
        estudios = self.db.obtener_estudios()
        for est in estudios:
            # est[0]=ID, est[1]=Nombre, est[2]=Clínica, est[3]=Precio, est[4]=Fecha
            self.tree.insert('', tk.END, values=(
                est[0], 
                est[1], 
                est[2], 
                f"${est[3]:.2f}", 
                est[4]
            ))
        self.actualizar_totales()

    def escanear(self):
        res = self.escaner.escanear_lado_derecho()
        if res:
            for e in res:
                if not self.db.estudio_existe(e['nombre']):
                    self.db.agregar_estudio(e['nombre'], e['precio'], self.clinica_actual)
            self.cargar_estudios()
        else:
            messagebox.showinfo("IA", "No se detectaron estudios en la zona derecha.")

    def actualizar_totales(self):
        total = 0
        items = self.tree.get_children()
        for item in items:
            valor_str = str(self.tree.item(item)['values'][3]).replace('$', '')
            total += float(valor_str)
        self.lbl_total.configure(text=f"${total:.2f}")
        self.lbl_conteo.configure(text=f"{len(items)} estudios registrados")

    def eliminar(self):
        seleccion = self.tree.selection()
        if not seleccion: return
        if messagebox.askyesno("Confirmar", "¿Eliminar estudios seleccionados?"):
            for item in seleccion:
                id_estudio = self.tree.item(item)['values'][0]
                self.db.eliminar_estudio(id_estudio)
            self.cargar_estudios()

    def exportar(self):
        messagebox.showinfo("Exportar", "Datos exportados correctamente.")

def abrir_ventana_escaneo(telefono_clinica="0000"):
    ventana_hija = tk.Toplevel()
    app = AplicacionEstudios(ventana_hija, telefono_clinica)