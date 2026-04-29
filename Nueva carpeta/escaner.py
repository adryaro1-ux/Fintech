import mss
import cv2
import numpy as np
import pytesseract
import re
from PIL import Image
import os
from price_manager import PriceManager

# Configuración de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class EscanerEstudios:
    def __init__(self):
        self.precios_referencia = {
            'autoinmune': 255.0, 'autoinmunidad': 285.0, 'autocuidado': 185.0,
            'automedicion': 155.0, 'autodiagnostico': 205.0, 'autocontrol': 175.0
        }
        self.precio_general = 0.0
        # Cargamos el gestor de precios de Excel
        self.price_manager = PriceManager()
    
    def capturar_y_leer(self, region_derecha=True):
        """Captura y procesa la imagen para extraer texto limpio"""
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            # Si region_derecha es True, solo escaneamos el 50% derecho (ahorra CPU)
            region = {
                'left': int(monitor['width'] * 0.5) if region_derecha else 0,
                'top': 0,
                'width': int(monitor['width'] * 0.5) if region_derecha else monitor['width'],
                'height': monitor['height']
            }
            
            sct_img = sct.grab(region)
            img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Pre-procesamiento: Gris -> Umbral -> Inversión (mejora OCR en Avaya)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            return pytesseract.image_to_string(thresh, lang='spa+eng')

    def escanear_estudios(self, clinica_id="0000"):
        """Busca patrones de estudios médicos y asigna precios según la clínica"""
        texto = self.capturar_y_leer(region_derecha=True)
        lineas = texto.split('\n')
        resultados = []
        
        for linea in lineas:
            linea_clean = linea.lower().strip()
            # Patrón flexible para "se auto", "5e auto", "se aut0"
            if re.search(r'[se5]e\s+aut[o0]', linea_clean):
                match = re.search(r'aut[o0]\s*(.*?)(?:\d|$)', linea_clean)
                if match:
                    nombre = match.group(1).strip()
                    if len(nombre) > 3:
                        # Buscamos el precio dinámico en los archivos Excel
                        precio_final = self.price_manager.obtener_precio(clinica_id, nombre)
                        
                        resultados.append({
                            'nombre': nombre.capitalize(),
                            'precio': precio_final
                        })
        return resultados
