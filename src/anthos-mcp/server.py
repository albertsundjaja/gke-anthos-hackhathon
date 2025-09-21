"""
Bank of Anthos MCP Server

Bank of Anthos MCP Server - banking functionality through MCP
allowing AI assistants to interact with Bank of Anthos services.
"""

# Import the MCP server with all tools registered
from banking_tools import mcp

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8080, host="0.0.0.0")