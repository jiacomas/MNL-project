# Testing Structure

This directory contains the integration and E2E tests of the project.

## Test structure

```
MNL-project/
├── backend/tests/          # Backend unit tests (pytest)
├── frontend/tests/         # Frontend unit tests (jest)
└── tests/                  # Integration tests (this directory)
    ├── integration/        # Integration tests between services
    ├── e2e/                # Full end-to-end tests
    └── docker-compose.test.yml
```

## How to run the tests

### Backend unit tests

```bash
cd backend
pytest tests/ -v
```

### Frontend unit tests

```bash
cd frontend
npm test
```

### Integration tests

```bash
# Start the services
docker compose up -d

# Run integration tests
cd tests
pytest integration/ -v

# Or use the test docker-compose
docker compose -f docker-compose.test.yml up --build
```

## Types of Tests

- **Unit**: Test individual functions/components
- **Integration**: Test communication between services
- **E2E**: Test full user workflows
