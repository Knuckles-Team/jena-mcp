"""Identity credentials loader for the Apache Jena Fuseki client."""

import os

from agent_utilities.base_utilities import get_logger, to_boolean

from jena_mcp.api_client import Api

logger = get_logger(__name__)


def get_client() -> Api:
    """Build an authenticated Apache Jena Fuseki client from the environment.

    Honors ``JENA_FUSEKI_URL`` (preferred) or ``JENA_URL``; bearer token via
    ``JENA_TOKEN``; optional basic auth via ``JENA_USERNAME``/``JENA_PASSWORD``;
    TLS verification via ``JENA_SSL_VERIFY``.
    """
    base_url = (
        os.getenv("JENA_FUSEKI_URL")
        or os.getenv("JENA_URL")
        or "http://localhost:3030"
    )
    token = os.getenv("JENA_TOKEN", "")
    username = os.getenv("JENA_USERNAME", "")
    password = os.getenv("JENA_PASSWORD", "")
    verify = to_boolean(os.getenv("JENA_SSL_VERIFY", "True"))

    return Api(
        base_url=base_url,
        token=token or None,
        username=username or None,
        password=password or None,
        verify=verify,
    )
