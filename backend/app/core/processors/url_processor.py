"""
Nuvora Core — URL Processor
==============================
Descarga una URL y extrae el texto visible.
Incluye defensas anti-SSRF.
"""

import ipaddress
import socket
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests

from app.core.processors.base import BaseProcessor, ProcessorResult, ProcessorError


# ============================================================
# LÍMITES Y CONSTANTES
# ============================================================

MAX_URL_SIZE = 5 * 1024 * 1024  # 5 MB
URL_TIMEOUT = 10  # segundos
URL_MAX_REDIRECTS = 3
USER_AGENT = "NuvoraBot/1.0 (+https://nuvora.com/bot)"

# Esquemas permitidos
ALLOWED_SCHEMES = {"http", "https"}


class URLProcessor(BaseProcessor):

    def process(self, content: str | bytes, **kwargs) -> ProcessorResult:
        # 1. Validar que sea string (URL)
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError:
                raise ProcessorError("La URL no es válida (bytes no decodificables)")

        if not isinstance(content, str) or not content.strip():
            raise ProcessorError("La URL está vacía")

        url = content.strip()

        # 2. Validar URL inicial (esquema + host)
        self._validate_url_safety(url)

        # 3. Fetch con seguimiento manual de redirecciones
        html, final_url, status_code, content_type = self._fetch_with_redirects(url)

        # 4. Parsear HTML → texto
        text, title = self._html_to_text(html)

        if not text.strip():
            raise ProcessorError("No se pudo extraer texto de la URL")

        # 5. Metadatos
        meta = {
            "url_original": url,
            "url_final": final_url,
            "status_code": status_code,
            "content_type": content_type,
            "chars": len(text),
            "title": title,
            "source_type": "url",
        }

        return ProcessorResult(
            text=text,
            meta=meta,
            size_bytes=len(html.encode("utf-8")),
        )

    # ============================================================
    # VALIDACIÓN ANTI-SSRF
    # ============================================================

    def _validate_url_safety(self, url: str):
        """
        Valida que la URL sea segura (no SSRF):
        1. Esquema permitido (http/https)
        2. Hostname no es localhost ni privado
        3. DNS resuelve a IP no privada
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ProcessorError(f"URL inválida: {e}")

        # 1. Esquema
        if parsed.scheme not in ALLOWED_SCHEMES:
            raise ProcessorError(
                f"Esquema no permitido: '{parsed.scheme}'. Solo http y https."
            )

        hostname = parsed.hostname
        if not hostname:
            raise ProcessorError("La URL no tiene hostname")

        # 2. Bloquear hostnames obvios
        hostname_lower = hostname.lower()
        if hostname_lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            raise ProcessorError("No se permiten URLs a localhost")

        if hostname_lower.endswith(".local"):
            raise ProcessorError("No se permiten dominios .local")

        # 3. Resolver DNS y verificar IP
        self._verify_ip_is_public(hostname)

    def _verify_ip_is_public(self, hostname: str):
        """
        Resuelve el hostname y verifica que la IP resultante NO sea privada.
        Previene ataques DNS rebinding básicos.
        """
        try:
            # getaddrinfo devuelve lista de (family, type, proto, canonname, sockaddr)
            addr_info = socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            raise ProcessorError(f"No se pudo resolver el hostname '{hostname}': {e}")

        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue

            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise ProcessorError(
                    f"La URL resuelve a una IP no permitida: {ip_str}"
                )

    # ============================================================
    # FETCH CON REDIRECTS
    # ============================================================

    def _fetch_with_redirects(self, url: str):
        """
        Descarga la URL con seguimiento MANUAL de redirecciones.
        Cada redirect se valida contra SSRF ANTES de seguir.
        """
        current_url = url
        headers = {"User-Agent": USER_AGENT}
        seen_urls = set()

        for _ in range(URL_MAX_REDIRECTS + 1):
            # Evitar bucles
            if current_url in seen_urls:
                raise ProcessorError("Bucle de redirecciones detectado")
            seen_urls.add(current_url)

            # Validar URL antes de cada conexión
            self._validate_url_safety(current_url)

            try:
                response = requests.get(
                    current_url,
                    headers=headers,
                    timeout=URL_TIMEOUT,
                    allow_redirects=False,
                    stream=True,
                )
            except requests.exceptions.Timeout:
                raise ProcessorError(f"Timeout al conectar con {current_url}")
            except requests.exceptions.RequestException as e:
                raise ProcessorError(f"Error al conectar con {current_url}: {e}")

            # ¿Redirección?
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    raise ProcessorError("Redirección sin Location header")
                # Resolver URL relativa
                current_url = urljoin(current_url, location)
                continue

            # ¿OK?
            if response.status_code >= 400:
                raise ProcessorError(
                    f"La URL devolvió status {response.status_code}"
                )

            # Verificar tamaño máximo durante la descarga
            content = response.content
            if len(content) > MAX_URL_SIZE:
                raise ProcessorError(
                    f"La respuesta supera el límite de {MAX_URL_SIZE // (1024*1024)} MB"
                )

            content_type = response.headers.get("Content-Type", "")
            try:
                html = content.decode(response.encoding or "utf-8", errors="replace")
            except Exception:
                html = content.decode("utf-8", errors="replace")

            return html, current_url, response.status_code, content_type

        raise ProcessorError(f"Demasiadas redirecciones (máx {URL_MAX_REDIRECTS})")

    # ============================================================
    # HTML → TEXTO
    # ============================================================

    def _html_to_text(self, html: str) -> tuple[str, str]:
        """
        Convierte HTML a texto plano.
        Devuelve (texto, título).
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extraer título
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Eliminar elementos no relevantes
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "noscript", "iframe", "svg", "form"]):
            tag.decompose()

        # Extraer secciones y contenido en orden
        lines = []

        # Títulos (h1-h6) con prefijo Markdown
        for level in range(1, 7):
            for h in soup.find_all(f"h{level}"):
                text = h.get_text(strip=True)
                if text:
                    lines.append(f"{'#' * level} {text}")
                    lines.append("")  # línea en blanco tras título

        # Párrafos
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                lines.append(text)

        # Listas
        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            if text:
                lines.append(f"- {text}")

        # Celdas de tabla
        for td in soup.find_all("td"):
            text = td.get_text(" ", strip=True)
            if text:
                lines.append(text)

        # Si no hay nada estructurado, usar texto plano del body
        if not lines:
            body = soup.body or soup
            text = body.get_text("\n", strip=True)
            if text:
                lines = [text]

        result = "\n".join(lines)
        return result, title
