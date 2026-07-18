import socket

import pytest

from job_offer_scraper_mcp.shared.url_validation import (
    UnsafeUrlError,
    validate_public_http_url,
)


def resolver_for(*addresses: str):
    def resolve(_hostname: str, _port: int) -> tuple[str, ...]:
        return addresses

    return resolve


def test_validate_public_http_url_accepts_public_https_address() -> None:
    url = "https://jobs.example.com/offer/1"

    result = validate_public_http_url(
        url,
        resolver=resolver_for("93.184.216.34"),
    )

    assert result == url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/jobs",
        "https://user:password@example.com/jobs",
        "https:///missing-host",
    ],
)
def test_validate_public_http_url_rejects_invalid_url_forms(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_http_url(url, resolver=resolver_for("93.184.216.34"))


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "192.168.1.10",
        "::1",
        "fc00::1",
    ],
)
def test_validate_public_http_url_rejects_non_public_addresses(
    address: str,
) -> None:
    with pytest.raises(UnsafeUrlError, match="non-public"):
        validate_public_http_url(
            "https://example.com/jobs",
            resolver=resolver_for(address),
        )


def test_validate_public_http_url_rejects_mixed_public_and_private_dns() -> None:
    with pytest.raises(UnsafeUrlError, match="non-public"):
        validate_public_http_url(
            "https://example.com/jobs",
            resolver=resolver_for("93.184.216.34", "127.0.0.1"),
        )


def test_validate_public_http_url_hides_dns_error_details() -> None:
    def failing_resolver(_hostname: str, _port: int) -> tuple[str, ...]:
        raise socket.gaierror("internal resolver detail")

    with pytest.raises(UnsafeUrlError, match="could not be resolved") as error_info:
        validate_public_http_url(
            "https://example.com/jobs",
            resolver=failing_resolver,
        )

    assert "internal resolver detail" not in str(error_info.value)
