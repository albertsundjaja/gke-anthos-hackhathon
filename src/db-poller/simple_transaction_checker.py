#!/usr/bin/env python3
"""
Simple Transaction Checker for Bank of Anthos Ledger DB

This script:
1. Reads the last count from a text file
2. Checks the current count of transactions in ledger-db
3. If different, publishes "new transaction" message to NATS
4. Updates the count in the text file
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

import psycopg2
import nats

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleTransactionChecker:
    def __init__(self):
        # Database configuration from ledger-db-config
        self.db_config = {
            'host': os.getenv('DB_HOST', 'ledger-db'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'postgresdb'),
            'user': os.getenv('POSTGRES_USER', 'admin'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password')
        }
        
        # NATS configuration
        self.nats_url = os.getenv('NATS_URL', 'nats://my-nats:4222')
        self.nats_subject = os.getenv('NATS_SUBJECT', 'msg.transaction')
        
        # State file configuration
        self.count_file_path = os.getenv('COUNT_FILE_PATH', '/app/data/transaction_count.txt')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.count_file_path), exist_ok=True)

    def get_last_count(self) -> int:
        """Read the last transaction count from the text file"""
        try:
            if os.path.exists(self.count_file_path):
                with open(self.count_file_path, 'r') as f:
                    count = int(f.read().strip())
                    logger.info(f"Last count from file: {count}")
                    return count
            else:
                logger.info("Count file doesn't exist, starting from 0")
                return 0
        except (ValueError, FileNotFoundError) as e:
            logger.warning(f"Error reading count file: {e}, starting from 0")
            return 0

    def update_count_file(self, new_count: int):
        """Update the transaction count in the text file"""
        try:
            with open(self.count_file_path, 'w') as f:
                f.write(str(new_count))
            logger.info(f"Updated count file with: {new_count}")
        except Exception as e:
            logger.error(f"Failed to update count file: {e}")
            raise

    def get_current_transaction_count(self) -> int:
        """Get the current count of transactions from the database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Count all transactions in the TRANSACTIONS table
            cursor.execute("SELECT COUNT(*) FROM transactions")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            logger.info(f"Current transaction count in DB: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to get transaction count from database: {e}")
            raise

    async def publish_new_transaction_message(self):
        """Publish a simple 'new transaction' message to NATS"""
        try:
            nc = await nats.connect(self.nats_url)
            
            message = "new transaction"
            await nc.publish(self.nats_subject, message.encode('utf-8'))
            
            logger.info(f"Published message to NATS: '{message}' on subject '{self.nats_subject}'")
            
            await nc.close()
            
        except Exception as e:
            logger.error(f"Failed to publish message to NATS: {e}")
            raise

    async def run(self):
        """Main execution flow"""
        try:
            logger.info("=== Starting Simple Transaction Checker ===")
            
            # Step 1: Get last count from text file
            last_count = self.get_last_count()
            
            # Step 2: Check current count in ledger-db
            current_count = self.get_current_transaction_count()
            
            # Step 3: Compare counts
            if current_count != last_count:
                logger.info(f"Transaction count changed: {last_count} -> {current_count}")
                
                # Step 4: Publish message to NATS
                await self.publish_new_transaction_message()
                
                # Step 5: Update count in text file
                self.update_count_file(current_count)
                
                logger.info("✅ New transaction detected and processed")
            else:
                logger.info("No new transactions detected")
            
            logger.info("=== Transaction Checker Complete ===")
            
        except Exception as e:
            logger.error(f"Error in transaction checker: {e}")
            sys.exit(1)

async def main():
    """Main entry point"""
    checker = SimpleTransactionChecker()
    await checker.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)
