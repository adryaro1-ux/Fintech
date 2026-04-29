import os
import sys
import pandas as pd
import glob

class PriceManager:
    def __init__(self, folder_path=r"C:\xampp\htdocs\FintechIA\estudios"):
        # Priorizar la ruta donde está el ejecutable/script
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.local_estudios = os.path.join(base_dir, "estudios")
        
        # Intentamos varias rutas posibles basadas en la estructura del usuario
        posibles_rutas = [
            self.local_estudios, 
            folder_path, 
            r"C:\xampp\htdocs\FintechIA\estudios",
            r"C:\xampp\htdocs\Fintech_IA\estudios"
        ]
        self.folder_path = next((p for p in posibles_rutas if os.path.exists(p)), self.local_estudios)
        
        print(f"[DEBUG] Usando carpeta de estudios: {self.folder_path}")
        self.prices = {} # {id_normalizado: {nombre_estudio: precio}}
        self.load_all_prices()
    def load_all_prices(self):
        if not os.path.exists(self.folder_path):
            print(f"[ERROR] No se pudo encontrar la carpeta de estudios en: {self.folder_path}")
            return

        files = [f for f in glob.glob(os.path.join(self.folder_path, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
        print(f"[DEBUG] Buscando en: {self.folder_path}")
        print(f"[DEBUG] Archivos Excel válidos encontrados: {len(files)}")
        
        for file in files:
            try:
                file_name = os.path.splitext(os.path.basename(file))[0]
                # Guardamos la versión limpia (solo números) y la original
                id_limpio = "".join(filter(str.isdigit, file_name))
                ids_a_registrar = [id_limpio, file_name.lower()]
                
                print(f"[DEBUG] -> Cargando: {file_name} (ID: {id_limpio})")
                
                dict_precios_clinica = {}
                excel_obj = pd.ExcelFile(file)
                
                for sheet_name in excel_obj.sheet_names:
                    # Leemos un bloque generoso para buscar la cabecera (incrementado a 100)
                    df_temp = pd.read_excel(file, sheet_name=sheet_name, nrows=100, header=None)
                    
                    header_row = -1
                    col_estudio = -1
                    col_precio = -1
                    
                    for i, row in df_temp.iterrows():
                        row_str = [str(val).lower() for val in row.values]
                        # Palabras clave más amplias para servicios y precios
                        contains_study = any(k in " ".join(row_str) for k in ['consultas', 'estudio', 'descripcion', 'servicio', 'especialidad', 'identificado', 'concepto', 'estudios'])
                        contains_price = any(k in " ".join(row_str) for k in ['baremo', 'precio', 'monto', 'referencia', '$', 'sh', 's.h', 'convenio'])
                        
                        if contains_study and contains_price:
                            header_row = i
                            for idx, val in enumerate(row_str):
                                v = val.strip()
                                # Priorizar 'consultas' o 'estudio' sobre 'especialidad'
                                if any(k in v for k in ['consultas', 'estudio', 'descripcion', 'identificado', 'estudios']): 
                                    col_estudio = idx
                                elif col_estudio == -1 and 'especialidad' in v:
                                    col_estudio = idx
                                
                                # Prioridad para precio: Preferimos 'referencia' o 'precio' 
                                if any(k in v for k in ['baremo', 'precio', 'referencia', 'monto', '$', 'convenio']):
                                    # Intentamos evitar columnas secundarias si ya tenemos una principal
                                    if col_precio == -1 or any(p in v for p in ['monto', 'precio', '$']):
                                        col_precio = idx
                            
                            if col_estudio != -1 and col_precio != -1:
                                print(f"[DEBUG]   -> Cabecera encontrada en fila {i}: Col Estudio={col_estudio}, Col Precio={col_precio}")
                                break
                    
                    if header_row != -1 and col_estudio != -1 and col_precio != -1:
                        # Leemos los datos a partir del encabezado
                        df = pd.read_excel(file, sheet_name=sheet_name, skiprows=header_row + 1, header=None)
                        
                        cont_sheet = 0
                        for _, row in df.iterrows():
                            try:
                                if col_estudio >= len(row) or col_precio >= len(row): continue
                                
                                nombre = str(row[col_estudio]).lower().strip()
                                # Filtros para omitir basura
                                if nombre in ['nan', '', 'total', 'subtotal', 'none', 'perfiles', 'aps', 'especialidad', 'especialidades'] or len(nombre) < 3: continue
                                
                                p_val = row[col_precio]
                                if pd.isna(p_val) or str(p_val).lower() == 'nan': continue
                                
                                if isinstance(p_val, (int, float)):
                                    price = float(p_val)
                                else:
                                    # Limpiar moneda y espacios
                                    p_raw = str(p_val).replace('$', '').replace('USD', '').replace(' ', '').strip()
                                    if not p_raw or any(c.isalpha() for c in p_raw if c not in '.,'): continue
                                    
                                    # Normalizar coma decimal
                                    if ',' in p_raw and '.' not in p_raw: p_raw = p_raw.replace(',', '.')
                                    elif ',' in p_raw and '.' in p_raw: p_raw = p_raw.replace('.', '').replace(',', '.')
                                    
                                    # Solo dejar dígitos y el punto decimal
                                    p_raw = "".join(c for c in p_raw if c.isdigit() or c == '.')
                                    if not p_raw: continue
                                    price = float(p_raw)
                                
                                dict_precios_clinica[nombre] = price
                                cont_sheet += 1
                            except: continue
                        if cont_sheet > 0:
                            print(f"[DEBUG]   -> Hoja '{sheet_name}': {cont_sheet} precios cargados.")
                
                if dict_precios_clinica:
                    for id_reg in ids_a_registrar:
                        if id_reg: self.prices[id_reg] = dict_precios_clinica
                    print(f"[SUCCESS] {file_name}: {len(dict_precios_clinica)} precios vinculados.")
                else:
                    print(f"[DEBUG]    ⚠️ No se encontraron datos válidos en {file_name}")
            except Exception as e:
                print(f"[ERROR] Error cargando {file}: {e}")

    def obtener_precio(self, clinica_id, nombre_detectado):
        print(f"[PRICE_DEBUG] obtener_precio RECIBIÓ clinica_id='{clinica_id}'")
        if not clinica_id or clinica_id == "0000": 
            print("[PRICE_DEBUG] ⚠️ clinica_id no válido o por defecto.")
            # Intentamos ver si hay una clínica 'general' para no retornar 0 por defecto si hay algo
            clinica_data = self.prices.get('general')
            if not clinica_data: return 0.0
        
        id_str = str(clinica_id).lower().strip()
        id_num = "".join(filter(str.isdigit, id_str))
        
        # Intentamos buscar los datos de esta clínica
        clinica_data = self.prices.get(id_num) or self.prices.get(id_str) or self.prices.get('general')
        
        if not clinica_data:
            print(f"[PRICE_DEBUG] ❌ No hay datos cargados para la clínica {id_num}. Clínicas disponibles: {list(self.prices.keys())}")
            return 0.0

        nombre_clean = str(nombre_detectado).lower().strip()
        print(f"[PRICE_DEBUG] Buscando '{nombre_clean}' en Clínica {id_num} ({len(clinica_data)} precios)...")
        
        # 1. Coincidencia exacta
        if nombre_clean in clinica_data:
            p = clinica_data[nombre_clean]
            print(f"[PRICE_DEBUG] ✅ Encontrado (Exacto): {nombre_clean} -> ${p}")
            return p
            
        # 2. Coincidencia parcial (el nombre del Excel está contenido en lo detectado o viceversa)
        for estudio_excel, p in clinica_data.items():
            if estudio_excel in nombre_clean or nombre_clean in estudio_excel:
                print(f"[PRICE_DEBUG] ✅ Encontrado (Parcial): '{estudio_excel}' matched with '{nombre_clean}' -> ${p}")
                return p
        
        print(f"[PRICE_DEBUG] ⚠️ No se encontró '{nombre_clean}'. Usando precio base $0.")
        return 0.0
