"""Carga opcional los archivos locales de entorno antes de inicializar servicios."""

from pathlib import Path

from dotenv import load_dotenv


_directorio_backend = Path(__file__).resolve().parents[1]
load_dotenv(_directorio_backend / ".env", override=False)
load_dotenv(_directorio_backend.parent / ".env", override=False)
