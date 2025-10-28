# Testing Structure

Aquest directori conté els **tests d'integració i E2E** del projecte.

## Estructura de Tests

```
MNL-project/
├── backend/tests/          # Tests unitaris del backend (pytest)
├── frontend/tests/         # Tests unitaris del frontend (jest)
└── tests/                  # Tests d'integració (aquest directori)
    ├── integration/        # Tests d'integració entre serveis
    ├── e2e/               # Tests end-to-end complets
    └── docker-compose.test.yml
```

## Com executar els tests

### Tests Unitaris Backend

```bash
cd backend
pytest tests/ -v
```

### Tests Unitaris Frontend

```bash
cd frontend
npm test
```

### Tests d'Integració

```bash
# Iniciar els serveis
docker compose up -d

# Executar tests d'integració
cd tests
pytest integration/ -v

# O usar el docker-compose de test
docker compose -f docker-compose.test.yml up --build
```

## Tipus de Tests

- **Unitaris**: Testegen funcions/components individuals
- **Integració**: Testegen comunicació entre serveis
- **E2E**: Testegen workflows complets d'usuari
