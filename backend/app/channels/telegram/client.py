"""
Nuvora — Telegram Channel: TelegramClient
==========================================
Cliente HTTP mínimo para hablar con la API de Telegram.

RESPONSABILIDADES:
    - getMe()         → valida token + devuelve info del bot
    - setWebhook()    → configura el webhook
    - deleteWebhook() → limpia el webhook
    - sendMessage()   → envía un mensaje de texto

FILOSOFÍA:
    - Solo HTTP calls. CERO lógica de negocio.
    - Aislado del resto del proyecto.
    - Sin dependencias nuevas: usa `requests` (ya está en requirements).
    - Fácil de mockear en tests: todo pasa por `self._request`.

SEGURIDAD:
    - El token NUNCA se loguea.
    - Los errores de la API se mapean a excepciones propias.

USO:
    client = TelegramClient(token="123456:ABC...")
    info = client.get_me()
    client.set_webhook(url="https://...", secret="...")
    client.send_message(chat_id=12345, text="Hola")
"""

import logging
import time

import requests

from app.channels.telegram.errors import (
    TelegramAuthError,
    TelegramAPIError,
    TelegramNetworkError,
)


logger = logging.getLogger(__name__)

# ============================================================
# CONSTANTES
# ============================================================

TELEGRAM_API_BASE = "https://api.telegram.org"
DEFAULT_TIMEOUT = 10  # segundos
MAX_RETRIES_ON_NETWORK = 1  # reintentos adicionales (total = 1 + 1)
RETRY_BACKOFF_SECONDS = 1.5


class TelegramClient:
    """
    Cliente HTTP para la API de Telegram.

    El token se pasa en el constructor. Todos los métodos llaman a
    `self._request(method, payload)` que hace el POST y mapea errores.
    """

    def __init__(self, token: str, timeout: int = DEFAULT_TIMEOUT):
        if not token or not isinstance(token, str):
            raise ValueError("TelegramClient requiere un token no vacío")
        self._token = token
        self._timeout = timeout

    # ============================================================
    # API PÚBLICA
    # ============================================================

    def get_me(self) -> dict:
        """
        Llama a getMe. Valida el token y devuelve info del bot.

        Returns:
            dict con al menos: {"id": int, "username": str, "first_name": str}

        Raises:
            TelegramAuthError: token inválido.
            TelegramAPIError:  otro error de la API.
            TelegramNetworkError: fallo de red tras reintentos.
        """
        result = self._request("getMe", {})
        return result.get("result", result)

    def set_webhook(self, url: str, secret: str | None = None) -> bool:
        """
        Configura el webhook del bot.

        Args:
            url: URL HTTPS pública que Telegram llamará.
            secret: token opaco que Telegram reenviará en el header
                    X-Telegram-Bot-Api-Secret-Token.

        Returns:
            True si Telegram aceptó la configuración.

        Raises:
            TelegramAuthError, TelegramAPIError, TelegramNetworkError.
        """
        payload = {
            "url": url,
            "allowed_updates": ["message"],  # MVP: solo mensajes
        }
        if secret:
            payload["secret_token"] = secret

        result = self._request("setWebhook", payload)
        # setWebhook devuelve {ok: true, result: true}
        return bool(result.get("result", result))

    def delete_webhook(self) -> bool:
        """
        Elimina el webhook del bot. Telegram dejará de enviar updates.

        Returns:
            True si se eliminó correctamente.
        """
        result = self._request("deleteWebhook", {})
        return bool(result.get("result", result))

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str | None = None,
    ) -> dict:
        """
        Envía un mensaje de texto a un chat.

        Args:
            chat_id: ID del chat de destino (int o str).
            text: texto del mensaje.
            parse_mode: "MarkdownV2" | "HTML" | None (default = texto plano).

        Returns:
            dict con la respuesta de Telegram (message_id, etc.).

        Raises:
            TelegramAuthError, TelegramAPIError, TelegramNetworkError.
        """
        if not text or not text.strip():
            raise ValueError("send_message: el texto no puede estar vacío")

        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        result = self._request("sendMessage", payload)
        return result.get("result", result)

    # ============================================================
    # INTERNO
    # ============================================================

    def _url(self, method: str) -> str:
        """URL completa para un método de la Bot API."""
        return f"{TELEGRAM_API_BASE}/bot{self._token}/{method}"

    def _request(self, method: str, payload: dict) -> dict:
        """
        Hace un POST a Telegram Bot API con retry 1 vez en errores de red.

        Returns:
            El JSON completo de la respuesta (dict con ok + result).

        Raises:
            TelegramAuthError, TelegramAPIError, TelegramNetworkError.
        """
        url = self._url(method)
        attempts = MAX_RETRIES_ON_NETWORK + 1
        last_exc: Exception | None = None

        for attempt in range(attempts):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    timeout=self._timeout,
                    headers={"Content-Type": "application/json"},
                )
            except (requests.Timeout, requests.ConnectionError) as e:
                last_exc = e
                if attempt < attempts - 1:
                    time.sleep(RETRY_BACKOFF_SECONDS)
                    continue
                # Se agotaron los reintentos
                logger.warning(
                    "Telegram %s: error de red tras %d intentos: %s",
                    method, attempts, type(e).__name__,
                )
                raise TelegramNetworkError(
                    f"Fallo de red al llamar a Telegram {method}: {type(e).__name__}"
                ) from e

            # Respuesta HTTP recibida
            return self._handle_response(method, resp)

        # No debería llegar aquí
        raise TelegramNetworkError(f"Fallo inesperado en {method}: {last_exc}")

    def _handle_response(self, method: str, resp: requests.Response) -> dict:
        """
        Mapea la respuesta HTTP a dict o lanza excepción propia.

        Telegram siempre devuelve JSON con "ok": true|false.
        """
        # 401 → token inválido
        if resp.status_code == 401:
            logger.warning("Telegram %s: token inválido (401)", method)
            raise TelegramAuthError(
                "Token de Telegram inválido o no autorizado."
            )

        # Intentar parsear JSON
        try:
            data = resp.json()
        except ValueError:
            raise TelegramAPIError(
                f"Respuesta no-JSON de Telegram {method} "
                f"(HTTP {resp.status_code}): {resp.text[:200]}",
                status_code=resp.status_code,
            )

        # Telegram devuelve "ok": false con "description" en errores
        if not data.get("ok"):
            description = data.get("description", "error desconocido")
            error_code = data.get("error_code", resp.status_code)

            # Algunos errores de "token mal formado" llegan como 404
            # con description "Not Found"
            if error_code == 404 and "not found" in description.lower():
                raise TelegramAuthError(
                    f"Token o método no encontrado: {description}"
                )

            raise TelegramAPIError(
                f"Error de Telegram {method}: {description}",
                status_code=error_code,
            )

        return data


__all__ = ["TelegramClient"]
