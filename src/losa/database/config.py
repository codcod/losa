import os
from typing import AsyncGenerator, Generator
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .models import Base


class DatabaseConfig:
    """Database configuration class"""

    def __init__(self):
        # Database connection parameters
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'losa')
        self.db_user = os.getenv('DB_USER', 'losa_user')
        self.db_password = os.getenv('DB_PASSWORD', 'losa_password')

        # Connection pool settings
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))

        # SSL settings
        self.ssl_mode = os.getenv('DB_SSL_MODE', 'disable')

        # Debug settings
        self.echo_sql = os.getenv('DB_ECHO', 'false').lower() == 'true'

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL"""
        url = f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'
        if self.ssl_mode != 'disable':
            url += f'?sslmode={self.ssl_mode}'
        return url

    @property
    def async_database_url(self) -> str:
        """Get asynchronous database URL"""
        url = f'postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'
        if self.ssl_mode != 'disable':
            url += f'?ssl={self.ssl_mode}'
        return url


# Global database configuration
db_config = DatabaseConfig()


# Synchronous engine and session factory
sync_engine = create_engine(
    db_config.sync_database_url,
    poolclass=QueuePool,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_timeout=db_config.pool_timeout,
    pool_recycle=db_config.pool_recycle,
    echo=db_config.echo_sql,
)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# Asynchronous engine and session factory
async_engine = create_async_engine(
    db_config.async_database_url,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_timeout=db_config.pool_timeout,
    pool_recycle=db_config.pool_recycle,
    echo=db_config.echo_sql,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# Context managers for database sessions


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Get synchronous database session"""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


# Dependency functions for FastAPI


def get_db_session() -> Generator[Session, None, None]:
    """Dependency function for FastAPI to get database session"""
    with get_sync_session() as session:
        yield session


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency function for FastAPI to get database session"""
    async with get_async_session() as session:
        yield session


# Database initialization functions


def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=sync_engine)


async def init_async_database():
    """Initialize database tables asynchronously"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def drop_database():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=sync_engine)


async def drop_async_database():
    """Drop all database tables asynchronously (use with caution!)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Health check functions


def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        with get_sync_session() as session:
            session.execute(text('SELECT 1'))
            return True
    except Exception:
        return False


async def check_async_database_connection() -> bool:
    """Check if async database connection is working"""
    try:
        async with get_async_session() as session:
            await session.execute(text('SELECT 1'))
            return True
    except Exception:
        return False


# Migration helpers


def get_current_schema_version() -> str:
    """Get current database schema version"""
    try:
        with get_sync_session() as session:
            result = session.execute(
                text(
                    'SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1'
                )
            ).fetchone()
            return result[0] if result else 'none'
    except Exception:
        return 'unknown'


async def get_current_schema_version_async() -> str:
    """Get current database schema version asynchronously"""
    try:
        async with get_async_session() as session:
            result = await session.execute(
                text(
                    'SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1'
                )
            )
            row = result.fetchone()
            return row[0] if row else 'none'
    except Exception:
        return 'unknown'


# Transaction helpers


@contextmanager
def database_transaction():
    """Context manager for explicit database transactions"""
    with get_sync_session() as session:
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@asynccontextmanager
async def async_database_transaction():
    """Async context manager for explicit database transactions"""
    async with get_async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


# Configuration management


class DatabaseManager:
    """Database manager for handling connections and operations"""

    def __init__(self):
        self.sync_engine = sync_engine
        self.async_engine = async_engine
        self.sync_session_factory = SyncSessionLocal
        self.async_session_factory = AsyncSessionLocal

    def get_sync_session(self) -> Session:
        """Get a synchronous session"""
        return self.sync_session_factory()

    def get_async_session(self) -> AsyncSession:
        """Get an asynchronous session"""
        return self.async_session_factory()

    async def close_connections(self):
        """Close all database connections"""
        await self.async_engine.dispose()
        self.sync_engine.dispose()

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.sync_engine)

    async def create_tables_async(self):
        """Create all database tables asynchronously"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(bind=self.sync_engine)

    async def drop_tables_async(self):
        """Drop all database tables asynchronously"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# Global database manager instance
db_manager = DatabaseManager()
