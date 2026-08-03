# Build Your PC â€” Backend (FastAPI) â€” Design/EspecificaÃ§Ã£o

Data: 2026-08-03
Status: aprovado para implementaÃ§Ã£o

## Objetivo

Criar o backend do **BYP - Build Your PC**. Garante as telas jÃ¡ prototipadas no front
(Login/Cadastro) e expÃµe o catÃ¡logo de peÃ§as para a futura funcionalidade de montagem.
Este primeiro ciclo cobre **autenticaÃ§Ã£o completa + catÃ¡logo de peÃ§as** (CRUD + seed).

Fora de escopo desta etapa: construtor de builds, verificaÃ§Ã£o de compatibilidade e o
assistente BYP. Essas features entram em ciclos futuros reutilizando a infraestrutura aqui criada.

## Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (sÃ­ncrono, ORM)
- Alembic (migraÃ§Ãµes)
- PostgreSQL via Docker Compose
- Pydantic v2 + pydantic-settings
- python-jose (JWT), passlib[bcrypt]
- pytest

## Arquitetura

Arquitetura em camadas: **router â†’ service â†’ repository â†’ model/DB**.

- Rota nunca acessa o banco: delega ao service.
- Service orquestra regras de negÃ³cio e chama o repository.
- Repository encapsula query/DB de cada entidade.
- Schemas Pydantic sÃ£o o "contrato" nas fronteiras; services e controllers expÃµem/consumos
  schemas, nÃ£o models.
- SessÃ£o de banco via `get_db` (Dependency Injection) fornecendo `Session`.

### Estrutura de pastas

```
back-byp/
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ main.py                  # cria a app FastAPI, CORS, handlers de erro, routers
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ config.py            # Settings (pydantic-settings) + .env
â”‚   â”‚   â”œâ”€â”€ database.py          # engine, SessionLocal, get_db
â”‚   â”‚   â”œâ”€â”€ security.py          # hash de senha, JWT (access/refresh)
â”‚   â”‚   â””â”€â”€ exceptions.py        # exceÃ§Ãµes de negÃ³cio + handlers
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ user.py
â”‚   â”‚   â”œâ”€â”€ component.py
â”‚   â”‚   â””â”€â”€ refresh_token.py
â”‚   â”œâ”€â”€ schemas/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ user.py              # UserCreate, UserRead, LoginRequest, TokenPair
â”‚   â”‚   â””â”€â”€ component.py         # ComponentCreate, ComponentRead, ComponentUpdate
â”‚   â”œâ”€â”€ repositories/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ user_repository.py
â”‚   â”‚   â”œâ”€â”€ component_repository.py
â”‚   â”‚   â””â”€â”€ refresh_token_repository.py
â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ auth_service.py      # registrar, autenticar, refresh, logout, token
â”‚   â”‚   â””â”€â”€ component_service.py # CRUD + filtro
â”‚   â””â”€â”€ routers/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ auth.py              # /api/v1/auth
â”‚       â””â”€â”€ components.py        # /api/v1/components
â”œâ”€â”€ alembic/  (env.py + versions/)
â”œâ”€â”€ alembic.ini
â”œâ”€â”€ seed.py                      # popula catÃ¡logo de exemplo
â”œâ”€â”€ docker-compose.yml           # PostgreSQL
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ conftest.py
â”‚   â”œâ”€â”€ test_auth.py
â”‚   â””â”€â”€ test_components.py
â”œâ”€â”€ .env.example
â”œâ”€â”€ .env                        # local, nÃ£o versionado
â”œâ”€â”€ .gitignore
â”œâ”€â”€ requirements.txt
â””â”€â”€ README.md
```

### DependÃªncias

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
| is_active | Boolean | default True (flag reservada; toda criaÃ§Ã£o default ativo) |
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

- `category` como string dÃ¡ flexibilidade ao catÃ¡logo crescer sem migraÃ§Ã£o.
- `specs` JSON evita dezenas de colunas por categoria.
- `components` serÃ¡ populado por `seed.py` (CPUs, GPUs, RAMs, armazenamentos de exemplo).

### refresh_tokens

