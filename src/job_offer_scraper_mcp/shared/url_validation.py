import ipaddress
import socket
from collections.abc import Callable, Iterable
from urllib.parse import urlsplit


class UnsafeUrlError(ValueError):
    """Raised when a URL could access a non-public network resource."""


AddressResolver = Callable[[str, int], Iterable[str]]


def _resolve_addresses(hostname: str, port: int) -> Iterable[str]:
    try:
        address_info = socket.getaddrinfo(
            hostname,
            port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as error:
        raise UnsafeUrlError("The URL hostname could not be resolved.") from error

    return (str(entry[4][0]) for entry in address_info)


def validate_public_http_url(
    url: str,
    *,
    resolver: AddressResolver = _resolve_addresses,
) -> str:
    """Validate that a URL uses HTTP(S) and resolves only to public addresses."""
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeUrlError("Only HTTP and HTTPS URLs are allowed.")
    if not parsed.hostname:
        raise UnsafeUrlError("The URL must contain a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeUrlError("URLs containing credentials are not allowed.")

    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    except ValueError as error:
        raise UnsafeUrlError("The URL contains an invalid port.") from error

    try:
        addresses = tuple(resolver(parsed.hostname, port))
    except UnsafeUrlError:
        raise
    except OSError as error:
        raise UnsafeUrlError("The URL hostname could not be resolved.") from error
    if not addresses:
        raise UnsafeUrlError("The URL hostname did not resolve to an address.")

    for address in addresses:
        normalized_address = address.split("%", maxsplit=1)[0]
        try:
            ip_address = ipaddress.ip_address(normalized_address)
        except ValueError as error:
            raise UnsafeUrlError("The URL resolved to an invalid address.") from error
        if not ip_address.is_global:
            raise UnsafeUrlError("The URL resolves to a non-public address.")

    return url
