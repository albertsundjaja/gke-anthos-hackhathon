"""
Banking tools for Bank of Anthos MCP server.
Extracted and adapted from the original agent.py file with multi-user session support.
"""

import requests
import jwt
import time
from typing import Optional, Dict, Any
from fastmcp import FastMCP, Context
import logging

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize FastMCP server
mcp = FastMCP("Bank of Anthos MCP Server")

# Session-based token storage for multiple users
# TODO: this is a hack for quick implementation
_user_sessions: Dict[str, str] = {}  # username -> token
# Default internal service URL
_bank_api_base_url: str = "http://userservice:8080"


def _get_user_token(username: Optional[str] = None) -> Optional[str]:
    """Get the user token for the current username."""
    if username is None:
        raise ValueError("Username is required")
    if username not in _user_sessions:
        raise ValueError(f"Username {username} not found. Please login first.")
    return _user_sessions.get(username)


def _set_user_token(token: Optional[str], username: Optional[str] = None) -> None:
    """Set the user token for the current username."""
    if username is None:
        raise ValueError("Username is required")
    _user_sessions[username] = token


@mcp.tool()
def login_to_bank(ctx: Context, username: str, password: str) -> Dict[str, Any]:
    """Login to Bank of Anthos and obtain a JWT token.

    Args:
        username (str): The username for the bank account.
        password (str): The password for the bank account.

    Returns:
        dict: status and result or error message.
    """
    try:
        # Make login request to the user service
        login_url = f"{_bank_api_base_url}/login"
        params = {
            "username": username,
            "password": password
        }

        response = requests.get(login_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            _set_user_token(token, username)

            return {
                "status": "success",
                "message": f"Successfully logged in as {username}",
                "token_obtained": True,
                "username": username
            }
        elif response.status_code == 404:
            return {
                "status": "error",
                "error_message": (
                    f"User '{username}' does not exist. "
                    "Please check your username or create a new account."
                )
            }
        elif response.status_code == 401:
            return {
                "status": "error",
                "error_message": (
                    "Invalid password. Please check your credentials and "
                    "try again."
                )
            }
        else:
            return {
                "status": "error",
                "error_message": (
                    f"Login failed with status code {response.status_code}: "
                    f"{response.text}"
                )
            }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Failed to connect to Bank of Anthos: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error during login: {str(e)}"
        }


@mcp.tool()
def check_login_status(ctx: Context, username: str) -> Dict[str, Any]:
    """Check if the user is currently logged in.

    Returns:
        dict: status and login information.
    """
    try:
        user_token = _get_user_token(username)
        has_token = user_token is not None
    except ValueError:
        has_token = False

    if has_token:
        return {
            "status": "success",
            "message": "User is currently logged in",
            "has_token": True,
            "username": username
        }
    else:
        return {
            "status": "info",
            "message": (
                "User is not logged in. Please use the login function first."
            ),
            "has_token": False,
            "username": username
        }


@mcp.tool()
def logout_from_bank(ctx: Context, username: str) -> Dict[str, Any]:
    """Logout from Bank of Anthos by clearing the stored token.

    Returns:
        dict: status and confirmation message.
    """
    try:
        user_token = _get_user_token(username)
    except ValueError:
        user_token = None

    if user_token:
        _set_user_token(None, username)
        return {
            "status": "success",
            "message": "Successfully logged out from Bank of Anthos",
            "username": username
        }
    else:
        return {
            "status": "info",
            "message": "No active session to logout from",
            "username": username
        }


@mcp.tool()
def set_bank_api_url(api_url: str) -> Dict[str, Any]:
    """Set the Bank of Anthos API base URL.

    Args:
        api_url (str): The base URL for the Bank of Anthos API
                      (e.g., "http://localhost:8080").

    Returns:
        dict: status and confirmation message.
    """
    global _bank_api_base_url

    _bank_api_base_url = api_url.rstrip('/')

    return {
        "status": "success",
        "message": f"Bank API URL set to: {_bank_api_base_url}"
    }


