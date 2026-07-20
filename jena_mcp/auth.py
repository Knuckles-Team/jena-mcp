"""Identity credentials loader for the Apache Jena Fuseki client."""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting
from agent_utilities.core.transport_security import resolve_configured_tls_profile

from jena_mcp.api_client import Api

logger = get_logger(__name__)


def get_client() -> Api:
    """Build an authenticated Apache Jena Fuseki client from the environment.

    Honors ``APACHE_JENA_URL`` (the deployed convention), ``JENA_FUSEKI_URL``,
    or ``JENA_URL`` for the base URL; bearer token via ``APACHE_JENA_TOKEN`` or
    ``JENA_TOKEN``; optional basic auth via ``JENA_USERNAME``/``JENA_PASSWORD``;
    TLS trust via a named ``JENA_TLS_PROFILE`` or ``JENA_TLS_PROFILE_REF``.
    """
    base_url = (
        setting("APACHE_JENA_URL", None)
        or setting("JENA_FUSEKI_URL", None)
        or setting("JENA_URL", None)
        or "http://localhost:3030"
    )
    token = setting("APACHE_JENA_TOKEN", "") or setting("JENA_TOKEN", "")
    username = setting("JENA_USERNAME", "")
    password = setting("JENA_PASSWORD", "")
    tls_profile = resolve_configured_tls_profile(
        "jena",
        profile_name=setting("JENA_TLS_PROFILE", None),
        profile_ref=setting("JENA_TLS_PROFILE_REF", None),
    )

    return Api(
        base_url=base_url,
        token=token or None,
        username=username or None,
        password=password or None,
        tls_profile=tls_profile,
    )
