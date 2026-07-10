"""
version.py
----------
Identidad y versión de ESTE programa, más la configuración de actualizaciones.

IMPORTANTE: subí VERSION en cada build nuevo ANTES de compilar el .exe. El
updater compara esta versión contra la del manifiesto remoto para saber si hay
que actualizar.
"""

# Identificador del programa (mismo esquema que la licencia por programa).
PROGRAM_ID = "recibos_2026"

# Versión de este build. Subila antes de compilar cada release.
VERSION = "1.1.0"

# URL del manifiesto de actualizaciones (JSON) en GitHub Releases.
# Es ESTABLE: siempre el tag 'latest' con el archivo manifest.json. En cada
# release actualizás el CONTENIDO del manifest (no esta URL).
#
# Formato del manifest.json (lo genera release/generar_manifest.py):
#   {
#       "version":   "1.0.1",
#       "url":       "https://github.com/JulianSarlingo/SueldoFacil/releases/download/v1.0.1/SueldoFacil.exe",
#       "sha256":    "<hash sha-256 del exe>",
#       "changelog": "Qué cambió"
#   }
URL_MANIFIESTO = "https://github.com/JulianSarlingo/SueldoFacil/releases/download/latest/manifest.json"