@mcp.tool()
def get_my_account_info(ctx: Context, username: str) -> Dict[str, Any]:
    """Get the current user's account information from the JWT token.

    Returns:
        dict: status and account information or error message.
    """
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

    if not user_token:
        return {
            "status": "error",
            "error_message": "Please login first to get account information."
        }

    try:
        decoded_token = jwt.decode(user_token, options={"verify_signature": False})
        return {
            "status": "success",
            "account_info": {
                "username": decoded_token.get("user"),
                "account_id": decoded_token.get("acct"),
                "full_name": decoded_token.get("name"),
                "issued_at": decoded_token.get("iat"),
                "expires_at": decoded_token.get("exp")
            }
        }
    except jwt.exceptions.DecodeError as e:
        return {
            "status": "error",
            "error_message": f"Failed to decode JWT token: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error getting account info: {str(e)}"
        }


def _get_account_id_internal(username: str) -> Dict[str, Any]:
    """Internal helper to get account ID without MCP decoration."""
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

    if not user_token:
        return {
            "status": "error",
            "error_message": "Please login first to get account ID."
        }

    try:
        decoded_token = jwt.decode(user_token, options={"verify_signature": False})
        account_id = decoded_token.get("acct")
        if account_id:
            return {
                "status": "success",
                "account_id": account_id,
                "message": f"Your account ID is: {account_id}"
            }
        else:
            return {
                "status": "error",
                "error_message": "Account ID not found in token."
            }
    except jwt.exceptions.DecodeError as e:
        return {
            "status": "error",
            "error_message": f"Failed to decode JWT token: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error getting account ID: {str(e)}"
        }


@mcp.tool()
def get_my_account_id(ctx: Context, username: str) -> Dict[str, Any]:
    """Get the current user's account ID from the JWT token.

    Returns:
        dict: status and account ID or error message.
    """
    return _get_account_id_internal(username)


def _get_contacts_internal(username: str) -> Dict[str, Any]:
    """Internal helper to get contacts without MCP decoration."""
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

    if not user_token:
        return {
            "status": "error",
            "error_message": "Please login first to get contacts."
        }

    try:
        contacts_url = f"http://contacts:8080/contacts/{username}"
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(contacts_url, headers=headers, timeout=10)

        if response.status_code == 200:
            contacts = response.json()
            return {
                "status": "success",
                "contacts": contacts,
                "message": f"Found {len(contacts)} saved contacts"
            }
        elif response.status_code == 401:
            return {
                "status": "error",
                "error_message": "Unauthorized. Please login again."
            }
        else:
            return {
                "status": "error",
                "error_message": (
                    f"Failed to get contacts. Status code: {response.status_code}"
                )
            }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Failed to connect to contacts service: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error getting contacts: {str(e)}"
        }


@mcp.tool()
def get_my_contacts(ctx: Context, username: str) -> Dict[str, Any]:
    """Get the current user's saved contacts.

    Returns:
        dict: status and contacts list or error message.
    """
    return _get_contacts_internal(username)


@mcp.tool()
def add_contact(
    ctx: Context,
    username: str,
    label: str,
    account_num: str,
    routing_num: str,
    is_external: bool = True
) -> Dict[str, Any]:
    """Add a new contact to the user's saved contacts.

    Args:
        label (str): The name/label for the contact (e.g., "John Doe").
        account_num (str): The account number (10 digits).
        routing_num (str): The routing number (9 digits).
        is_external (bool): Whether this is an external contact (default True).

    Returns:
        dict: status and confirmation message or error message.
    """
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

    if not user_token:
        return {
            "status": "error",
            "error_message": "Please login first to add contacts."
        }

    try:
        contacts_url = f"http://contacts:8080/contacts/{username}"
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        contact_data = {
            "label": label,
            "account_num": account_num,
            "routing_num": routing_num,
            "is_external": is_external
        }

        response = requests.post(contacts_url, headers=headers, json=contact_data, timeout=10)

        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully added contact '{label}'"}
        elif response.status_code == 401:
            return {"status": "error", "error_message": "Unauthorized. Please login again."}
        elif response.status_code == 400:
            return {"status": "error", "error_message": f"Invalid contact{response.text}"}
        else:
            return {
                "status": "error",
                "error_message": f"Failed to add contact. Status code: {response.status_code}"
            }

    except requests.exceptions.RequestException as e:
        return {"status": "error", "error_message": f"Failed to connect to contacts service: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error adding contact: {str(e)}"}


