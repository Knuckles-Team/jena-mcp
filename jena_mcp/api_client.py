"""Public client facade for jena_mcp."""

from jena_mcp.api.api_client_jena import JenaApi

__version__ = "2.4.3"


class Api(JenaApi):
    """Authenticated Apache Jena Fuseki client."""

    pass
