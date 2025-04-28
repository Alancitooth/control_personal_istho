@echo off
echo Activando el entorno virtual...

if not exist venv (
    echo No se encontro un entorno virtual. Creandolo...
    python -m venv venv
)

call venv\Scripts\activate

echo Instalando dependencias necesarias...
pip install -r requirements.txt

echo Iniciando la aplicacion...
streamlit run app.py

pause
