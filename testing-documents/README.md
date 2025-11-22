# Testing Documents

This folder contains test evidence for the backend system of the MNL Project. It demonstrates unit testing, integration testing, external API mocking, CI execution, and coverage reports.

## Test Categories

### 1. Unit Tests

Covers isolated business logic and file persistence rules, using mock-based isolation when appropriate.
Tested modules include:

- repositories (movies, reviews, bookmarks, penalties, users, reset tokens, sessions)
- services (auth, reviews, bookmarks, recommendations, external sync, password reset)
  Mock isolation implemented using:

```
mocker.patch(...)
```

### 2. Integration Tests

Covers API routers with dependency injection and persistent JSON/CSV file usage.
Features validated:

- Role-based access enforcement
- Schema validation
- JSON persistence
- Authentication check through test headers

### 3. Mock-Based External API Tests

Uses `mocker` and `pytest-mock` to replace external HTTP calls:

```
mocker.patch("backend.services.external_sync_service._fetch_external_metadata", return_value=...)
```

Verifies:

- Metadata sync into JSON files
- Audit log updates
- Update counts and timestamps

### 4. Fault Injection and Error Handling Tests

Deliberately triggers edge cases such as:

- Duplicate review prevention
- Unauthorized updates/deletes
- Admin-only restrictions
- Password reset token errors
- Penalty enforcement behavior

## Continuous Integration Evidence

Tests run automatically in GitHub Actions:

- Executes full Pytest suite
- Enforces pre-commit hooks
- Runs tests on pull request creation and on branch pushes

CI workflow:

```
.github/workflows/ci-all.yml
```

## Coverage Evidence

Terminal coverage summary:

```
pytest --cov=backend --cov-report=term-missing
```

HTML coverage export:

```
pytest --cov=backend --cov-report=html
```

Coverage reports are captured via screenshots rather than committing build artifacts.

## Folder Structure

```
testing-documents/
  screenshots/
      ci-pipeline.png
      pytest-summary.png
      coverage-overview.png
```

## Notes

- `htmlcov/` and `.coverage` remain ignored in version control.
