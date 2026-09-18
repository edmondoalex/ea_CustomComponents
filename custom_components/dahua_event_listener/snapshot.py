"""Utility condivise per gli snapshot Dahua."""

import logging

import requests
from requests.auth import HTTPDigestAuth

_LOGGER = logging.getLogger(__name__)


def fetch_dahua_snapshot(
    host: str,
    username: str,
    password: str,
    channel: int,
    connect_timeout: int = 10,
    read_timeout: int = 10,
) -> bytes | None:
    """Scarica uno snapshot provando main stream e poi substream."""
    auth = HTTPDigestAuth(username, password)

    for stream in (0, 1):
        snapshot_url = (
            f"http://{host}/cgi-bin/snapshot.cgi"
            f"?channel={channel}&stream={stream}"
        )
        try:
            response = requests.get(
                snapshot_url,
                auth=auth,
                timeout=(connect_timeout, read_timeout),
            )
        except requests.exceptions.RequestException as ex:
            _LOGGER.warning(
                "Snapshot Dahua CH%s stream=%s fallito: %s",
                channel,
                stream,
                ex,
            )
            continue

        content_type = response.headers.get("Content-Type", "").lower()
        is_image = content_type.startswith("image/") or response.content.startswith(
            b"\xff\xd8\xff"
        )
        if response.status_code == 200 and response.content and is_image:
            if stream == 1:
                _LOGGER.info(
                    "Snapshot Dahua CH%s acquisito dal substream dopo il fallimento del main stream",
                    channel,
                )
            return response.content

        _LOGGER.warning(
            "Snapshot Dahua CH%s stream=%s non valido: HTTP %s, Content-Type=%s, bytes=%s",
            channel,
            stream,
            response.status_code,
            content_type or "N/D",
            len(response.content),
        )

    return None
