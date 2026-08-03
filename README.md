# Build Your PC — Backend (FastAPI)

Backend do BYP — Build Your PC. Autenticação JWT + catálogo de peças, em arquitetura em camadas (router → service → repository → model).

## Requisitos

- Python 3.12
- Docker (para o PostgreSQL)

## Setup

1. Copiar `.env.example` → `.env`.
2. Subir o banco: `docker compose up -d`.
3. Criar venv e instalar deps:
   `python -m venv .venv` + `pip install -r requirements.txt`.
4. Aplicar migrações: `alembic upgrade head`.
5. Popular catálogo: `python seed.py`.
6. Rodar: `uvicorn app.main:app --reload` — docs em `http://127.0.0.1:8000/docs`.

## Testes

Garantir `docker compose up -d` e rodar `pytest` (usa o banco `byp_test`).

## Endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login` (form: `username` aceita email ou usuário + `password`)
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/components?category=cpu`
- `GET /api/v1/components/{id}`
- `POST /api/v1/components` (admin)
- `PUT /api/v1/components/{id}` (admin)
- `DELETE /api/v1/components/{id}` (admin)

## Arquitetura

```
app/
├── core/        (config, database, security, exceptions)
├── models/      (SQLAlchemy)
├── schemas/     (Pydantic)
├── repositories/
├── services/
└── routers/
```

## Admin

Não há rota pública para criar admin. Para testes, crie o usuário e marque `is_admin=true`
direto no banco (ex.: `UPDATE users SET is_admin = true WHERE username = 'seu_usuario';`).
