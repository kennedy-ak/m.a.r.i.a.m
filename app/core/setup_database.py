#!/usr/bin/env python3
"""
Database setup script for the Personal Assistant Bot
This script creates the database and tables if they don't exist
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from models import Base, create_tables
from dotenv import load_dotenv

load_dotenv()


def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    # Parse database URL to get database name
    # Format: postgresql://username:password@host:port/database_name
    try:
        parts = database_url.split('/')
        db_name = parts[-1]
        base_url = '/'.join(parts[:-1])
        
        print(f"🔍 Checking if database '{db_name}' exists...")
        
        # Connect to PostgreSQL server (not to a specific database)
        server_url = f"{base_url}/postgres"
        engine = create_engine(server_url)
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if result.fetchone():
                print(f"✅ Database '{db_name}' already exists")
            else:
                print(f"🔨 Creating database '{db_name}'...")
                conn.execute(text("COMMIT"))  # End any transaction
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"✅ Database '{db_name}' created successfully")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Error managing database: {e}")
        sys.exit(1)


def setup_tables():
    """Create all tables"""
    try:
        print("🔨 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully")
        
        # Verify tables were created
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in result]
            
            if 'tasks' in tables:
                print("✅ Tasks table verified")
            else:
                print("❌ Tasks table not found")
                sys.exit(1)
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


def verify_environment():
    """Verify all required environment variables are set"""
    required_vars = [
        'DATABASE_URL',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
        'OPENAI_API_KEY',
        'MNOTIFY_API_KEY',
        'YOUR_PHONE_NUMBER'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all variables are set.")
        return False
    
    print("✅ All required environment variables are set")
    return True


def test_database_connection():
    """Test database connection"""
    try:
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        engine.dispose()
        print("✅ Database connection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Setting up Personal Assistant Bot Database...")
    print("=" * 50)
    
    # Step 1: Verify environment variables
    if not verify_environment():
        sys.exit(1)
    
    # Step 2: Create database if needed
    create_database_if_not_exists()
    
    # Step 3: Test database connection
    if not test_database_connection():
        sys.exit(1)
    
    # Step 4: Create tables
    setup_tables()
    
    print("=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Make sure your Telegram bot token is valid")
    print("2. Get your Telegram chat ID by messaging your bot")
    print("3. Verify your OpenAI API key has sufficient credits")
    print("4. Check your Mnotify API key and account balance")
    print("5. Run the application: python main.py")


if __name__ == "__main__":
    main()