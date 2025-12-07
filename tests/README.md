# 🧪 Agent47 Test Suite

This directory contains comprehensive tests for the entire Agent47 platform, including backend services, frontend components, and integration tests.

## 📁 Directory Structure

```
tests/
├── README.md                 # This file
├── conftest.py              # Pytest configuration and fixtures
├── requirements.txt         # Test-specific dependencies
├── backend/                 # Backend tests
│   ├── unit/               # Unit tests
│   │   ├── core/           # Core service tests
│   │   ├── agents/         # Agent-specific tests
│   │   └── api/            # API endpoint tests
│   ├── integration/        # Integration tests
│   │   ├── database/       # Database integration tests
│   │   ├── redis/          # Redis integration tests
│   │   ├── kafka/          # Kafka integration tests
│   │   └── ai/             # AI service integration tests
│   ├── e2e/                # End-to-end tests
│   │   ├── user_flows/     # User journey tests
│   │   ├── agent_flows/    # Agent interaction tests
│   │   └── api_flows/      # API workflow tests
│   └── performance/        # Performance tests
│       ├── load/           # Load testing
│       ├── stress/         # Stress testing
│       └── benchmark/      # Benchmark tests
├── frontend/                # Frontend tests
│   ├── unit/               # Component unit tests
│   ├── integration/        # Integration tests
│   ├── e2e/                # End-to-end tests
│   └── visual/             # Visual regression tests
├── fixtures/                # Test data and fixtures
│   ├── data/               # Test data files
│   ├── images/             # Test images
│   └── models/             # Test model files
├── utils/                   # Test utilities
│   ├── helpers.py          # Test helper functions
│   ├── mocks.py            # Mock objects
│   └── factories.py        # Test data factories
└── reports/                 # Test reports and coverage
    ├── coverage/           # Coverage reports
    ├── html/               # HTML test reports
    └── junit/              # JUnit XML reports
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- pytest, jest, and other testing frameworks

### Running Tests

#### Backend Tests

   ```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all backend tests
pytest tests/backend/

# Run specific test categories
pytest tests/backend/unit/          # Unit tests
pytest tests/backend/integration/   # Integration tests
pytest tests/backend/e2e/          # End-to-end tests
pytest tests/backend/performance/  # Performance tests

# Run with coverage
pytest tests/backend/ --cov=backend --cov-report=html

# Run specific agent tests
pytest tests/backend/unit/agents/test_aria.py
pytest tests/backend/unit/agents/test_clara.py
```

#### Frontend Tests

   ```bash
# Install dependencies
cd frontend && npm install

# Run all frontend tests
npm test

# Run specific test types
npm run test:unit          # Unit tests
npm run test:integration   # Integration tests
npm run test:e2e          # End-to-end tests
npm run test:visual       # Visual regression tests

# Run with coverage
npm run test:coverage
```

#### Integration Tests

   ```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/backend/integration/

# Run end-to-end tests
pytest tests/backend/e2e/

# Cleanup
docker-compose -f docker-compose.test.yml down
```

## 🧪 Test Categories

### Unit Tests

Test individual components in isolation:

```python
# Example: Testing Aria agent service
def test_aria_content_generation():
    service = AriaContentService()
    result = service.generate_content("Test prompt")
    assert result is not None
    assert "content" in result
```

### Integration Tests

Test component interactions:

```python
# Example: Testing database integration
async def test_user_creation():
    user = await create_user("test@example.com")
    assert user.id is not None
    assert user.email == "test@example.com"
```

### End-to-End Tests

Test complete user workflows:

```python
# Example: Testing user registration flow
async def test_user_registration_flow():
    # Register user
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 201
    
    # Login user
    response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
```

### Performance Tests

Test system performance under load:

```python
# Example: Load testing API endpoints
def test_api_load():
    with locust.HttpUser() as user:
        user.get("/api/health")
        user.post("/api/agents/aria/chat", json={"message": "test"})
