from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Zona horaria oficial de Argentina (UTC-3)
TZ_ARGENTINA = timezone(timedelta(hours=-3))


def ahora_argentina() -> datetime:
    return datetime.now(TZ_ARGENTINA)


def fecha_hora_argentina_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return ahora_argentina().strftime(fmt)


# Resolución del logotipo oficial del sistema
DIRECTORIO_APP = Path(__file__).resolve().parent.parent.parent
RUTA_LOGO = DIRECTORIO_APP / "static" / "logo.png"
if not RUTA_LOGO.exists():
    RUTA_LOGO = (
        DIRECTORIO_APP.parent.parent
        / "vet_front"
        / "public"
        / "assets"
        / "aistudio"
        / "Gemini_Generated_Image_o95dgio95dgio95d-removebg-preview_cbe90b76.png"
    )

