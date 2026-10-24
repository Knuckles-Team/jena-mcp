"""Main FastMCP server and tool registration for jena-mcp."""

from jena_mcp.mcp.mcp_jena import register_jena_tools  # noqa: F401

# SDK discovery registers the register_<tag>_tools functions bound in this module.
__all__ = ["register_jena_tools"]