```

## 🔧 Test Configuration

### Pytest Configuration

```python
# conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///./test.db")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    engine.dispose()

@pytest.fixture
def client(test_db):
    """Create a test client."""
    from backend.main import app
    return TestClient(app)
```

### Jest Configuration

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testMatch: [
    '<rootDir>/tests/**/*.test.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

## 📊 Test Data Management

### Fixtures

```python
# fixtures/user_fixtures.py
import pytest
from backend.core.database.models import User

@pytest.fixture
def test_user():
    return User(
        email="test@example.com",
        username="testuser",
        full_name="Test User"
    )

@pytest.fixture
def test_users():
    return [
        User(email=f"user{i}@example.com", username=f"user{i}")
        for i in range(10)
    ]
```

### Factories

```python
# utils/factories.py
import factory
from backend.core.database.models import User, Task

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    full_name = factory.Faker("name")

class TaskFactory(factory.Factory):
    class Meta:
        model = Task
    
    title = factory.Faker("sentence")
    description = factory.Faker("text")
    user = factory.SubFactory(UserFactory)
```

## 🎯 Test Coverage

### Coverage Goals

- **Backend**: 90%+ code coverage
- **Frontend**: 85%+ code coverage
- **Critical Paths**: 100% coverage
- **API Endpoints**: 100% coverage

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=backend --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/backend/ --cov=backend
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Run tests
        run: cd frontend && npm test
```

## 🐛 Debugging Tests

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database is running
   docker-compose ps postgres
   
   # Test connection
   psql -h localhost -U agent47 -d agent47_db
   ```

2. **Test Data Cleanup**
   ```python
   # Use fixtures for proper cleanup
   @pytest.fixture(autouse=True)
   def cleanup_test_data():
       yield
       # Cleanup after each test
       cleanup_database()
   ```

3. **Async Test Issues**
   ```python
   # Use proper async test decorators
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

### Test Debugging

```bash
# Run tests with verbose output
pytest -v tests/backend/unit/

# Run specific test with debugging
pytest -s tests/backend/unit/test_specific.py::test_function

# Run tests with pdb debugging
pytest --pdb tests/backend/unit/
```

## 📈 Performance Testing

### Load Testing

```python
# tests/performance/load_test.py
import locust

class Agent47User(locust.HttpUser):
    def on_start(self):
        # Login user
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @locust.task(3)
    def chat_with_aria(self):
        self.client.post("/api/agents/aria/chat", json={
            "message": "Generate content about AI"
        })
    
    @locust.task(1)
    def get_dashboard(self):
        self.client.get("/api/dashboard/overview")
```

### Stress Testing

```bash
# Run stress tests
locust -f tests/performance/stress_test.py --host=http://localhost:8000
```

## 🔍 Test Monitoring

### Test Metrics

- **Test Execution Time**: Track test performance
- **Flaky Tests**: Identify unreliable tests
- **Coverage Trends**: Monitor coverage over time
- **Failure Rates**: Track test failure patterns

### Test Reports

- **HTML Reports**: Detailed test results
- **JUnit XML**: CI/CD integration
- **Coverage Reports**: Code coverage analysis
- **Performance Reports**: Load test results

## 📚 Best Practices

### Test Organization

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Single Responsibility**: One test per scenario
3. **Descriptive Names**: Clear test descriptions
4. **Independent Tests**: Tests should not depend on each other

### Test Data

1. **Use Fixtures**: Reusable test data
2. **Clean State**: Reset state between tests
3. **Realistic Data**: Use realistic test data
4. **Edge Cases**: Test boundary conditions

### Performance

1. **Fast Tests**: Keep unit tests fast
2. **Parallel Execution**: Run tests in parallel
3. **Selective Testing**: Run only relevant tests
4. **Mock External Services**: Avoid external dependencies

## 🤝 Contributing

1. Write tests for new features
2. Maintain test coverage
3. Follow testing best practices
4. Update test documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.