@mcp.tool()
def get_account_balance(ctx: Context, username: str, account_id: str) -> Dict[str, Any]:
    """Get the current balance for a specific account.

    Args:
        account_id (str): The account ID to check balance for.

    Returns:
        dict: status and balance information or error message.
    """
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {"status": "error", "error_message": str(e)}

    if not user_token:
        return {"status": "error", "error_message": "Please login first before checking balance."}

    try:
        balance_url = f"http://balancereader:8080/balances/{account_id}"
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(balance_url, headers=headers, timeout=10)
        if response.status_code == 200:
            balance_cents = response.json()
            balance_dollars = balance_cents / 100.0
            return {
                "status": "success",
                "account_id": account_id,
                "balance": f"${balance_dollars:,.2f}",
                "currency": "USD"
            }
        elif response.status_code == 401:
            return {"status": "error", "error_message": "Unauthorized. Please login again."}
        elif response.status_code == 404:
            return {"status": "error", "error_message": f"Account {account_id} not found or not accessible."}
        else:
            return {"status": "error", "error_message": f"Failed to get balance. Status code: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "error_message": f"Failed to connect to balance service: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error getting balance: {str(e)}"}


def _transfer_money_internal(
    username: str,
    from_account: str,
    to_account: str,
    amount: str,
    memo: str = ""
) -> Dict[str, Any]:
    """Internal helper to transfer money without MCP decoration."""
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {"status": "error", "error_message": str(e)}

    if not user_token:
        return {"status": "error", "error_message": "Please login first before making transfers."}

    try:
        transfer_url = "http://ledgerwriter:8080/transactions"
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

        # Convert amount to cents (ledgerwriter expects integer cents)
        amount_cents = int(float(amount) * 100)

        transaction_data = {
            "fromAccountNum": from_account,
            "fromRoutingNum": "883745000",
            "toAccountNum": to_account,
            "toRoutingNum": "883745000",
            "amount": amount_cents,
            "memo": memo or f"Transfer from {from_account} to {to_account}"
        }

        response = requests.post(transfer_url, headers=headers, json=transaction_data, timeout=10)

        if response.status_code == 201:
            return {
                "status": "success",
                "message": f"Successfully transferred ${amount} from {from_account} to {to_account}",
                "transaction": {
                    "from_account": from_account,
                    "to_account": to_account,
                    "amount": amount,
                    "memo": memo
                }
            }
        elif response.status_code == 401:
            return {"status": "error", "error_message": "Unauthorized. Please login again."}
        elif response.status_code == 400:
            return {"status": "error", "error_message": f"Invalid transaction: {response.text}"}
        else:
            return {"status": "error", "error_message": f"Transfer failed. Status code: {response.status_code}, Response: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "error_message": f"Failed to connect to transfer service: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error during transfer: {str(e)}"}


@mcp.tool()
def transfer_money(
    ctx: Context,
    username: str,
    from_account: str,
    to_account: str,
    amount: str,
    memo: str = ""
) -> Dict[str, Any]:
    """Transfer money from one account to another.

    Args:
        from_account (str): The account ID to transfer from.
        to_account (str): The account ID to transfer to.
        amount (str): The amount to transfer (as string, e.g., "100.50").
        memo (str): Optional memo for the transaction.

    Returns:
        dict: status and transaction information or error message.
    """
    return _transfer_money_internal(username, from_account, to_account, amount, memo)


@mcp.tool()
def transfer_money_by_name(
    ctx: Context,
    username: str,
    to_contact_name: str,
    amount: str,
    memo: str = ""
) -> Dict[str, Any]:
    """Transfer money to a contact by their saved name.

    Args:
        to_contact_name (str): The name/label of the saved contact.
        amount (str): The amount to transfer (as string, e.g., "100.50").
        memo (str): Optional memo for the transaction.

    Returns:
        dict: status and transaction information or error message.
    """
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {"status": "error", "error_message": str(e)}

    if not user_token:
        return {"status": "error", "error_message": "Please login first before making transfers."}

    try:
        # First get the user's contacts to find the contact by name
        contacts_result = _get_contacts_internal(username)
        if contacts_result["status"] != "success":
            return contacts_result

        contacts = contacts_result["contacts"]

        target_contact = None
        for contact in contacts:
            if contact.get("label", "").lower() == to_contact_name.lower():
                target_contact = contact
                break

        if not target_contact:
            return {
                "status": "error",
                "error_message": (
                    f"Contact '{to_contact_name}' not found. Use 'get_my_contacts' to see available contacts."
                )
            }

        # Get the user's account ID
        account_result = _get_account_id_internal(username)
        if account_result["status"] != "success":
            return account_result

        from_account = account_result["account_id"]
        to_account = target_contact["account_num"]

        # Now make the transfer using the internal transfer function
        return _transfer_money_internal(
            username,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            memo=memo or f"Transfer to {to_contact_name}"
        )

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error during transfer by name: {str(e)}"}


@mcp.tool()
def credit_user_account(ctx: Context, username: str, account_id: str, amount: str, memo: str = "") -> Dict[str, Any]:
    """Credit money to a user account using external deposit simulation.

    Args:
        account_id (str): The account ID to credit money to.
        amount (str): The amount to credit (as string, e.g., "100.50").
        memo (str): Optional memo for the credit transaction.

    Returns:
        dict: status and transaction information or error message.
    """
    try:
        user_token = _get_user_token(username)
    except ValueError as e:
        return {"status": "error", "error_message": str(e)}

    if not user_token:
        return {"status": "error", "error_message": "Please login first before crediting accounts."}

    try:
        external_account = "9099791699"
        external_routing = "808889588"
        local_routing = "883745000"

        transfer_url = "http://ledgerwriter:8080/transactions"
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

        amount_cents = int(float(amount) * 100)

        transaction_data = {
            "fromAccountNum": external_account,
            "fromRoutingNum": external_routing,
            "toAccountNum": account_id,
            "toRoutingNum": local_routing,
            "amount": amount_cents,
            "uuid": f"credit-{account_id}-{int(time.time())}"
        }

        response = requests.post(transfer_url, headers=headers, json=transaction_data, timeout=10)

        if response.status_code == 201:
            return {
                "status": "success",
                "message": f"Successfully credited ${amount} to account {account_id}",
                "transaction": {
                    "from_account": external_account,
                    "to_account": account_id,
                    "amount": amount,
                    "memo": memo or f"Credit to account {account_id}"
                }
            }
        elif response.status_code == 401:
            return {"status": "error", "error_message": "Unauthorized. Please login again."}
        elif response.status_code == 400:
            return {"status": "error", "error_message": f"Invalid credit transaction: {response.text}"}
        else:
            return {"status": "error", "error_message": f"Credit failed. Status code: {response.status_code}, Response: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "error_message": f"Failed to connect to transfer service: {str(e)}"}
    except ValueError as e:
        return {"status": "error", "error_message": f"Invalid amount format: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error during credit: {str(e)}"}


@mcp.tool()
def list_active_sessions(ctx: Context) -> Dict[str, Any]:
    """List all active user sessions (for debugging/admin purposes).

    Returns:
        dict: status and list of active sessions.
    """
    # For security, only show usernames (session keys), not tokens
    active_usernames = list(_user_sessions.keys())

    return {
        "status": "success",
        "active_usernames": active_usernames,
        "total_sessions": len(active_usernames)
    }
