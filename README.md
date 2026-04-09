🛡️ Asistencia Predictiva - Seguros Horizonte (AMP)
Este sistema utiliza IA y OCR para automatizar la identificación de asegurados mediante la lectura en tiempo real de la pantalla del software Avaya Workspace.

📋 Requisitos Previos
Antes de instalar las librerías de Python, es obligatorio instalar el motor de reconocimiento de texto en el sistema operativo:

Tesseract OCR:

Descarga el instalador para Windows aquí.

Importante: Durante la instalación, asegúrate de que la ruta sea C:\Program Files\Tesseract-OCR\tesseract.exe o actualiza la variable pytesseract.pytesseract.tesseract_cmd en el código.

🚀 Instalación de Dependencias
Ejecuta el siguiente comando en tu terminal para instalar todas las librerías necesarias:

Bash
pip install pytesseract mysql-connector-python pyautogui customtkinter Pillow
Detalle de las librerías utilizadas:
pytesseract: Interfaz para el motor OCR Tesseract.

mysql-connector-python: Conector oficial para la base de datos MySQL (XAMPP/WAMP).

pyautogui: Utilizado para realizar las capturas de pantalla automáticas de la región de Avaya.

customtkinter: Framework para la interfaz gráfica moderna con estilo Cyberpunk y modo oscuro.

Pillow (PIL): Gestión de imágenes y generación dinámica del logo F-Escudo en formato .ico.

🛠️ Configuración de la Base de Datos
El sistema busca una base de datos local con los siguientes parámetros por defecto:

DB Name: fintech_horizontes

Tabla: asegurados

Campos requeridos: nombre, cedula, telefono, estatus_pago.

🖥️ Ejecución
Para iniciar el monitor de IA, simplemente corre el script principal:

```Bash
python Base.py
Nota sobre el Icono: El sistema genera automáticamente un archivo logo_amp.ico al ejecutarse para personalizar la barra de tareas de Windows mediante el AppUserModelID configurado.
