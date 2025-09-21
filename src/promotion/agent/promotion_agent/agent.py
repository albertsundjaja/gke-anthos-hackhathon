from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPServerParams
)
import os
from datetime import datetime

from .db import PromotionDb
from .ledger_db import LedgerDb

# Default internal service URL
_db: PromotionDb | None = None
_ledger_db: LedgerDb | None = None


def get_db() -> PromotionDb:
    global _db
    if _db is None:
        db_uri = os.environ.get("PROMOTION_DB_URI")
        if not db_uri:
            raise ValueError(
                "PROMOTION_DB_URI environment variable is not set"
            )
        _db = PromotionDb(db_uri)
    return _db


def get_ledger_db() -> LedgerDb:
    global _ledger_db
    if _ledger_db is None:
        ledger_uri = os.environ.get("LEDGER_DB_URI")
        if not ledger_uri:
            raise ValueError(
                "LEDGER_DB_URI environment variable is not set"
            )
        _ledger_db = LedgerDb(ledger_uri)
    return _ledger_db


def create_promotion(username: str, detail: str) -> str:
    """Create a promotion for a user.

    Args:
        username (str): the username of the user to give promotion to.
        detail (str): the detail of the promotion.

    Returns:
        str: the detail of the promotion.
    
    Raises:
        Exception: if there is an error creating the promotion.
    """
    try:
        db = get_db()
        if db is None:
            raise RuntimeError("Database connection is not available")
        db.create_promotion(username, detail)
        return detail
    except Exception as e:
        raise e


def get_promotion(username: str) -> dict:
    """Get the promotions for a user.

    Args:
        username (str): the username of the user to get promotions for.

    Returns:
       dict: the promotion for the user and the creation time, or empty dict if not found.

    Raises:
        Exception: if there is an error getting the promotions.
    """
    try:
        db = get_db()
        if db is None:
            raise RuntimeError("Database connection is not available")
        promo = db.get_promotion_by_username(username)
        if promo is None:
            return {
                "found": False,
                "message": f"No promotion found for user '{username}'",
                "username": username
            }
        return {
            "found": True,
            "detail": promo[0],
            "created_at": promo[1].isoformat(),
            "username": username
        }
    except Exception as e:
        raise e


def delete_promotion(username: str) -> str:
    """Delete the promotion for a user.

    Args:
        username (str): the username of the user to delete the promotion for.
        
    Returns:
        str: Success message.
    """
    try:
        db = get_db()
        if db is None:
            raise RuntimeError("Database connection is not available")
        db.delete_promotion(username)
        return f"Promotion for user '{username}' has been deleted successfully."
    except Exception as e:
        raise e


def get_account_transactions(account_id: str) -> list[dict]:
    """Get transaction history for an account ID.

    Args:
        account_id (str): the account ID to get transactions for.

    Returns:
        list[dict]: list of transaction dictionaries with serialized timestamps.

    Raises:
        Exception: if there is an error getting the transactions.
    """
    try:
        ledger_db = get_ledger_db()
        if ledger_db is None:
            raise RuntimeError("Ledger database connection is not available")
        transactions = ledger_db.get_account_transactions(account_id)
        
        # Ensure we never return None, always return a list
        if transactions is None:
            transactions = []
        
        # Serialize datetime objects to strings for ADK compatibility
        serialized_transactions = []
        for transaction in transactions:
            serialized_transaction = transaction.copy()
            if 'timestamp' in serialized_transaction:
                serialized_transaction['timestamp'] = serialized_transaction['timestamp'].isoformat()
            serialized_transactions.append(serialized_transaction)
        
        return serialized_transactions
    except Exception as e:
        raise e


def get_account_deposits_total(account_id: str, since_date: str) -> int:
    """Get total deposits for an account ID.

    Args:
        account_id (str): the account ID to check deposits for.
        since_date (str): the date to check deposits since in isoformat.

    Returns:
        int: total deposit amount in cents.

    Raises:
        Exception: if there is an error getting the deposits.
    """
    try:
        ledger_db = get_ledger_db()
        if ledger_db is None:
            raise RuntimeError("Ledger database connection is not available")
        since = datetime.fromisoformat(since_date)
        return ledger_db.get_deposits_total(account_id, since)
    except Exception as e:
        raise e


def get_account_transfers_total(account_id: str, since_date: str) -> int:
    """Get total transfers for an account ID.

    Args:
        account_id (str): the account ID to check transfers for.
        since_date (str): the date to check transfers since in isoformat.

    Returns:
        int: total transfer amount in cents.

    Raises:
        Exception: if there is an error getting the transfers.
    """
    try:
        ledger_db = get_ledger_db()
        if ledger_db is None:
            raise RuntimeError("Ledger database connection is not available")
        since = datetime.fromisoformat(since_date)
        return ledger_db.get_transfers_total(account_id, since)
    except Exception as e:
        raise e
    

def get_all_promotions() -> dict[str, str]:
    """Get the promotion details for all users.

    Returns:
        dict[str, str]: dictionary of usernames and their promotion detail.
    """
    try:
        db = get_db()
        if db is None:
            raise RuntimeError("Database connection is not available")
        return db.get_all_promotions()
    except Exception as e:
        raise e


root_agent = LlmAgent(
    name="bank_of_anthos_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to interact with Bank of Anthos promotion services. "
        "Can help customer service agents create promotions, get promotions, and delete promotions. "
        "Always ask for username when creating promotions."
    ),
    instruction=(
        "You are a helpful promotion assistant for Bank of Anthos. "
        "You can help customer service agents create promotions, get "
        "promotions, and delete promotions. One username can only have one "
        "promotion. If you are asked to create a promotion for a username "
        "that already has a promotion, you have to return the current "
        "promotion detail instead of creating a new one. When you are asked "
        "to create a promotion, you need to generate a promotion detail "
        "based on the username, if you are not told the username you can default to testuser. "
        "A promotion can either be a bonus cash "
        "deposited into the user's account when they make a deposit or a "
        "transfer. But not both. Example 1: User will get $15 bonus "
        "everytime they make a cumulative deposit of $1000. Example 2: User "
        "will get $10 bonus everytime they make a cumulative transfer of "
        "$500. If you are not told which type of promotion to create, "
        "create random type of promotion. You can also be asked to check "
        "whether a user is eligible for the promotion they have. In that "
        "case, use your available tools to get the user's transactions and "
        "check if they are eligible for the promotion. if they are "
        "eligible, credit them the bonus to their account and delete the "
        "promotion. You can login to the anthos-mcp using username testuser "
        "and password bankofanthos"
    ),
    tools=[McpToolset(
        connection_params=StreamableHTTPServerParams(
            url="http://anthos-mcp:8080/mcp"
        )
    ), create_promotion, get_promotion, delete_promotion,
       get_account_transactions, get_account_deposits_total,
       get_account_transfers_total, get_all_promotions
    ],
)
