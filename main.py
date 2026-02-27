"""
main.py
Main entrypoint for the YouTube Pipeline application.
Orchestrates all components: webhook server, API server, ingestion, chatbot, subscriptions.

Usage:
    python main.py webhook              # Start webhook server (receives notifications)
    python main.py api                  # Start REST API server
    python main.py ingest               # Initial bulk ingestion of 1000 videos per channel
    python main.py ingest --limit 500   # Custom video limit
    python main.py query                # Query latest videos
    python main.py query --last-24h     # Query videos from last 24 hours
    python main.py query --stats        # Show database statistics
    python main.py chatbot              # Start Streamlit chatbot
    python main.py subscribe            # Subscribe to YouTube channels (PubSubHubbub)
    python main.py unsubscribe          # Unsubscribe from YouTube channels
    python main.py all                  # Start all services (webhook + API)
"""
import os
import sys
import argparse
from datetime import datetime
import logging
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()


def run_webhook_server():
    """Start the webhook server for receiving YouTube notifications"""
    logger.info("="*80)
    logger.info("STARTING WEBHOOK SERVER (Real-time Video Ingestion)")
    logger.info("="*80)
    logger.info("Webhook server will listen for PubSubHubbub notifications from YouTube")
    
    from webhook.webhook_app import app
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Webhook server starting on {host}:{port}")
    logger.info(f"Webhook endpoint: POST {os.environ.get('WEBHOOK_BASE_URL', 'http://localhost:8080')}/webhook")
    logger.info("Waiting for YouTube notifications...")
    
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("Webhook server stopped")


def run_api_server():
    """Start the REST API server for querying video data"""
    logger.info("="*80)
    logger.info("STARTING REST API SERVER")
    logger.info("="*80)
    
    from api.api import app
    import uvicorn
    
    port = int(os.environ.get("API_PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"API server starting on {host}:{port}")
    logger.info(f"API documentation: http://{host}:{port}/docs")
    logger.info(f"API root: http://{host}:{port}/")
    
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("API server stopped")


def run_bulk_ingestion(limit=1000):
    """Run bulk ingestion of historical video data"""
    logger.info("="*80)
    logger.info("STARTING INITIAL VIDEO INGESTION (bulk_ingest)")
    logger.info("="*80)
    
    from ingestion.bulk_ingest import ingest_channel
    
    channels = [
        "https://www.youtube.com/@markets",
        "https://www.youtube.com/@ANINewsIndia",
    ]
    
    logger.info(f"Will ingest up to {limit} videos per channel")
    logger.info(f"Channels: {', '.join(channels)}")
    
    try:
        for channel in channels:
            logger.info(f"\nIngesting: {channel}")
            ingest_channel(channel, limit)
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        sys.exit(1)


def run_query(query_args):
    """Run query commands"""
    logger.info("="*80)
    logger.info("QUERYING VIDEO DATABASE")
    logger.info("="*80)
    
    from query_latest import (
        query_latest,
        query_last_24h,
        query_database_stats
    )
    
    try:
        if query_args.stats:
            query_database_stats()
        elif query_args.last_24h:
            query_last_24h()
        else:
            query_latest(query_args.limit)
    except Exception as e:
        logger.error(f"Error during query: {e}", exc_info=True)
        sys.exit(1)


def run_chatbot():
    """Start the Streamlit chatbot"""
    logger.info("="*80)
    logger.info("STARTING STREAMLIT CHATBOT")
    logger.info("="*80)
    logger.info("Opening chatbot UI in browser...")
    logger.info("Chatbot will be available at: http://localhost:8501")
    
    try:
        subprocess.run(
            ["streamlit", "run", "streamlit_app.py"],
            check=True
        )
    except FileNotFoundError:
        logger.error("Streamlit not found. Install with: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting chatbot: {e}", exc_info=True)
        sys.exit(1)


def run_subscribe(unsubscribe=False):
    """Subscribe to or unsubscribe from YouTube channels"""
    from webhook.subscribe import subscribe_all_channels, unsubscribe_all_channels
    
    logger.info("="*80)
    if unsubscribe:
        logger.info("UNSUBSCRIBING FROM YOUTUBE CHANNELS (PubSubHubbub)")
    else:
        logger.info("SUBSCRIBING TO YOUTUBE CHANNELS (PubSubHubbub)")
    logger.info("="*80)
    
    try:
        if unsubscribe:
            successful, failed = unsubscribe_all_channels()
        else:
            successful, failed = subscribe_all_channels()
        
        logger.info(f"Result: {successful} successful, {failed} failed")
        
        if failed == 0:
            logger.info("✓ All operations successful")
            return 0
        else:
            logger.warning(f"⚠ {failed} operations failed")
            return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def run_all_services():
    """Start webhook and API servers together"""
    logger.info("="*80)
    logger.info("STARTING ALL SERVICES (Webhook + API)")
    logger.info("="*80)
    logger.info("Running both servers in parallel...")
    logger.info("")
    logger.info("Webhook server: http://0.0.0.0:8080")
    logger.info("API server: http://0.0.0.0:8000/docs")
    logger.info("")
    
    import threading
    
    webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    
    webhook_thread.start()
    api_thread.start()
    
    try:
        webhook_thread.join()
        api_thread.join()
    except KeyboardInterrupt:
        logger.info("Shutting down all services...")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Pipeline - Cloud-Native AI Data Engineer Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py webhook              # Start webhook (receives real-time notifications)
  python main.py api                  # Start REST API (query videos)
  python main.py ingest               # Initial bulk ingestion (1000 videos)
  python main.py ingest --limit 500   # Ingest 500 videos per channel
  python main.py query                # Show 10 latest videos
  python main.py query --last-24h     # Show videos from last 24 hours
  python main.py query --stats        # Show database statistics
  python main.py chatbot              # Start Streamlit AI chatbot
  python main.py subscribe            # Subscribe to YouTube channels
  python main.py unsubscribe          # Unsubscribe from YouTube channels
  python main.py all                  # Start webhook + API together
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Webhook command
    subparsers.add_parser("webhook", help="Start webhook server")
    
    # API command
    subparsers.add_parser("api", help="Start REST API server")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Bulk ingestion of videos")
    ingest_parser.add_argument("--limit", type=int, default=1000, help="Videos per channel")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("--limit", type=int, default=10, help="Number of videos")
    query_parser.add_argument("--last-24h", action="store_true", help="Last 24 hours")
    query_parser.add_argument("--stats", action="store_true", help="Database statistics")
    
    # Chatbot command
    subparsers.add_parser("chatbot", help="Start Streamlit chatbot")
    
    # Subscribe command
    subparsers.add_parser("subscribe", help="Subscribe to YouTube channels")
    subparsers.add_parser("unsubscribe", help="Unsubscribe from YouTube channels")
    
    # All command
    subparsers.add_parser("all", help="Start all services (webhook + API)")
    
    args = parser.parse_args()
    
    logger.info(f"YouTube Pipeline - Started at {datetime.now().isoformat()}")
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "webhook":
            run_webhook_server()
        elif args.command == "api":
            run_api_server()
        elif args.command == "ingest":
            run_bulk_ingestion(args.limit)
        elif args.command == "query":
            run_query(args)
        elif args.command == "chatbot":
            run_chatbot()
        elif args.command == "subscribe":
            sys.exit(run_subscribe(unsubscribe=False))
        elif args.command == "unsubscribe":
            sys.exit(run_subscribe(unsubscribe=True))
        elif args.command == "all":
            run_all_services()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
