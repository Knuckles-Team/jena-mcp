"""jena-mcp: Apache Jena (Fuseki) API + MCP Server + A2A Server."""

from scion_sdk.connector import Connector

from jena_mcp.api_client import Api
from jena_mcp.auth import get_client

connector = Connector(
    api=Api,
    get_client=get_client,
    tools="jena_mcp.mcp_server",
    instructions="Apache Jena (Fuseki) MCP Server - SPARQL query/update, Graph Store Protocol, and server administration.",
)
