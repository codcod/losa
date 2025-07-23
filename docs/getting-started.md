# Getting Started with LOSA

This guide will help you set up and run the Loan Origination System Application (LOSA) on your local development environment.

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.13+
- PostgreSQL 12+
- Git
- OpenAI API Key

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd losa

# Create Python environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (minimum required):
# DB_HOST=localhost
# DB_NAME=losa
# DB_USER=losa_user
# DB_PASSWORD=your_password
# OPENAI_API_KEY=your_openai_api_key
```

### 3. Setup Database

```bash
# Create PostgreSQL database and user
createdb losa
createuser losa_user
psql -c "ALTER USER losa_user PASSWORD 'your_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE losa TO losa_user;"
```

### 4. Run the Application

```bash
# Simple way - using the run script
python run.py

# Or manually
python -m losa.main
```

### 5. Test the Setup

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Run example workflow
python examples/example_loan_workflow.py
```

## 🐳 Docker Quick Start (Even Faster!)

If you have Docker installed:

```bash
# Clone repository
git clone <repository-url>
cd losa

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env

# Start all services
docker-compose up -d

# Check if running
docker-compose ps

# View logs
docker-compose logs losa

# Access the API
open http://localhost:8000/docs
```

## 📋 Detailed Setup Instructions

### Environment Setup Options

#### Option A: Using uv (Recommended - Faster)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

#### Option B: Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Database Setup Options

#### Option A: Local PostgreSQL

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE losa;
CREATE USER losa_user WITH PASSWORD 'losa_password';
GRANT ALL PRIVILEGES ON DATABASE losa TO losa_user;
\q
```

#### Option B: Docker PostgreSQL

```bash
# Start PostgreSQL in Docker
docker run -d \
  --name losa_postgres \
  -e POSTGRES_DB=losa \
  -e POSTGRES_USER=losa_user \
  -e POSTGRES_PASSWORD=losa_password \
  -p 5432:5432 \
  postgres:15-alpine
```

### Configuration

Create your `.env` file from the template:

```bash
cp .env.example .env
```

**Minimum required configuration:**

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=losa
DB_USER=losa_user
DB_PASSWORD=losa_password

# OpenAI API (required for AI features)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Application
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 🧪 Testing Your Setup

### 1. Basic Health Check

```bash
# Start the application
python run.py

# In another terminal, test the health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-01T12:00:00Z",
#   "components": {
#     "database": "healthy",
#     "api": "healthy",
#     "workflows": "healthy"
#   }
# }
```

### 2. API Documentation

Visit http://localhost:8000/docs to see the interactive API documentation.

### 3. Run Example Workflow

```bash
# Run the complete loan workflow example
python examples/example_loan_workflow.py
```

This will:
- Create a sample loan application
- Add required documents
- Process through the AI workflow
- Show the decision results

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=losa --cov-report=html

# Run specific test
pytest tests/test_loan_service.py -v
```

## 🔧 Development Workflow

### Project Structure

```
losa/
├── src/losa/           # Main application code
│   ├── models/         # Pydantic data models
│   ├── workflows/      # LangGraph workflows
│   ├── chains/         # LangChain AI chains
│   ├── services/       # Business logic
│   ├── api/           # FastAPI routes
│   ├── database/      # Database models & config
│   └── main.py        # FastAPI application
├── tests/             # Test files
├── examples/          # Example scripts
├── docker/           # Docker configuration
└── docs/            # Documentation
```

### Running in Development Mode

```bash
# With auto-reload and debug logging
python run.py --debug

# Or with custom host/port
python run.py --host 127.0.0.1 --port 8080
```

### Working with the Database

```bash
# Initialize/reset database tables
python run.py --init-db

# Check database connection
python run.py --check

# View database with Adminer (if using Docker)
docker-compose --profile tools up -d adminer
open http://localhost:8080
```

### Using Docker for Development

```bash
# Start development environment
docker-compose --profile dev up -d

# View development logs
docker-compose logs -f losa-dev

# Access development container
docker-compose exec losa-dev bash

# Stop development environment
docker-compose --profile dev down
```

## 🎯 First API Call

Once everything is running, try creating your first loan application:

```bash
curl -X POST "http://localhost:8000/api/v1/loans/" \
  -H "Content-Type: application/json" \
  -d '{
    "personal_info": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "5551234567",
      "ssn": "123-45-6789",
      "date_of_birth": "1990-01-01T00:00:00Z",
      "marital_status": "single",
      "dependents": 0,
      "address": {
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "12345"
      }
    },
    "employment_info": {
      "status": "employed",
      "employer_name": "Tech Corp",
      "job_title": "Software Engineer",
      "annual_income": 80000,
      "monthly_income": 6666.67
    },
    "financial_info": {
      "monthly_rent_mortgage": 1500,
      "monthly_debt_payments": 300,
      "savings_balance": 10000
    },
    "loan_details": {
      "loan_type": "personal",
      "requested_amount": 25000,
      "requested_term_months": 60,
      "purpose": "Debt consolidation"
    }
  }'
```

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL is running
pg_ctl status

# Test connection manually
psql -h localhost -U losa_user -d losa

# Check environment variables
echo $DB_HOST $DB_NAME $DB_USER
```

#### OpenAI API Errors
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or use different port
python run.py --port 8001
```

#### Permission Errors
```bash
# Fix upload directory permissions
mkdir -p uploads logs
chmod 755 uploads logs

# On Docker
docker-compose exec losa chown -R losa:losa /app/uploads
```

### Getting Help

1. **Check the logs:**
   ```bash
   tail -f losa.log
   # or for Docker
   docker-compose logs -f losa
   ```

2. **Run system checks:**
   ```bash
   python run.py --check
   ```

3. **Verify installation:**
   ```bash
   python -c "import losa; print('LOSA imported successfully')"
   ```

4. **Check API health:**
   ```bash
   curl -s http://localhost:8000/health | python -m json.tool
   ```

## 🎓 Next Steps

### Learn the System

1. **Read the README.md** - Comprehensive system overview
2. **Explore the API** - Visit http://localhost:8000/docs
3. **Run Examples** - Check the `examples/` directory
4. **Study the Code** - Start with `src/losa/main.py`

### Try Different Workflows

```bash
# Process a loan application manually
python examples/example_loan_workflow.py

# Test different loan types and amounts
# Modify the examples and see different outcomes
```

### Development Tasks

- **Add New Loan Types** - Extend the `LoanType` enum
- **Create Custom Chains** - Build new LangChain processing chains
- **Add Integrations** - Connect to real credit bureaus or document services
- **Enhance Workflows** - Modify the LangGraph workflow logic

### Production Deployment

When ready for production:

1. **Set production environment:**
   ```bash
   # Update .env
   DEBUG=false
   ENVIRONMENT=production
   ```

2. **Use production database:**
   ```bash
   # Configure production PostgreSQL
   DB_HOST=your-prod-db-host.com
   DB_SSL_MODE=require
   ```

3. **Deploy with Docker:**
   ```bash
   docker-compose --profile production up -d
   ```

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **ReDoc Documentation:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics

- **LangChain Documentation:** https://python.langchain.com/
- **LangGraph Documentation:** https://langchain-ai.github.io/langgraph/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

🎉 **Congratulations!** You now have LOSA running locally. Start exploring the AI-powered loan origination workflows!