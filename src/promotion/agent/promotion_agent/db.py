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
db manages interactions with the underlying promotion database
"""

import logging
from sqlalchemy import create_engine, MetaData, Table, Column, String, Text, DateTime
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class PromotionDb:
    """
    PromotionDb provides a set of helper functions over SQLAlchemy
    to handle database operations for the promotion service
    """

    def __init__(self, uri: str, logger: logging.Logger = None):
        """
        Initialize the PromotionDb with database connection.
        
        Args:
            uri (str): Database connection URI
            logger (logging.Logger): Logger instance for debugging
        """
        self.engine = create_engine(uri)
        self.logger = logger or logging.getLogger(__name__)
        
        # Define the promotions table schema
        self.metadata = MetaData()
        self.promotions_table = Table(
            'promotions',
            self.metadata,
            Column('username', String(64), primary_key=True, nullable=False),
            Column('detail', Text, nullable=False),
            Column('created_at', DateTime, nullable=False),
        )

    def create_promotion(self, username: str, detail: str) -> None:
        """
        Create a new promotion for a user.
        
        Args:
            username (str): The username to create promotion for
            detail (str): The promotion details/description
                
        Raises:
            SQLAlchemyError: If there was an issue with the database
        """
        try:
            promotion_data = {
                'username': username,
                'detail': detail,
                'created_at': datetime.now()
            }
            
            statement = self.promotions_table.insert().values(promotion_data)
            self.logger.debug('QUERY: %s', str(statement))
            
            with self.engine.connect() as conn:
                conn.execute(statement)
                conn.commit()
                
        except SQLAlchemyError as e:
            self.logger.error("Database error creating promotion: %s", str(e))
            raise e
        except Exception as e:
            self.logger.error("Unexpected error creating promotion: %s", str(e))
            raise e

    def get_promotion_by_username(self, username: str) -> tuple[str, datetime] | None:
        """
        Get the promotion for a specific username.
        
        Args:
            username (str): The username to get promotions for
            
        Returns:
            tuple[str, datetime] | None: the promotion detail and creation time, or None if not found
            
        Raises:
            SQLAlchemyError: If there was an issue with the database
        """
        try:
            statement = self.promotions_table.select().where(
                self.promotions_table.c.username == username
            )
            
            self.logger.debug('QUERY: %s', str(statement))
            
            with self.engine.connect() as conn:
                result = conn.execute(statement)
                # Use mappings() to get dictionary-like access
                for row in result.mappings():
                    return (row['detail'], row['created_at'])
                
                return None
                
        except SQLAlchemyError as e:
            self.logger.error("Database error getting promotions: %s", str(e))
            raise e
        except Exception as e:
            self.logger.error("Unexpected error getting promotions: %s", str(e))
            raise e

    def delete_promotion(self, username: str) -> None:
        """
        Delete a promotion by its ID.
        
        Args:
            promotion_id (int): The promotion ID to delete
            
        Raises:
            SQLAlchemyError: If there was an issue with the database
        """
        try:
            statement = self.promotions_table.delete().where(
                self.promotions_table.c.username == username
            )
            
            self.logger.debug('QUERY: %s', str(statement))
            
            with self.engine.connect() as conn:
                conn.execute(statement)
                conn.commit()
                
        except SQLAlchemyError as e:
            self.logger.error("Database error deleting promotion: %s", str(e))
            raise e
        except Exception as e:
            self.logger.error("Unexpected error deleting promotion: %s", str(e))
            raise e

    def get_all_promotions(self) -> dict[str, str]:
        """Get the promotion details for all users.

        Returns:
            dict[str, str]: dictionary of usernames and their promotion detail.
        """
        try:
            statement = self.promotions_table.select()
            self.logger.debug('QUERY: %s', str(statement))
            with self.engine.connect() as conn:
                result = conn.execute(statement)
                return {row['username']: row['detail'] for row in result.mappings()}
        except SQLAlchemyError as e:
            self.logger.error("Database error getting all promotions: %s", str(e))
            raise e
        except Exception as e:
            self.logger.error("Unexpected error getting all promotions: %s", str(e))
            raise e