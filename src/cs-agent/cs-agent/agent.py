import requests
import jwt
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams    
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH


remote_agent = RemoteA2aAgent(
    name="promotion_agent",
    description="Agent that handles getting, creating, deleting and checking promotion details.",
    agent_card=f"http://promotion-agent:8080{AGENT_CARD_WELL_KNOWN_PATH}",
)

root_agent = LlmAgent(
    name="cs_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to interact with Bank of Anthos banking services. "
        "Can help users login, check account balances, transfer money, "
        "and perform various banking operations."
    ),
    instruction=(
        "You are a helpful banking assistant for Bank of Anthos. "
        "You can help users login to their accounts, get their account "
        "information, check balances, transfer money between accounts, "
        "manage contacts, and perform various banking operations. Always "
        "ask for username and password when users want to login. Make sure "
        "to inform users about their login status before performing any "
        "banking operations. Users can get their account ID by asking "
        "'what is my account ID' or 'show my account info'. When checking "
        "balances or making transfers, you can use the user's own account "
        "ID automatically. Users can transfer money by contact name if they "
        "have saved contacts, or by account number directly. Help users "
        "manage their contacts for easier transfers."
        "You can also be asked about promotion details. Ask the promotion_agent for the details."
        "If there is no promotion, tell it to create one if none is available."
        "Leave the decision of what promotion to create to the promotion_agent."
        "You shouldn't need to ask user for the username or detail of the promotion they want."
        "User should always have a promotion if they ask for it."
    ),
    sub_agents=[remote_agent],
    tools=[McpToolset(
        connection_params=StreamableHTTPServerParams(
            url="http://anthos-mcp:8080/mcp"
        )
    )],
)
