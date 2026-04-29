
import os
import subprocess
import sys
import customtkinter

def build():
    # Nombre del archivo principal
    main_script = "main.py"
    # Nombre de la carpeta de salida
    app_name = "FintechIA_App"
    
    # Obtener ruta de customtkinter para incluir sus assets
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    # --- NUEVO: Limpieza de archivos temporales antes de compilar ---
    print("[*] Preparando carpeta de estudios (limpiando archivos temporales)...")
    if not os.path.exists("dist_assets"):
        os.makedirs("dist_assets")
        
    import shutil
    import glob
    
    # Limpiamos carpeta temporal si existe
    if os.path.exists("dist_assets/estudios"):
        shutil.rmtree("dist_assets/estudios")
    os.makedirs("dist_assets/estudios")
    
    # Copiamos solo los archivos .xlsx que no son temporales
    archivos_estudios = glob.glob("estudios/*.xlsx")
    for f in archivos_estudios:
        if not os.path.basename(f).startswith("~$"):
            shutil.copy(f, "dist_assets/estudios/")
    
    print(f"[*] Iniciando compilación de {app_name}...")
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={app_name}",
        f"--add-data={ctk_path}{os.pathsep}customtkinter",
        f"--add-data=dist_assets/estudios{os.pathsep}estudios", # Usamos la carpeta limpia
    ]
    
    # Si tienes un icono en assets/logo.ico lo agregamos
    if os.path.exists("assets/logo.ico"):
        cmd.append("--icon=assets/logo.ico")
        
    cmd.append(main_script)
    
    try:
        subprocess.check_call(cmd)
        print(f"\n[OK] ¡Compilación terminada con éxito!")
        print(f"[INFO] Tu ejecutable está en: dist/{app_name}/{app_name}.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Algo falló durante la compilación: {e}")

if __name__ == "__main__":
    build()
