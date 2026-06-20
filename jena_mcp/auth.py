"""Identity credentials loader for the Apache Jena Fuseki client."""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting

from jena_mcp.api_client import Api

logger = get_logger(__name__)


def get_client() -> Api:
    """Build an authenticated Apache Jena Fuseki client from the environment.

    Honors ``JENA_FUSEKI_URL`` (preferred) or ``JENA_URL``; bearer token via
    ``JENA_TOKEN``; optional basic auth via ``JENA_USERNAME``/``JENA_PASSWORD``;
    TLS verification via ``JENA_SSL_VERIFY``.
    """
    base_url = (
        setting("JENA_FUSEKI_URL", None)
        or setting("JENA_URL", None)
        or "http://localhost:3030"
    )
    token = setting("JENA_TOKEN", "")
    username = setting("JENA_USERNAME", "")
    password = setting("JENA_PASSWORD", "")
    verify = setting("JENA_SSL_VERIFY", True)

    return Api(
        base_url=base_url,
        token=token or None,
        username=username or None,
        password=password or None,
        verify=verify,
    )
