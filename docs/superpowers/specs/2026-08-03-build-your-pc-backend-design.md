# Build Your PC — Backend (FastAPI) — Design/Especificação

Data: 2026-08-03
Status: aprovado para implementação

## Objetivo

Criar o backend do **BYP - Build Your PC**. Garante as telas já prototipadas no front
(Login/Cadastro) e expõe o catálogo de peças para a futura funcionalidade de montagem.
Este primeiro ciclo cobre **autenticação completa + catálogo de peças** (CRUD + seed).

Fora de escopo desta etapa: construtor de builds, verificação de compatibilidade e o
assistente BYP. Essas features entram em ciclos futuros reutilizando a infraestrutura aqui criada.

## Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (síncrono, ORM)
- Alembic (migrações)
- PostgreSQL via Docker Compose
- Pydantic v2 + pydantic-settings
- python-jose (JWT), passlib[bcrypt]
- pytest

## Arquitetura

Arquitetura em camadas: **router → service → repository → model/DB**.

- Rota nunca acessa o banco: delega ao service.
- Service orquestra regras de negócio e chama o repository.
- Repository encapsula query/DB de cada entidade.
- Schemas Pydantic são o "contrato" nas fronteiras; services e controllers expõem/consumos
  schemas, não models.
- Sessão de banco via `get_db` (Dependency Injection) fornecendo `Session`.

### Estrutura de pastas

```
back-byp/
├── app/
│   ├── __init__.py
│   ├── main.py                  # cria a app FastAPI, CORS, handlers de erro, routers
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings) + .env
│   │   ├── database.py          # engine, SessionLocal, get_db
│   │   ├── security.py          # hash de senha, JWT (access/refresh)
│   │   └── exceptions.py        # exceções de negócio + handlers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── component.py
│   │   └── refresh_token.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py              # UserCreate, UserRead, LoginRequest, TokenPair
│   │   └── component.py         # ComponentCreate, ComponentRead, ComponentUpdate
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── component_repository.py
│   │   └── refresh_token_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # registrar, autenticar, refresh, logout, token
│   │   └── component_service.py # CRUD + filtro
│   └── routers/
│       ├── __init__.py
│       ├── auth.py              # /api/v1/auth
│       └── components.py        # /api/v1/components
├── alembic/  (env.py + versions/)
├── alembic.ini
├── seed.py                      # popula catálogo de exemplo
├── docker-compose.yml           # PostgreSQL
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_components.py
├── .env.example
├── .env                        # local, não versionado
├── .gitignore
├── requirements.txt
└── README.md
```

### Dependências

`fastapi`, `uvicorn[standard]`, `sqlalchemy>=2.0`, `alembic`, `psycopg2-binary`,
`pydantic-settings`, `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`;
dev: `pytest`.

## Modelo de dados

### users

| campo | tipo | obs |
|---|---|---|
| id | Integer PK | |
| email | String(255) | unique, not null, index |
| username | String(50) | unique, not null |
| password_hash | String(255) | bcrypt |
| is_active | Boolean | default True (flag reservada; toda criação default ativo) |
| is_admin | Boolean | default False |
| created_at | DateTime | server_default now |

### components

| campo    | tipo               | obs |
|---|---|---|
| id       | Integer PK         | |
| name     | String(200)        | not null |
| category | String(30)         | enum: cpu, gpu, ram, storage, motherboard, psu, case, cooling; index |
| brand    | String(100)        | nullable |
| price    | Numeric(12,2)      | nullable |
| specs    | JSON               | specs livre (ex.: {"cores": 8, "socket": "AM5"}) |
| created_at | DateTime         | server_default now |

- `category` como string dá flexibilidade ao catálogo crescer sem migração.
- `specs` JSON evita dezenas de colunas por categoria.
- `components` será populado por `seed.py` (CPUs, GPUs, RAMs, armazenamentos de exemplo).

### refresh_tokens

| campo      | tipo           | obs |
|---|---|---|
| id         | Integer PK     | |
| user_id    | Integer FK     | ondelete CASCADE |
| token      | String(500)    | unique |
| expires_at | DateTime       | |
| created_at | DateTime       | server_default now |

## Endpoints

### Auth — `/api/v1/auth`

| método | rota | função | acesso |
|---|---|---|---|
| POST | /register | email + username + senha → cria usuário, retorna UserRead | público |
| POST | /login | credentials (OAuth2PasswordRequestForm) → TokenPair | público |
| POST | /refresh | refresh token → novo TokenPair | refresh válido |
| GET | /me | dados do usuário logado | autenticado |
| POST | /logout | revoga refresh token (apaga do banco) | autenticado |

### Catalog — `/api/v1/components`

| método | rota | função | acesso |
|---|---|---|---|
| GET | /components | lista (query `category`) | público |
| GET | /components/{id} | retorna um componente | público |
| POST | /components | cria | admin |
| PUT | /components/{id} | atualiza | admin |
| DELETE | /components/{id} | remove | admin |

## Autenticação

- Senhas com bcrypt (passlib).
- **access token** — JWT, exp 30min, claim `sub=user id`, `exp`, `type=access`.
- **refresh token** — JWT aleatório (token string) persistido em `refresh_tokens`, exp 7d,
  revogável no logout.
- `/login` aceita email OU username no campo `username` do form.
- `get_current_user` (dependency) decodifica access token e busca usuário; valida `is_active`.
- `get_current_admin` estende `get_current_user` exigindo `is_admin=True` (coluna booleana
  no User, default False).

## Erros e validação

- Exceções de negócio em `app/core/exceptions.py`:
  - `EmailAlreadyRegistered` → 409
  - `UsernameAlreadyRegistered` → 409
  - `InvalidCredentials` → 401
  - `TokenExpired` / `InvalidToken` → 401
  - `NotFound` → 404
- Resposta padronizada: `{"detail": "mensagem"}`.
- Handlers registrados em `app/main.py`.
- Pydantic v2: email válido, senha mínima 8, categoria enum, preço >= 0.
- Erros de validação Pydantic usam defaults do FastAPI (422).

## Testes

- `tests/conftest.py`: cria DB de teste PostgreSQL isolado, sessão, fixture `client`.
- `tests/test_auth.py`: registro (ok, email/username duplicado, senha curta), login (ok,
  inválido), refresh, logout, /me.
- `tests/test_components.py`: CRUD, filtro por categoria, e regras de admin (criar/editar/
  remover exige admin; lista e detalhe públicos).

## Configuração / infra

- `docker-compose.yml`: serviço `db` com imagem PostgreSQL 16, porta 5432, volume, envs.
- `.env.example` contém `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES=30`,
  `REFRESH_TOKEN_EXPIRE_DAYS=7`.
- Migrações via Alembic: `alembic init alembic` (gera `alembic.ini` + pasta `alembic/`),
  `alembic revision --autogenerate` e `alembic upgrade head` após definir os models.

## Runbook inicial

1. Copiar `.env.example` → `.env`.
2. `docker compose up -d` (sobe PostgreSQL).
3. Criar virtualenv e `pip install -r requirements.txt`.
4. `alembic upgrade head` (cria tabelas).
5. `python seed.py` (popula catálogo).
6. `uvicorn app.main:app --reload` (aplicação em http://localhost:8000, docs em /docs).
7. `pytest` para os testes.

## Notas finais

- Adicionar coluna `is_admin` (Boolean, default False) ao User, em vez de um enum `role`,
  para simplificar `get_current_admin`.
- Manter CORS configurado (origem do front local) no `main.py`.