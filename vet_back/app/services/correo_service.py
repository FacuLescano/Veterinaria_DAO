"""Configuración y envío SMTP para avisos de resultados disponibles."""

from dataclasses import dataclass
from email.message import EmailMessage
import logging
import os
import smtplib
import ssl

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfiguracionSMTP:
    servidor: str | None
    puerto: int
    usuario: str | None
    contrasena: str | None
    remitente: str | None
    seguridad: str

    @classmethod
    def desde_entorno(cls) -> "ConfiguracionSMTP":
        try:
            puerto = int(os.getenv("SMTP_PORT", "587"))
        except ValueError:
            puerto = 0
        return cls(
            servidor=os.getenv("SMTP_HOST") or None,
            puerto=puerto,
            usuario=os.getenv("SMTP_USER") or None,
            contrasena=os.getenv("SMTP_PASSWORD") or None,
            remitente=os.getenv("SMTP_FROM") or None,
            seguridad=os.getenv("SMTP_SECURITY", "starttls").strip().lower(),
        )

    @property
    def disponible(self) -> bool:
        return bool(
            self.servidor
            and self.remitente
            and 1 <= self.puerto <= 65535
            and self.seguridad in {"starttls", "ssl", "none"}
        )


class ServicioCorreo:
    def __init__(self, configuracion: ConfiguracionSMTP | None = None) -> None:
        self.configuracion = configuracion or ConfiguracionSMTP.desde_entorno()

    def enviar_resultados_disponibles(
        self, destinatario: str, nombre_responsable: str | None, nombre_mascota: str | None
    ) -> bool:
        config = self.configuracion
        if not config.disponible:
            logger.warning("No se envió el aviso: SMTP no está configurado o SMTP_SECURITY no es válido")
            return False

        asunto, cuerpo = plantilla_resultados_disponibles(nombre_responsable, nombre_mascota)
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = config.remitente
        mensaje["To"] = destinatario
        mensaje.set_content(cuerpo)
        contexto_tls = ssl.create_default_context()

        try:
            if config.seguridad == "ssl":
                with smtplib.SMTP_SSL(config.servidor, config.puerto, context=contexto_tls, timeout=20) as smtp:
                    self._autenticar(smtp, config)
                    smtp.send_message(mensaje)
            else:
                with smtplib.SMTP(config.servidor, config.puerto, timeout=20) as smtp:
                    smtp.ehlo()
                    if config.seguridad == "starttls":
                        smtp.starttls(context=contexto_tls)
                        smtp.ehlo()
                    self._autenticar(smtp, config)
                    smtp.send_message(mensaje)
        except (OSError, smtplib.SMTPException) as error:
            logger.error("No se pudo enviar el aviso de resultados por correo (%s)", type(error).__name__)
            return False
        return True

    @staticmethod
    def _autenticar(smtp, config: ConfiguracionSMTP) -> None:
        if config.usuario:
            smtp.login(config.usuario, config.contrasena or "")


def plantilla_resultados_disponibles(
    nombre_responsable: str | None, nombre_mascota: str | None
) -> tuple[str, str]:
    nombre = (nombre_responsable or "").strip()
    mascota = (nombre_mascota or "").strip()
    saludo = f"Hola {nombre}," if nombre else "Hola,"
    mascota_texto = f" de {mascota}" if mascota else ""
    cuerpo = (
        f"{saludo}\n\n"
        f"Te informamos que los resultados de los análisis{mascota_texto} ya están disponibles.\n\n"
        "Te recomendamos solicitar un nuevo turno con el veterinario para revisar los resultados "
        "y recibir las indicaciones correspondientes.\n\n"
        "Saludos cordiales,\nPatitas & Co."
    )
    return "Resultados de análisis disponibles", cuerpo
