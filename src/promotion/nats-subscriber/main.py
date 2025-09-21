#!/usr/bin/env python3
"""
Simple NATS Transaction Subscriber for Bank of Anthos

This service:
1. Connects to NATS server
2. Subscribes to 'msg.transaction' subject
3. Logs received "new transaction" messages to console
"""

import asyncio
import os
import logging
import signal
import sys
import aiohttp
import json
import nats


# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CS_AGENT_SESSION_URL = "http://cs-agent:8080/apps/cs-agent/users/nats-user/sessions"
CS_AGENT_RUN_URL = "http://cs-agent:8080/run"


class NATSTransactionSubscriber:
    def __init__(self):
        # NATS configuration
        self.nats_url = os.getenv('NATS_URL', 'nats://simple-nats:4222')
        self.nats_subject = os.getenv('NATS_SUBJECT', 'msg.transaction')
        self.nc = None
        self.running = True

    async def message_handler(self, msg):
        """Handle incoming NATS messages"""
        try:
            # Decode the message
            message_data = msg.data.decode('utf-8')

            # Log the received message
            logger.info(f"📨 Received message: '{message_data}' on subject: "
                        f"'{msg.subject}'")

            # Check if it's a "new transaction" message
            if message_data == "new transaction":
                logger.info("🎯 New transaction detected! Logging to console.")
                timeout = aiohttp.ClientTimeout(total=600, connect=60, sock_read=60, sock_connect=60)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(CS_AGENT_SESSION_URL) as response:
                        logger.info(f"🔄 Response from CS Agent: {response}")
                        resp = await response.json()
                        logger.info(f"🔄 Response JSON from CS Agent: {resp}")
                        session_id = resp['id']
                        check_promotion_body = {
                            "app_name": "cs-agent",
                            "user_id": "nats-user", 
                            "session_id": session_id,
                            "new_message": { "role": "user", "parts": [ { "text": "Check whether all users who have promotions are eligible for them." } ] }
                        }
                    async with session.post(CS_AGENT_RUN_URL, json=check_promotion_body) as response:
                        resp = await response.json()
                        if resp and len(resp) > 0:
                            last_event = resp[-1]  # Get the last event
                            if 'content' in last_event and 'parts' in last_event['content']:
                                parts = last_event['content']['parts']
                                if parts and len(parts) > 0 and 'text' in parts[0]:
                                    response_message = parts[0]['text']
                                    logger.info(f"✅ Promotion Agent Response: {response_message}")
                                else:
                                    logger.warning("No text found in response parts")
                            else:
                                logger.warning("No content found in last event")
                        else:
                            logger.warning("Empty response received")
                # Future functionality can be added here
            else:
                logger.info(f"ℹ️  Other message received: {message_data}")

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

    async def connect_and_subscribe(self):
        """Connect to NATS and subscribe to the transaction subject"""
        try:
            logger.info(f"🔌 Connecting to NATS at: {self.nats_url}")
            self.nc = await nats.connect(self.nats_url)
            logger.info("✅ Connected to NATS successfully")

            # Subscribe to the transaction subject
            logger.info(f"📡 Subscribing to subject: {self.nats_subject}")
            await self.nc.subscribe(self.nats_subject, cb=self.message_handler)
            logger.info("✅ Subscription established successfully")

        except Exception as e:
            logger.error(f"❌ Failed to connect to NATS or subscribe: {e}")
            raise

    async def disconnect(self):
        """Gracefully disconnect from NATS"""
        if self.nc:
            try:
                logger.info("🔌 Disconnecting from NATS...")
                await self.nc.close()
                logger.info("✅ Disconnected from NATS successfully")
            except Exception as e:
                logger.error(f"❌ Error during NATS disconnection: {e}")

    async def run(self):
        """Main execution loop"""
        try:
            logger.info("=== Starting NATS Transaction Subscriber ===")

            # Connect and subscribe
            await self.connect_and_subscribe()

            # Keep the service running
            logger.info("🚀 Service is running, waiting for messages...")
            logger.info("Press Ctrl+C to stop the service")

            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Error in subscriber service: {e}")
            raise
        finally:
            await self.disconnect()

    def stop(self):
        """Stop the service"""
        logger.info("🛑 Stopping service...")
        self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
    subscriber.stop()


# Global subscriber instance for signal handling
subscriber = None


async def main():
    """Main entry point"""
    global subscriber

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    subscriber = NATSTransactionSubscriber()
    await subscriber.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Service interrupted by user")
    except Exception as e:
        logger.error(f"❌ Service failed: {e}")
        sys.exit(1)
