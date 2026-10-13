import ipaddress
import os
import socket
from urllib.parse import urlparse


def _allowed_http_hosts() -> set[str]:
  return {
    item.strip().lower()
    for item in os.getenv("AI_ENDPOINT_HTTP_ALLOWLIST", "localhost,127.0.0.1").split(",")
    if item.strip()
  }


def validate_ai_endpoint_url(value: str) -> str:
  parsed = urlparse((value or "").strip())
  if parsed.scheme not in ["http", "https"] or not parsed.hostname:
    raise ValueError("AI endpoint base_url must be an HTTP(S) URL with a hostname")
  if parsed.username or parsed.password:
    raise ValueError("AI endpoint base_url must not contain credentials")

  hostname = parsed.hostname.lower()
  allowlisted = hostname in _allowed_http_hosts()
  is_production = os.getenv("APP_ENV", "development").lower() == "production"
  if is_production and parsed.scheme != "https" and not allowlisted:
    raise ValueError("Production AI endpoints must use HTTPS unless their host is allowlisted")

  try:
    resolved = {
      item[4][0]
      for item in socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    }
  except socket.gaierror as error:
    raise ValueError("AI endpoint hostname could not be resolved") from error

  if not allowlisted:
    for address in resolved:
      ip = ipaddress.ip_address(address)
      if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        raise ValueError("AI endpoint resolves to a restricted address")

  return value
