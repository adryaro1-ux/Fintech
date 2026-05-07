# 🛡️ Asistencia Predictiva - Seguros Horizonte (AMP)

Sistema inteligente de soporte al usuario diseñado para el departamento de **Atención Médica Primaria (AMP)**. Esta herramienta utiliza **IA y Reconocimiento Óptico de Caracteres (OCR)** para monitorear la pantalla de **Avaya Workspace**, identificar números telefónicos de asegurados y clínicas entrantes, con el objetivo de mostrar automáticamente la información de la persona solicitante a un servicio o estudio médico solicitado, de manera anticipada en una interfaz con estilo **Cyberpunk**, además posee la función de escanear de manera autónoma los documentos de registros efectuados por los **Operadores del Área de Call Center**, y asi evitar la sobrecarga manual en el calculo de los montos de los antes mencionados.

## Requisitos del Sistema

### 1. Dependencias Externas:
Es obligatorio instalar el motor de Tesseract OCR en el sistema operativo para que la lectura de pantalla funcione:
* **Tesseract OCR**: [Descargar aquí](https://github.com/UB-Mannheim/tesseract/wiki).
* **Ruta de instalación**: El script busca el ejecutable en `C:\Program Files\Tesseract-OCR\tesseract.exe`. En caso de instalarse en otra ruta, modifícalo en la sección de configuración del código.
* **Registos Baremos**: Informacion en formato "xlsx" sobre los estudios y precios vinculados; y convenidos por cada clínica filial.
* **Ruta o Ubicacion de Baremos**: Ubicado dentro de la carpeta de "estudios" dentro de la ruta principal del sistema Fintech, cada uno esta registrado por numero telefónico de acuerdo a la clínica registrada en la base de datos `fintech_horizontes`.

### 2. Base de Datos:
El sistema esta constituido mediante lenguaje de programación Sqlite para independizar el medio de almacenamiento a un externo como "XAMPP", ubicado dentro de la carpeta de "database" de la ruta principal del sistema Fintech:
* **Nombre de la DB**: `fintech_horizontes`
* **Tabla**: `registros`,`estudios`
* **1 Campo**: `id`,`nombre`, `cedula`,`telefono`,`estatus_pago`
* **2 Campo**: `id`,`nombre_estudio`,`precio`,`clinica_emisor`,`fecha_escaneo`

## 3. Instalación y Despliegue:

Selecciona y descomprime los 7 archivos presentes en formato "rar" 

Clona este repositorio o descarga los archivos y ejecuta el siguiente comando para instalar las librerías necesarias:

```bash
pip install pandas openpyxl pillow pytesseract pyautogui opencv-python customtkinter fuzzywuzzy python-Levenshtein pyinstaller
