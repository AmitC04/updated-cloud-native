"""
main.py
Main entrypoint for the YouTube Pipeline application
This orchestrates the various components of the system
"""
import os
import sys
import argparse
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_webhook_server():
    """Start the webhook server for receiving YouTube notifications"""
    logger.info("Starting YouTube Pipeline Webhook Server...")
    from webhook.webhook_app import app
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Webhook server starting on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


def run_api_server():
    """Start the REST API server for querying video data"""
    logger.info("Starting YouTube Pipeline API Server...")
    from api.api import app
    import uvicorn
    
    port = int(os.environ.get("API_PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"API server starting on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


def run_bulk_ingestion(limit=1000):
    """Run bulk ingestion of historical video data"""
    logger.info(f"Starting bulk ingestion of up to {limit} videos per channel...")
    from ingestion.bulk_ingest import main as bulk_ingest_main
    import sys
    sys.argv = ['bulk_ingest.py', '--limit', str(limit)]
    bulk_ingest_main()


def run_subscription(mode="subscribe"):
    """Subscribe or unsubscribe from YouTube channels for real-time notifications"""
    logger.info(f"Running channel {mode} operation...")
    from ingestion.subscribe import main as subscribe_main
    import sys
    sys.argv = ['subscribe.py', '--mode', mode]
    subscribe_main()


def run_resubscribe():
    """Renew existing subscriptions (typically run periodically)"""
    logger.info("Running resubscription process...")
    from scheduler.resubscribe import main as resubscribe_main
    resubscribe_main()


def run_get_channel_ids():
    """Get YouTube channel IDs for configuration"""
    logger.info("Getting YouTube channel IDs...")
    from ingestion.get_channel_ids import main as get_channel_ids_main
    get_channel_ids_main()


def main():
    parser = argparse.ArgumentParser(description='YouTube Pipeline Orchestrator')
    parser.add_argument('command', 
                       choices=['webhook', 'api', 'ingest', 'subscribe', 'unsubscribe', 
                               'resubscribe', 'get-channel-ids'],
                       help='Command to execute')
    parser.add_argument('--limit', type=int, default=1000, 
                       help='Limit for bulk ingestion (default: 1000)')
    
    args = parser.parse_args()
    
    if args.command == 'webhook':
        run_webhook_server()
    elif args.command == 'api':
        run_api_server()
    elif args.command == 'ingest':
        run_bulk_ingestion(args.limit)
    elif args.command == 'subscribe':
        run_subscription('subscribe')
    elif args.command == 'unsubscribe':
        run_subscription('unsubscribe')
    elif args.command == 'resubscribe':
        run_resubscribe()
    elif args.command == 'get-channel-ids':
        run_get_channel_ids()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()