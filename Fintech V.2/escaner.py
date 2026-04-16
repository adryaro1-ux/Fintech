import mss
import mss.tools
import cv2
import numpy as np
import pytesseract
import re
from PIL import Image

# Configurar ruta de tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class EscanerEstudios:
    def __init__(self):
        # Precios de ejemplo por tipo de estudio
        self.precios_referencia = {
            'autoinmune': 250.00,
            'autoinmunidad': 280.00,
            'autocuidado': 180.00,
            'automedicion': 150.00,
            'autodiagnostico': 200.00,
            'autocontrol': 170.00,
            'autoregulacion': 220.00
        }
        
        self.precio_general = 300.00
    
    def escanear_lado_derecho(self, region_porcentaje=(0.5, 0, 0.5, 1)):
        """Escanea el lado derecho de la pantalla buscando 'se auto'"""
        with mss.mss() as sct:
            # Obtener tamaño de pantalla
            monitor = sct.monitors[1]
            ancho_total = monitor['width']
            alto_total = monitor['height']
            
            # Calcular región derecha (50% derecha de la pantalla)
            x_inicio = int(ancho_total * region_porcentaje[0])
            y_inicio = int(alto_total * region_porcentaje[1])
            ancho = int(ancho_total * region_porcentaje[2])
            alto = int(alto_total * region_porcentaje[3])
            
            # Capturar región
            region = {
                'left': x_inicio,
                'top': y_inicio,
                'width': ancho,
                'height': alto
            }
            
            screenshot = sct.grab(region)
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            # Convertir a OpenCV para mejorar calidad
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Preprocesamiento para mejor OCR
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Mejorar contraste
            enhanced = cv2.convertScaleAbs(thresh, alpha=1.5, beta=0)
            
            # OCR - Usando inglés (funciona bien con texto en español)
            texto = pytesseract.image_to_string(enhanced, lang='eng')
            
            # Buscar líneas con "se auto"
            lineas = texto.split('\n')
            resultados = []
            
            for linea in lineas:
                if re.search(r'se\s+auto', linea.lower()):
                    # Extraer nombre del estudio
                    match = re.search(r'se\s+auto\s*(.*?)(?:\d|$)', linea.lower())
                    if match:
                        nombre_estudio = match.group(1).strip()
                        if nombre_estudio:
                            precio = self.determinar_precio(nombre_estudio)
                            resultados.append({
                                'nombre': nombre_estudio.capitalize(),
                                'precio': precio,
                                'texto_original': linea
                            })
            
            return resultados
    
    def determinar_precio(self, nombre_estudio):
        """Determina el precio del estudio según palabras clave"""
        nombre_lower = nombre_estudio.lower()
        
        for key, precio in self.precios_referencia.items():
            if key in nombre_lower:
                return precio
        
        return self.precio_general

    def simular_texto_ejemplo(self):
        """Método de prueba para simular texto sin pantalla real"""
        textos_ejemplo = [
            "se autoinmune estudio de anticuerpos",
            "se autocontrol prueba de glucosa",
            "se autodiagnostico panel hormonal",
            "se autoinmunidad perfil reumatologico",
            "se autocuidado evaluacion nutricional"
        ]
        
        resultados = []
        for texto in textos_ejemplo:
            if re.search(r'se\s+auto', texto):
                match = re.search(r'se\s+auto\s*(.*)', texto)
                if match:
                    nombre = match.group(1).strip()
                    precio = self.determinar_precio(nombre)
                    resultados.append({
                        'nombre': nombre.capitalize(),
                        'precio': precio,
                        'texto_original': texto
                    })
        
        return resultados