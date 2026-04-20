import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from escaner import EscanerEstudios
import os

class AplicacionEstudios:
    def __init__(self, ventana, telefono_clinica="0000"):
        self.root = ventana
        self.clinica_actual = telefono_clinica
        self.db = Database()
        self.escaner = EscanerEstudios()
        
        # Ruta Actualizada del Icono
        self.icon_path = r"C:\xampp\htdocs\horizontes-ai-scanner\logo_amp.ico"
        
        self.root.title(f"PANEL DE ESTUDIOS - EMISOR: {self.clinica_actual}")
        self.root.geometry("1220x720") # Aumentado para dar espacio al sidebar
        self.root.configure(bg='#f4f7f9')
        
        if os.path.exists(self.icon_path):
            try: 
                self.root.iconbitmap(self.icon_path)
                # Forzar después del renderizado inicial para evitar que se pierda
                self.root.after(250, lambda: self.root.iconbitmap(self.icon_path))
            except: pass

        self.setup_styles()
        self.build_ui()
        self.refrescar_tabla()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                        background="#ffffff", 
                        foreground="#333333",
                        rowheight=40,
                        fieldbackground="#ffffff",
                        font=('Segoe UI', 10))
        style.configure("Treeview.Heading", 
                        background="#1e3a8a", 
                        foreground="white", 
                        relief="flat",
                        font=('Segoe UI', 10, 'bold'))
        style.map("Treeview", background=[('selected', '#3b82f6')])

    def build_ui(self):
        # Top Bar
        header = tk.Frame(self.root, bg="#1e3a8a", height=65)
        header.pack(fill=tk.X)
        tk.Label(header, text="🛡️ LIQUIDACIÓN DE SERVICIOS MÉDICOS - HORIZONTES", 
                 font=('Segoe UI', 13, 'bold'), bg="#1e3a8a", fg='white').pack(pady=18)

        # Contenedor Principal (Cuerpo)
        body = tk.Frame(self.root, bg='#f4f7f9')
        body.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # --- PANEL LATERAL (SIDEBAR) ---
        # Lo empaquetamos PRIMERO a la derecha para que conserve su espacio fijo
        sidebar = tk.Frame(body, bg='#f4f7f9', width=280)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(25, 0))
        sidebar.pack_propagate(False)

        # Card de Totales
        card = tk.Frame(sidebar, bg='white', padx=20, pady=25, highlightthickness=1, highlightbackground='#e5e7eb')
        card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(card, text="TOTAL ACUMULADO", font=('Segoe UI', 9, 'bold'), bg='white', fg='#4b5563').pack()
        self.lbl_total = tk.Label(card, text="$0.00", font=('Segoe UI', 26, 'bold'), bg='white', fg='#059669')
        self.lbl_total.pack(pady=10)
        
        tk.Frame(card, height=1, bg='#f3f4f6').pack(fill=tk.X, pady=10)
        
        self.lbl_count = tk.Label(card, text="0 registros", font=('Segoe UI', 10), bg='white', fg='#6b7280')
        self.lbl_count.pack()

        # Botones de Acción
        btn_scan = tk.Button(sidebar, text="🔍 INICIAR ESCANEO AI", bg="#3b82f6", fg="white", 
                             font=('Segoe UI', 10, 'bold'), cursor="hand2", relief="flat",
                             activebackground="#2563eb", activeforeground="white",
                             command=self.ejecutar_escaneo)
        btn_scan.pack(fill=tk.X, pady=10, ipady=12)
        
        btn_del = tk.Button(sidebar, text="🗑️ ELIMINAR SELECCIÓN", bg="#ffffff", fg="#ef4444", 
                             font=('Segoe UI', 10), borderwidth=1, cursor="hand2", relief="solid",
                             activebackground="#fef2f2",
                             command=self.eliminar_seleccion)
        btn_del.pack(fill=tk.X, pady=5, ipady=8)

        # --- CONTENEDOR DE TABLA ---
        # Se empaqueta DESPUÉS para que tome todo el espacio sobrante a la izquierda
        data_container = tk.Frame(body, bg='white', highlightthickness=1, highlightbackground='#e2e8f0')
        data_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Eliminamos borderwidth=0 que causaba el error
        self.tree = ttk.Treeview(data_container, columns=('id', 'estudio', 'emisor', 'precio', 'fecha'), 
                                show='headings', selectmode='browse')
        
        cols = {
            'id': ('ID', 50),
            'estudio': ('SERVICIO IDENTIFICADO', 320),
            'emisor': ('EMISOR / CLÍNICA', 180),
            'precio': ('PRECIO (USD)', 110),
            'fecha': ('FECHA REGISTRO', 170)
        }
        
        for cid, (name, width) in cols.items():
            self.tree.heading(cid, text=name)
            self.tree.column(cid, width=width, anchor=tk.CENTER if cid != 'estudio' else tk.W)

        # Scrollbar vertical para la tabla
        vsb = ttk.Scrollbar(data_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def refrescar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        estudios = self.db.obtener_estudios()
        total = 0
        for e in estudios:
            self.tree.insert('', tk.END, values=(e[0], e[1], e[2], f"${e[3]:.2f}", e[4]))
            total += float(e[3])
        self.lbl_total.config(text=f"${total:.2f}")
        self.lbl_count.config(text=f"{len(estudios)} archivos detectados")

    def ejecutar_escaneo(self):
        res = self.escaner.escanear_estudios()
        if res:
            for r in res:
                self.db.agregar_estudio(r['nombre'], r['precio'], self.clinica_actual)
            self.refrescar_tabla()
            messagebox.showinfo("Scanner AI", f"Operación exitosa: {len(res)} servicios médicos vinculados a la clínica.")
        else:
            messagebox.showwarning("IA", "No se detectaron servicios médicos procesables en la región activa.")

    def eliminar_seleccion(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Seguridad", "¿Desea eliminar definitivamente los registros seleccionados?"):
            for s in sel:
                self.db.eliminar_estudio(self.tree.item(s)['values'][0])
            self.refrescar_tabla()

def abrir_ventana_escaneo(telefono_clinica="0000"):
    win = tk.Toplevel()
    AplicacionEstudios(win, telefono_clinica)
    return win
