# setup_venv.ps1 — Crea un venv unico para el proyecto e instala todas las dependencias
# (incluido el modulo Seguridad en modo editable) con un solo interprete de Python.
#
# Uso:
#   cd C:\Users\Julian\Desktop\Programacion\Proyectos\SueldoFacil
#   .\setup_venv.ps1

$ErrorActionPreference = "Stop"

# Interprete base fijo (el mismo que usabas para correr main.py)
$PYTHON = "C:\Users\Julian\AppData\Local\Programs\Python\Python314\python.exe"
$SEGURIDAD_LIB = "C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias"

Write-Host "Creando venv en .venv con $PYTHON ..."
& $PYTHON -m venv .venv

$VENV_PY = ".\.venv\Scripts\python.exe"

Write-Host "Actualizando pip..."
& $VENV_PY -m pip install --upgrade pip

Write-Host "Instalando dependencias del proyecto..."
& $VENV_PY -m pip install -r requirements.txt

Write-Host "Instalando modulo Seguridad (editable) desde $SEGURIDAD_LIB ..."
& $VENV_PY -m pip install -e $SEGURIDAD_LIB

Write-Host "Verificando import de Seguridad..."
& $VENV_PY -c "import Seguridad; print('OK ->', Seguridad.__file__)"

Write-Host ""
Write-Host "Listo. A partir de ahora corre el proyecto con:"
Write-Host "  .\.venv\Scripts\python.exe main.py"
Write-Host "o activa el venv con:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
