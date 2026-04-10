# 🛡️ Asistencia Predictiva - Seguros Horizonte (AMP)

Sistema inteligente de soporte al cliente diseñado para el departamento de **Atención Médica Primaria (AMP)**. Esta herramienta utiliza **IA y Reconocimiento Óptico de Caracteres (OCR)** para monitorear la pantalla de **Avaya Workspace**, identificar números telefónicos de asegurados entrantes y mostrar automáticamente su estatus de póliza en una interfaz con estilo Cyberpunk.

## 🚀 Requisitos del Sistema

### 1. Dependencias Externas
Es obligatorio instalar el motor de Tesseract OCR en el sistema operativo para que la lectura de pantalla funcione:
* **Tesseract OCR**: [Descargar aquí](https://github.com/UB-Mannheim/tesseract/wiki).
* **Ruta de instalación**: El script busca el ejecutable en `C:\Program Files\Tesseract-OCR\tesseract.exe`. Si lo instalas en otra ruta, modifícalo en la sección de configuración del código.

### 2. Base de Datos
El sistema requiere una base de datos MySQL (XAMPP/WAMP) con las siguientes especificaciones:
* **Nombre de la DB**: `fintech_horizontes`
* **Tabla**: `asegurados`
* **Columnas**: `nombre`, `cedula`, `telefono`, `estatus_pago`

## 📦 Instalación
Clona este repositorio o descarga los archivos y ejecuta el siguiente comando para instalar las librerías necesarias:

```bash
pip install pytesseract mysql-connector-python pyautogui customtkinter Pillow
