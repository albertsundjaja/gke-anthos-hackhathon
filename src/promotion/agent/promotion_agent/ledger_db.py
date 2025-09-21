# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ledger_db manages direct interactions with the ledger database
to access transaction history for promotion eligibility checks
"""

import logging
from sqlalchemy import (
    create_engine, MetaData, Table, Column, BigInteger, String, Integer,
    DateTime
)
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import List, Dict, Any


class LedgerDb:
    """
    LedgerDb provides direct access to the ledger database
    to retrieve transaction history for any account
    """

    def __init__(self, uri: str, logger: logging.Logger = None):
        """
        Initialize the LedgerDb with database connection.
        
        Args:
            uri (str): Database connection URI
            logger (logging.Logger): Logger instance for debugging
        """
        self.engine = create_engine(uri)
        self.logger = logger or logging.getLogger(__name__)
        
        # Define the transactions table schema (from ledger-db)
        self.metadata = MetaData()
        self.transactions_table = Table(
            'transactions',
            self.metadata,
            Column('transaction_id', BigInteger, primary_key=True),
            Column('from_acct', String(10), nullable=False),
            Column('to_acct', String(10), nullable=False),
            Column('from_route', String(9), nullable=False),
            Column('to_route', String(9), nullable=False),
            Column('amount', Integer, nullable=False),
            Column('timestamp', DateTime, nullable=False),
        )

    def get_account_transactions(
            self, account_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific account (both incoming and outgoing).
        
        Args:
            account_id (str): The account ID to get transactions for
            limit (int): Maximum number of transactions to return
            
        Returns:
            List[Dict[str, Any]]: List of transaction dictionaries
            
        Raises:
            SQLAlchemyError: If there was an issue with the database
        """
        try:
            # Get transactions where this account is either sender or receiver
            statement = self.transactions_table.select().where(
                (self.transactions_table.c.from_acct == account_id) |
                (self.transactions_table.c.to_acct == account_id)
            ).order_by(
                self.transactions_table.c.timestamp.desc()
            ).limit(limit)
            
            self.logger.debug('QUERY: %s', str(statement))
            
            with self.engine.connect() as conn:
                result = conn.execute(statement)
                transactions = []
                
                for row in result.mappings():
                    transaction = {
                        'transaction_id': row['transaction_id'],
                        'from_account': row['from_acct'],
                        'to_account': row['to_acct'],
                        'from_routing': row['from_route'],
                        'to_routing': row['to_route'],
                        'amount': row['amount'],
                        'timestamp': row['timestamp'],
                        'is_debit': row['from_acct'] == account_id,  # True if outgoing
                        'is_credit': row['to_acct'] == account_id,   # True if incoming
                    }
                    transactions.append(transaction)
                
                self.logger.debug(
                    "RESULT: Fetched %d transactions for account %s",
                    len(transactions), account_id
                )
                return transactions
                
        except SQLAlchemyError as e:
            self.logger.error("Database error getting transactions: %s", str(e))
            raise e
        except Exception as e:
            self.logger.error("Unexpected error getting transactions: %s", str(e))
            raise e

    def get_deposits_total(
            self, account_id: str, since_date: datetime = None
    ) -> int:
        """
        Get total amount of deposits (incoming transactions) for an account.
        
        Args:
            account_id (str): The account ID to check
            since_date (datetime): Only count deposits since this date (optional)
            
        Returns:
            int: Total deposit amount in cents
        """
        try:
            statement = self.transactions_table.select().where(
                self.transactions_table.c.to_acct == account_id
            )
            
            if since_date:
                statement = statement.where(
                    self.transactions_table.c.timestamp >= since_date
                )
            
            self.logger.debug('QUERY: %s', str(statement))
            
            with self.engine.connect() as conn:
                result = conn.execute(statement)
                total = sum(row['amount'] for row in result.mappings())
                
                self.logger.debug(
                    "RESULT: Total deposits for account %s: %d cents",
                    account_id, total
                )
                return total
                
        except SQLAlchemyError as e:
            self.logger.error("Database error getting deposits: %s", str(e))
            raise e
        except Exception as e:
            self.logger.error("Unexpected error getting deposits: %s", str(e))
            raise e

    def get_transfers_total(
            self, account_id: str, since_date: datetime = None
    ) -> int:
        """
        Get total amount of transfers (outgoing transactions) for an account.
        
        Args:
            account_id (str): The account ID to check
            since_date (datetime): Only count transfers since this date (optional)
            
        Returns:
            int: Total transfer amount in cents
        """
        try:
            statement = self.transactions_table.select().where(
                self.transactions_table.c.from_acct == account_id
            )
            
            if since_date:
                statement = statement.where(
                    self.transactions_table.c.timestamp >= since_date
                )
            
            self.logger.debug('QUERY: %s', str(statement))
            
            with self.engine.connect() as conn:
                result = conn.execute(statement)
                total = sum(row['amount'] for row in result.mappings())
                
                self.logger.debug(
                    "RESULT: Total transfers for account %s: %d cents",
                    account_id, total
                )
                return total
                
        except SQLAlchemyError as e:
            self.logger.error("Database error getting transfers: %s", str(e))
            raise e
        except Exception as e:
            self.logger.error("Unexpected error getting transfers: %s", str(e))
            raise e
