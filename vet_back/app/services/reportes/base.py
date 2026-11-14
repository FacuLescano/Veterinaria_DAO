from pathlib import Path
import logging

logger = logging.getLogger(__name__)

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

