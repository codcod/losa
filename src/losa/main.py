import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn
from datetime import datetime

from .database.config import db_manager, check_database_connection
from .api.loan_routes import router as loan_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('losa.log')],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info('Starting Loan Origination System...')

    # Initialize database
    try:
        if not check_database_connection():
            logger.error('Database connection failed!')
            raise Exception('Cannot connect to database')

        # Create tables if they don't exist
        db_manager.create_tables()
        logger.info('Database initialized successfully')

    except Exception as e:
        logger.error(f'Failed to initialize database: {str(e)}')
        raise

    logger.info('Application startup completed')

    yield

    # Shutdown
    logger.info('Shutting down Loan Origination System...')
    await db_manager.close_connections()
    logger.info('Application shutdown completed')


# Create FastAPI application
app = FastAPI(
    title='Loan Origination System (LOSA)',
    description="""
    A comprehensive loan origination system built with LangChain and LangGraph.

    ## Features

    * **Complete Loan Application Management** - Create, update, and track loan applications
    * **Automated Workflow Processing** - AI-powered document verification, credit assessment, and risk evaluation
    * **Document Management** - Upload, verify, and manage loan-related documents
    * **Real-time Status Tracking** - Monitor application progress through the origination workflow
    * **Underwriter Assignment** - Assign and manage human review when needed
    * **Comprehensive Reporting** - Statistics and insights on loan portfolio

    ## Workflow Stages

    1. **Application Creation** - Capture applicant information and loan details
    2. **Document Upload** - Collect required documentation
    3. **Validation** - Verify application completeness and basic requirements
    4. **Document Verification** - AI-powered document analysis and validation
    5. **Credit Check** - Credit bureau integration and score analysis
    6. **Risk Assessment** - Comprehensive risk evaluation using multiple factors
    7. **Decision Making** - Automated approval/rejection with human review when needed
    8. **Final Processing** - Loan funding and completion

    Built with LangChain for AI chains and LangGraph for workflow orchestration.
    """,
    version='1.0.0',
    contact={
        'name': 'LOSA Development Team',
        'email': 'dev@losa.com',
    },
    license_info={
        'name': 'MIT',
    },
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc',
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Trust host middleware
trusted_hosts = os.getenv('TRUSTED_HOSTS', 'localhost,127.0.0.1').split(',')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)


# Custom middleware for request logging
@app.middleware('http')
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()

    # Log request
    logger.info(f'Request: {request.method} {request.url}')

    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = (datetime.utcnow() - start_time).total_seconds()

        # Log response
        logger.info(
            f'Response: {response.status_code} for {request.method} {request.url} '
            f'(processed in {process_time:.3f}s)'
        )

        # Add processing time header
        response.headers['X-Process-Time'] = str(process_time)

        return response

    except Exception as e:
        logger.error(f'Request failed: {request.method} {request.url} - {str(e)}')
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f'Unhandled exception for {request.method} {request.url}: {str(exc)}',
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat(),
            'path': str(request.url),
        },
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        f'HTTP exception for {request.method} {request.url}: {exc.status_code} - {exc.detail}'
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': exc.detail,
            'status_code': exc.status_code,
            'timestamp': datetime.utcnow().isoformat(),
            'path': str(request.url),
        },
    )


# Include routers
app.include_router(loan_router)


# Root endpoint
@app.get('/', tags=['root'])
async def root():
    """Root endpoint with API information"""
    return {
        'message': 'Welcome to the Loan Origination System (LOSA)',
        'version': '1.0.0',
        'description': 'AI-powered loan origination system built with LangChain and LangGraph',
        'documentation': '/docs',
        'health_check': '/health',
        'api_prefix': '/api/v1',
        'timestamp': datetime.utcnow().isoformat(),
    }


# Health check endpoint
@app.get('/health', tags=['health'])
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database connection
        db_healthy = check_database_connection()

        # Check basic system health
        system_health = {
            'status': 'healthy' if db_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'components': {
                'database': 'healthy' if db_healthy else 'unhealthy',
                'api': 'healthy',
                'workflows': 'healthy',  # Could add more detailed checks
            },
        }

        if not db_healthy:
            system_health['issues'] = ['Database connection failed']

        status_code = 200 if db_healthy else 503

        return JSONResponse(content=system_health, status_code=status_code)

    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return JSONResponse(
            content={
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
            },
            status_code=503,
        )


# Ready endpoint (for Kubernetes readiness probes)
@app.get('/ready', tags=['health'])
async def ready_check():
    """Readiness probe endpoint"""
    try:
        db_ready = check_database_connection()
        if db_ready:
            return {'status': 'ready', 'timestamp': datetime.utcnow().isoformat()}
        else:
            return JSONResponse(
                content={'status': 'not ready', 'reason': 'database not available'},
                status_code=503,
            )
    except Exception as e:
        return JSONResponse(
            content={'status': 'not ready', 'reason': str(e)}, status_code=503
        )


# Live endpoint (for Kubernetes liveness probes)
@app.get('/live', tags=['health'])
async def liveness_check():
    """Liveness probe endpoint"""
    return {'status': 'alive', 'timestamp': datetime.utcnow().isoformat()}


# Metrics endpoint (basic metrics)
@app.get('/metrics', tags=['monitoring'])
async def get_metrics():
    """Basic metrics endpoint"""
    from .services.loan_service import LoanService

    try:
        loan_service = LoanService()
        stats = loan_service.get_application_statistics()

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'application_metrics': stats,
            'system_metrics': {
                'uptime': 'unknown',  # Would need to track startup time
                'version': '1.0.0',
            },
        }

    except Exception as e:
        logger.error(f'Metrics endpoint failed: {str(e)}')
        return JSONResponse(
            content={'error': 'Failed to retrieve metrics', 'detail': str(e)},
            status_code=500,
        )


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title='Loan Origination System API',
        version='1.0.0',
        description=app.description,
        routes=app.routes,
    )

    # Add custom schema extensions
    openapi_schema['info']['x-logo'] = {
        'url': 'https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png'
    }

    # Add security schemes if authentication is implemented
    # openapi_schema["components"]["securitySchemes"] = {
    #     "BearerAuth": {
    #         "type": "http",
    #         "scheme": "bearer",
    #         "bearerFormat": "JWT"
    #     }
    # }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Development server configuration
if __name__ == '__main__':
    # Load environment variables
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    reload = os.getenv('RELOAD', 'true').lower() == 'true'

    logger.info(f'Starting server on {host}:{port}')
    logger.info(f'Debug mode: {debug}')
    logger.info(f'Auto-reload: {reload}')

    uvicorn.run(
        'losa.main:app',
        host=host,
        port=port,
        reload=reload,
        log_level='info' if not debug else 'debug',
        access_log=True,
        server_header=False,
        date_header=False,
    )
