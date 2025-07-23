#!/usr/bin/env python3
"""
Loan Origination System Application (LOSA) - Development Runner

This script provides a convenient way to run the LOSA application in development mode
with proper environment setup and configuration.
"""

import os
import sys
import logging
import argparse
import importlib.util
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def setup_logging(debug: bool = False):
    """Configure logging for development"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(), logging.FileHandler('losa_dev.log')],
    )


def load_environment():
    """Load environment variables from .env file"""
    from dotenv import load_dotenv

    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        env_example = Path(__file__).parent.parent / ".env.example"
        if env_example.exists():
            print(
                f"⚠️  No .env file found. Please copy {env_example} to .env and configure it."
            )
        else:
            print("⚠️  No .env file found. Using default environment settings.")


def check_dependencies():
    """Check if required dependencies are available"""
    try:
        # import fastapi
        # import sqlalchemy
        # import langchain
        # import langgraph
        # import uvicorn

        importlib.util.find_spec("fastapi")
        importlib.util.find_spec("sqlalchemy")
        importlib.util.find_spec("langchain")
        importlib.util.find_spec("langgraph")
        importlib.util.find_spec("uvicorn")

        print("✅ All required dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: uv sync  or  pip install -e .")
        return False


def check_database():
    """Check database connection"""
    try:
        from losa.database.config import check_database_connection

        if check_database_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            print("Please ensure PostgreSQL is running and configured correctly")
            return False
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False


def init_database():
    """Initialize database tables"""
    try:
        from losa.database.config import db_manager

        db_manager.create_tables()
        print("✅ Database tables initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False


def run_server(
    host: str = "0.0.0.0", port: int = 8000, reload: bool = True, debug: bool = False
):
    """Run the FastAPI server"""
    import uvicorn

    print(f"🚀 Starting LOSA server on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 ReDoc Documentation: http://{host}:{port}/redoc")
    print(f"❤️  Health Check: http://{host}:{port}/health")

    # Set environment variables for uvicorn
    os.environ["HOST"] = host
    os.environ["PORT"] = str(port)
    os.environ["DEBUG"] = str(debug).lower()
    os.environ["RELOAD"] = str(reload).lower()

    uvicorn.run(
        "losa.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info",
        access_log=True,
        server_header=False,
        date_header=False,
    )


def run_tests():
    """Run the test suite"""
    import pytest

    print("🧪 Running LOSA test suite...")

    # Run pytest with common options
    exit_code = pytest.main(["tests/", "-v", "--tb=short", "--durations=10"])

    return exit_code == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LOSA Development Runner")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database and exit"
    )
    parser.add_argument("--test", action="store_true", help="Run tests and exit")
    parser.add_argument(
        "--check", action="store_true", help="Run system checks and exit"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Load environment
    load_environment()

    print("🏦 Loan Origination System Application (LOSA)")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Run system checks
    if args.check:
        print("🔍 Running system checks...")
        db_ok = check_database()
        print("=" * 50)
        if db_ok:
            print("✅ All system checks passed")
            sys.exit(0)
        else:
            print("❌ System checks failed")
            sys.exit(1)

    # Initialize database if requested
    if args.init_db:
        print("🗄️  Initializing database...")
        if init_database():
            print("✅ Database initialization complete")
            sys.exit(0)
        else:
            sys.exit(1)

    # Run tests if requested
    if args.test:
        if run_tests():
            print("✅ All tests passed")
            sys.exit(0)
        else:
            print("❌ Some tests failed")
            sys.exit(1)

    # Check database before starting server
    if not check_database():
        print("❌ Cannot start server without database connection")
        print("💡 Try running with --init-db to initialize the database")
        sys.exit(1)

    # Initialize database tables if they don't exist
    init_database()

    # Start the server
    try:
        run_server(
            host=args.host, port=args.port, reload=not args.no_reload, debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