| campo      | tipo           | obs |
|---|---|---|
| id         | Integer PK     | |
| user_id    | Integer FK     | ondelete CASCADE |
| token      | String(500)    | unique |
| expires_at | DateTime       | |
| created_at | DateTime       | server_default now |

## Endpoints

### Auth â€” `/api/v1/auth`

| mÃ©todo | rota | funÃ§Ã£o | acesso |
|---|---|---|---|
| POST | /register | email + username + senha â†’ cria usuÃ¡rio, retorna UserRead | pÃºblico |
| POST | /login | credentials (OAuth2PasswordRequestForm) â†’ TokenPair | pÃºblico |
| POST | /refresh | refresh token â†’ novo TokenPair | refresh vÃ¡lido |
| GET | /me | dados do usuÃ¡rio logado | autenticado |
| POST | /logout | revoga refresh token (apaga do banco) | autenticado |

### Catalog â€” `/api/v1/components`

| mÃ©todo | rota | funÃ§Ã£o | acesso |
|---|---|---|---|
| GET | /components | lista (query `category`) | pÃºblico |
| GET | /components/{id} | retorna um componente | pÃºblico |
| POST | /components | cria | admin |
| PUT | /components/{id} | atualiza | admin |
| DELETE | /components/{id} | remove | admin |

## AutenticaÃ§Ã£o

- Senhas com bcrypt (passlib).
- **access token** â€” JWT, exp 30min, claim `sub=user id`, `exp`, `type=access`.
- **refresh token** â€” JWT aleatÃ³rio (token string) persistido em `refresh_tokens`, exp 7d,
  revogÃ¡vel no logout.
- `/login` aceita email OU username no campo `username` do form.
- `get_current_user` (dependency) decodifica access token e busca usuÃ¡rio; valida `is_active`.
- `get_current_admin` estende `get_current_user` exigindo `is_admin=True` (coluna booleana
  no User, default False).

## Erros e validaÃ§Ã£o

- ExceÃ§Ãµes de negÃ³cio em `app/core/exceptions.py`:
  - `EmailAlreadyRegistered` â†’ 409
  - `UsernameAlreadyRegistered` â†’ 409
  - `InvalidCredentials` â†’ 401
  - `TokenExpired` / `InvalidToken` â†’ 401
  - `NotFound` â†’ 404
- Resposta padronizada: `{"detail": "mensagem"}`.
- Handlers registrados em `app/main.py`.
- Pydantic v2: email vÃ¡lido, senha mÃ­nima 8, categoria enum, preÃ§o >= 0.
- Erros de validaÃ§Ã£o Pydantic usam defaults do FastAPI (422).

## Testes

- `tests/conftest.py`: cria DB de teste PostgreSQL isolado, sessÃ£o, fixture `client`.
- `tests/test_auth.py`: registro (ok, email/username duplicado, senha curta), login (ok,
  invÃ¡lido), refresh, logout, /me.
- `tests/test_components.py`: CRUD, filtro por categoria, e regras de admin (criar/editar/
  remover exige admin; lista e detalhe pÃºblicos).

## ConfiguraÃ§Ã£o / infra

- `docker-compose.yml`: serviÃ§o `db` com imagem PostgreSQL 16, porta 5433, volume, envs.
- `.env.example` contÃ©m `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES=30`,
  `REFRESH_TOKEN_EXPIRE_DAYS=7`.
- MigraÃ§Ãµes via Alembic: `alembic init alembic` (gera `alembic.ini` + pasta `alembic/`),
  `alembic revision --autogenerate` e `alembic upgrade head` apÃ³s definir os models.

## Runbook inicial

1. Copiar `.env.example` â†’ `.env`.
2. `docker compose up -d` (sobe PostgreSQL).
3. Criar virtualenv e `pip install -r requirements.txt`.
4. `alembic upgrade head` (cria tabelas).
5. `python seed.py` (popula catÃ¡logo).
6. `uvicorn app.main:app --reload` (aplicaÃ§Ã£o em http://localhost:8000, docs em /docs).
7. `pytest` para os testes.

## Notas finais

- Adicionar coluna `is_admin` (Boolean, default False) ao User, em vez de um enum `role`,
  para simplificar `get_current_admin`.
- Manter CORS configurado (origem do front local) no `main.py`.
