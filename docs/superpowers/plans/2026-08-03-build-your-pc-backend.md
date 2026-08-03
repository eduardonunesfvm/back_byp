# Build Your PC Backend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o backend FastAPI do BYP — Build Your PC com autenticação JWT (register/login/refresh/logout/me) e catálogo de peças (CRUD + seed), em arquitetura em camadas.

**Architecture:** Camadas `router → service → repository → model/DB`. Schemas Pydantic cruzam as fronteiras; models nunca. Sessão via `get_db` (Dependency Injection). PostgreSQL via Docker Compose, migrações com Alembic.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0 (sync), Alembic, psycopg2-binary, Pydantic v2 + pydantic-settings, python-jose (JWT), passlib[bcrypt], pytest, PostgreSQL 16.

## Global Constraints

- Python 3.12.10 (verificar com `python --version`).
- Camadas rígidas: router → service → repository → model. Rota não acessa banco diretamente.
- Schemas Pydantic são o contrato nas fronteiras; nunca expor models em rotas/services.
- Resposta de erro padronizada: `{"detail": "mensagem"}`.
- Categoria do componente: apenas `cpu`, `gpu`, `ram`, `storage`, `motherboard`, `psu`, `case`, `cooling`.
- Senha mínima 8 caracteres; `email` válido; `price >= 0`.
- Access token: JWT, exp 30min, claims `sub` (user id), `type=access`. Refresh token: string aleatória persistida em `refresh_tokens`, exp 7d, revogável.
- Login aceita email OU username no campo `username` do OAuth2PasswordRequestForm.
- Admin: coluna `is_admin` (bool, default False); dependency `get_current_admin` exige `is_admin=True` senão 403.
- Versões pinadas em `requirements.txt` (ver Task 1). `passlib==1.7.4` + `bcrypt==4.0.1` (evita warning do passlib com bcrypt>=4.1).
- Rodar testes com PostgreSQL no ar (`docker compose up -d`), banco de teste `byp_test`.
- Não commitar `.env`, `.venv/`, `__pycache__/`.

---

### Task 1: Infraestrutura base (requirements, env, docker, gitignore)

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `.env`
- Create: `docker-compose.yml`
- Create: `db/init.sql`
- Create: `app/__init__.py`
- Create: `app/core/__init__.py`

**Interfaces:**
- Consumes: nada.
- Produces: comando `docker compose up -d` sobe PostgreSQL na porta 5432; `pip install -r requirements.txt` instala as deps; `.env` fornece `DATABASE_URL`, `SECRET_KEY`, etc. para `app/core/config.py` (Task 2).

- [ ] **Step 1: Criar `requirements.txt`**

```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
pydantic==2.10.4
pydantic-settings==2.7.0
email-validator==2.2.0
python-jose[cryptography]==3.3.0
passlib==1.7.4
bcrypt==4.0.1
python-multipart==0.0.20
pytest==8.3.4
```

- [ ] **Step 2: Criar `.gitignore`**

```gitignore
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
.DS_Store
```

- [ ] **Step 3: Criar `.env.example`**

```env
DATABASE_URL=postgresql+psycopg2://byp:byp_dev_password@localhost:5432/byp
TEST_DATABASE_URL=postgresql+psycopg2://byp:byp_dev_password@localhost:5432/byp_test
SECRET_KEY=change-me-para-um-valor-aleatorio-longo
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

- [ ] **Step 4: Copiar para `.env`**

Copie o conteúdo do `.env.example` para `.env` (mesmos valores de exemplo; o `SECRET_KEY` pode ficar de exemplo nesta fase).

- [ ] **Step 5: Criar `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16
    container_name: byp_db
    environment:
      POSTGRES_USER: byp
      POSTGRES_PASSWORD: byp_dev_password
      POSTGRES_DB: byp
    ports:
      - "5432:5432"
    volumes:
      - byp_pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  byp_pgdata:
```

- [ ] **Step 6: Criar `db/init.sql`** (cria o banco de teste na inicialização)

```sql
CREATE DATABASE byp_test;
```

- [ ] **Step 7: Criar `app/__init__.py` e `app/core/__init__.py`** (arquivos vazios)

- [ ] **Step 8: Subir o banco e instalar dependências**

Run: `docker compose up -d`
Expected: container `byp_db` criado. `docker ps` mostra postgres na porta 5432.

Run: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
Expected: instalação concluída sem erro.

- [ ] **Step 9: Verificar versão do SQLAlchemy**

Run: `.\.venv\Scripts\python.exe -c "import sqlalchemy; print(sqlalchemy.__version__)"`
Expected: `2.0.36`

- [ ] **Step 10: Commit**

```bash
git add requirements.txt .gitignore .env.example docker-compose.yml db/init.sql app/__init__.py app/core/__init__.py
git commit -m "chore: infraestrutura base do backend (env, docker, deps)"
```

---

### Task 2: Configuração e banco (config.py, database.py)

**Files:**
- Create: `app/core/config.py`
- Create: `app/core/database.py`

**Interfaces:**
- Consumes: `.env` (Task 1).
- Produces: `settings` (objeto `Settings`), `engine`, `SessionLocal`, `Base`, `get_db()`. Usados por models (Task 3), deps (Task 7) e routers (Tasks 8-9).

- [ ] **Step 1: Escrever `app/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: list[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
```

- [ ] **Step 2: Escrever `app/core/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "from app.core.database import engine, SessionLocal, Base, get_db; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add app/core/config.py app/core/database.py
git commit -m "feat: configuração (pydantic-settings) e engine/sessão SQLAlchemy"
```

---

### Task 3: Models SQLAlchemy + migração inicial Alembic

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/user.py`
- Create: `app/models/component.py`
- Create: `app/models/refresh_token.py`
- Create: `alembic.ini` (via `alembic init alembic`)
- Create: `alembic/env.py` (editado)
- Create: `alembic/versions/*.py` (migração autogerada)

**Interfaces:**
- Consumes: `Base`, `engine`, `settings` (Task 2).
- Produces: tabelas `users`, `components`, `refresh_tokens` criadas no Postgres; models `User`, `Component`, `RefreshToken` usados pelos repositories (Tasks 6-7). Colunas obrigatórias: `User.id/email/username/password_hash/is_active/is_admin/created_at`; `Component.id/name/category/brand/price/specs/created_at`; `RefreshToken.id/user_id/token/expires_at/created_at`.

- [ ] **Step 1: Escrever `app/models/user.py`**

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 2: Escrever `app/models/component.py`**

```python
import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ComponentCategory(str, enum.Enum):
    cpu = "cpu"
    gpu = "gpu"
    ram = "ram"
    storage = "storage"
    motherboard = "motherboard"
    psu = "psu"
    case = "case"
    cooling = "cooling"


class Component(Base):
    __tablename__ = "components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 3: Escrever `app/models/refresh_token.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()
```

- [ ] **Step 4: Escrever `app/models/__init__.py`** (registra os models no metadata)

```python
from app.models.component import Component
from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = ["Component", "RefreshToken", "User"]
```

- [ ] **Step 5: Iniciar Alembic**

Run: `.\.venv\Scripts\python.exe -m alembic init alembic`
Expected: cria `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/`.

- [ ] **Step 6: Editar `alembic/env.py`**

No topo, após os imports existentes, adicione:

```python
from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401
```

No início de `run_migrations_offline` e de `run_migrations_online`, adicione (logo após a definição de `config` no escopo da função; no arquivo gerado é mais simples adicionar uma linha no topo da função ou antes do `engine_from_config`):

```python
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

E substitua:

```python
target_metadata = None
```

por:

```python
target_metadata = Base.metadata
```

- [ ] **Step 7: Gerar a migração inicial**

Run: `.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "initial tables"`
Expected: cria um arquivo em `alembic/versions/` com `create_table` para `users`, `components` e `refresh_tokens`. Revise o arquivo gerado para confirmar as 3 tabelas e as constraints (unique de email/username/token, FK de refresh_tokens.user_id com ondelete CASCADE).

- [ ] **Step 8: Aplicar a migração**

Run: `.\.venv\Scripts\python.exe -m alembic upgrade head`
Expected: `Running upgrade ... -> ..., initial tables`.

- [ ] **Step 9: Verificar tabelas no banco**

Run: `docker exec byp_db psql -U byp -d byp -c "\dt"`
Expected: lista `alembic_version`, `components`, `refresh_tokens`, `users`.

- [ ] **Step 10: Commit**

```bash
git add app/models alembic alembic.ini
git commit -m "feat: models User/Component/RefreshToken e migração inicial"
```

---

### Task 4: Exceções de negócio + security (JWT/bcrypt)

**Files:**
- Create: `app/core/exceptions.py`
- Create: `app/core/security.py`

**Interfaces:**
- Consumes: `settings` (Task 2).
- Produces: exceções `AppError`, `EmailAlreadyRegistered`, `UsernameAlreadyRegistered`, `InvalidCredentials`, `InvalidToken`, `TokenExpired`, `NotFound`, `PermissionDenied`; funções `hash_password`, `verify_password`, `create_access_token(user_id: int) -> str`, `generate_refresh_token() -> str`, `decode_access_token(token: str) -> int`. Usadas por services (Task 7), deps (Task 8) e main (Task 9).

- [ ] **Step 1: Escrever `app/core/exceptions.py`**

```python
class AppError(Exception):
    status_code = 500
    detail = "Erro interno"

    def __init__(self, detail: str | None = None, status_code: int | None = None):
        self.detail = detail or self.detail
        self.status_code = status_code or self.status_code
        super().__init__(self.detail)


class EmailAlreadyRegistered(AppError):
    status_code = 409
    detail = "E-mail já cadastrado"


class UsernameAlreadyRegistered(AppError):
    status_code = 409
    detail = "Usuário já cadastrado"


class InvalidCredentials(AppError):
    status_code = 401
    detail = "Credenciais inválidas"


class InvalidToken(AppError):
    status_code = 401
    detail = "Token inválido"


class TokenExpired(AppError):
    status_code = 401
    detail = "Token expirado"


class NotFound(AppError):
    status_code = 404
    detail = "Recurso não encontrado"


class PermissionDenied(AppError):
    status_code = 403
    detail = "Permissão negada"
```

- [ ] **Step 2: Escrever `app/core/security.py`**

```python
import secrets
from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidToken, TokenExpired

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except JWTError as exc:
        raise InvalidToken() from exc
    if payload.get("type") != "access" or payload.get("sub") is None:
        raise InvalidToken()
    return int(payload["sub"])
```

- [ ] **Step 3: Teste manual de hash/verify**

Run: `.\.venv\Scripts\python.exe -c "from app.core.security import hash_password, verify_password; h=hash_password('segredo123'); print(verify_password('segredo123', h)); print(verify_password('errada', h))"`
Expected: `True` e `False`.

- [ ] **Step 4: Commit**

```bash
git add app/core/exceptions.py app/core/security.py
git commit -m "feat: exceções de negócio e security (bcrypt + JWT)"
```

---

### Task 5: Schemas Pydantic

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/user.py`
- Create: `app/schemas/component.py`

**Interfaces:**
- Consumes: nada além do Pydantic.
- Produces: `UserCreate`, `UserRead`, `TokenPair`, `RefreshRequest`, `ComponentCreate`, `ComponentUpdate`, `ComponentRead`, e a categoria literal `ComponentCategoryLiteral`. Usados por routers/services (Tasks 7-9).

- [ ] **Step 1: Escrever `app/schemas/user.py`**

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
```

- [ ] **Step 2: Escrever `app/schemas/component.py`**

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ComponentCategoryLiteral = Literal[
    "cpu", "gpu", "ram", "storage", "motherboard", "psu", "case", "cooling"
]


class ComponentBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: ComponentCategoryLiteral
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    specs: dict | None = None


class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: ComponentCategoryLiteral | None = None
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    specs: dict | None = None


class ComponentRead(ComponentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
```

- [ ] **Step 3: Criar `app/schemas/__init__.py`** (vazio)

- [ ] **Step 4: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "from app.schemas.user import UserCreate, TokenPair; from app.schemas.component import ComponentCreate; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add app/schemas
git commit -m "feat: schemas Pydantic (user, component)"
```

---

### Task 6: Repositories

**Files:**
- Create: `app/repositories/__init__.py`
- Create: `app/repositories/user_repository.py`
- Create: `app/repositories/refresh_token_repository.py`
- Create: `app/repositories/component_repository.py`

**Interfaces:**
- Consumes: models (Task 3), schemas (Task 5).
- Produces:
  - `UserRepository(db)` — `get_by_id(user_id: int) -> User | None`, `get_by_username_or_email(login: str) -> User | None`, `email_exists(email: str) -> bool`, `username_exists(username: str) -> bool`, `create(email, username, password_hash) -> User`.
  - `RefreshTokenRepository(db)` — `get_by_token(token) -> RefreshToken | None`, `create(user_id, token, expires_at) -> RefreshToken`, `delete(rt) -> None`, `delete_all_for_user(user_id) -> None`.
  - `ComponentRepository(db)` — `list(category: str | None) -> list[Component]`, `get_by_id(component_id) -> Component | None`, `create(data: ComponentCreate) -> Component`, `update(comp, data: ComponentUpdate) -> Component`, `delete(comp) -> None`.

- [ ] **Step 1: Escrever `app/repositories/user_repository.py`**

```python
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username_or_email(self, login: str) -> User | None:
        stmt = select(User).where(
            or_(User.username == login, User.email == login)
        )
        return self.db.scalars(stmt).first()

    def email_exists(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email).limit(1)
        return self.db.scalars(stmt).first() is not None

    def username_exists(self, username: str) -> bool:
        stmt = select(User.id).where(User.username == username).limit(1)
        return self.db.scalars(stmt).first() is not None

    def create(self, email: str, username: str, password_hash: str) -> User:
        user = User(email=email, username=username, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
```

- [ ] **Step 2: Escrever `app/repositories/refresh_token_repository.py`**

```python
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        return self.db.scalars(stmt).first()

    def create(self, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
        self.db.add(rt)
        self.db.commit()
        return rt

    def delete(self, rt: RefreshToken) -> None:
        self.db.delete(rt)
        self.db.commit()

    def delete_all_for_user(self, user_id: int) -> None:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        for rt in self.db.scalars(stmt):
            self.db.delete(rt)
        self.db.commit()
```

- [ ] **Step 3: Escrever `app/repositories/component_repository.py`**

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.component import Component
from app.schemas.component import ComponentCreate, ComponentUpdate


class ComponentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, category: str | None = None) -> list[Component]:
        stmt = select(Component)
        if category:
            stmt = stmt.where(Component.category == category)
        return list(self.db.scalars(stmt))

    def get_by_id(self, component_id: int) -> Component | None:
        return self.db.get(Component, component_id)

    def create(self, data: ComponentCreate) -> Component:
        comp = Component(**data.model_dump())
        self.db.add(comp)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def update(self, comp: Component, data: ComponentUpdate) -> Component:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(comp, field, value)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def delete(self, comp: Component) -> None:
        self.db.delete(comp)
        self.db.commit()
```

- [ ] **Step 4: Criar `app/repositories/__init__.py`** (vazio)

- [ ] **Step 5: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "from app.repositories.user_repository import UserRepository; from app.repositories.component_repository import ComponentRepository; from app.repositories.refresh_token_repository import RefreshTokenRepository; print('ok')"`
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add app/repositories
git commit -m "feat: repositories de user, refresh token e componente"
```

---

### Task 7: Services (auth + component)

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/auth_service.py`
- Create: `app/services/component_service.py`

**Interfaces:**
- Consumes: repositories (Task 6), schemas (Task 5), security/exceptions (Task 4), `settings` (Task 2).
- Produces:
  - `AuthService(db, user_repo=None, refresh_token_repo=None)` — `register(data: UserCreate) -> User`, `login(login: str, password: str) -> TokenPair`, `refresh(refresh_token: str) -> TokenPair`, `logout(user_id: int) -> None`.
  - `ComponentService(db, repo=None)` — `list(category: str | None) -> list[Component]`, `get(component_id: int) -> Component`, `create(data: ComponentCreate) -> Component`, `update(component_id: int, data: ComponentUpdate) -> Component`, `delete(component_id: int) -> None`.

- [ ] **Step 1: Escrever `app/services/auth_service.py`**

```python
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidToken,
    NotFound,
    TokenExpired,
    UsernameAlreadyRegistered,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenPair, UserCreate


class AuthService:
    def __init__(
        self,
        db: Session,
        user_repo: UserRepository | None = None,
        refresh_token_repo: RefreshTokenRepository | None = None,
    ):
        self.db = db
        self.user_repo = user_repo or UserRepository(db)
        self.refresh_token_repo = refresh_token_repo or RefreshTokenRepository(db)

    def register(self, data: UserCreate) -> User:
        if self.user_repo.email_exists(str(data.email)):
            raise EmailAlreadyRegistered()
        if self.user_repo.username_exists(data.username):
            raise UsernameAlreadyRegistered()
        password_hash = security.hash_password(data.password)
        return self.user_repo.create(str(data.email), data.username, password_hash)

    def login(self, login: str, password: str) -> TokenPair:
        user = self.user_repo.get_by_username_or_email(login)
        if not user or not security.verify_password(password, user.password_hash):
            raise InvalidCredentials()
        return self._create_token_pair(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        stored = self.refresh_token_repo.get_by_token(refresh_token)
        if stored is None:
            raise InvalidToken()
        if stored.expires_at < datetime.now(timezone.utc):
            self.refresh_token_repo.delete(stored)
            raise TokenExpired()
        user = self.user_repo.get_by_id(stored.user_id)
        if user is None:
            raise NotFound()
        self.refresh_token_repo.delete(stored)
        return self._create_token_pair(user)

    def logout(self, user_id: int) -> None:
        self.refresh_token_repo.delete_all_for_user(user_id)

    def _create_token_pair(self, user: User) -> TokenPair:
        access_token = security.create_access_token(user.id)
        refresh_token = security.generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        self.refresh_token_repo.create(user.id, refresh_token, expires_at)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
```

- [ ] **Step 2: Escrever `app/services/component_service.py`**

```python
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound
from app.models.component import Component
from app.repositories.component_repository import ComponentRepository
from app.schemas.component import ComponentCreate, ComponentUpdate


class ComponentService:
    def __init__(self, db: Session, repo: ComponentRepository | None = None):
        self.db = db
        self.repo = repo or ComponentRepository(db)

    def list(self, category: str | None = None) -> list[Component]:
        return self.repo.list(category)

    def get(self, component_id: int) -> Component:
        comp = self.repo.get_by_id(component_id)
        if comp is None:
            raise NotFound()
        return comp

    def create(self, data: ComponentCreate) -> Component:
        return self.repo.create(data)

    def update(self, component_id: int, data: ComponentUpdate) -> Component:
        comp = self.get(component_id)
        return self.repo.update(comp, data)

    def delete(self, component_id: int) -> None:
        comp = self.get(component_id)
        self.repo.delete(comp)
```

- [ ] **Step 3: Criar `app/services/__init__.py`** (vazio)

- [ ] **Step 4: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "from app.services.auth_service import AuthService; from app.services.component_service import ComponentService; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add app/services
git commit -m "feat: services de auth e componente"
```

---

### Task 8: Dependencies de autenticação + router de auth + app main (esqueleto)

**Files:**
- Create: `app/routers/__init__.py`
- Create: `app/routers/deps.py`
- Create: `app/routers/auth.py`
- Create: `app/routers/components.py` (APIRouter vazio, preenchido na Task 9)
- Create: `app/main.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: services (Task 7), schemas (Task 5), security/exceptions (Task 4), `get_db` (Task 2).
- Produces: `get_current_user`, `get_current_admin` (deps); router `auth` com `/register`, `/login`, `/refresh`, `/me`, `/logout`; `app` FastAPI com CORS e handler de `AppError`; fixture `client` e `db_session` para testes.

- [ ] **Step 1: Escrever `app/routers/deps.py`**

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.core.exceptions import InvalidCredentials, InvalidToken, PermissionDenied
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = security.decode_access_token(token)
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise InvalidToken()
    if not user.is_active:
        raise InvalidCredentials()
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise PermissionDenied()
    return user
```

- [ ] **Step 2: Escrever `app/routers/auth.py`**

```python
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter()


def _service(db: Session) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return _service(db).register(data)


@router.post("/login", response_model=TokenPair)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return _service(db).login(form.username, form.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return _service(db).refresh(payload.refresh_token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", status_code=204)
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _service(db).logout(current_user.id)
    return None
```

- [ ] **Step 3: Criar `app/routers/components.py`** (esqueleto vazio desta Task; preenchido na Task 9)

```python
from fastapi import APIRouter

router = APIRouter()
```

- [ ] **Step 4: Criar `app/routers/__init__.py`** (vazio)

- [ ] **Step 5: Escrever `app/main.py`**

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppError
from app.routers import auth, components

app = FastAPI(title="Build Your PC API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/")
async def root():
    return {"message": "Build Your PC API"}


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(components.router, prefix="/api/v1", tags=["components"])
```

- [ ] **Step 6: Escrever `tests/conftest.py`**

```python
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://byp:byp_dev_password@localhost:5432/byp_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_tables(db_session):
    yield
    db_session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
    db_session.commit()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 7: Escrever `tests/test_app.py`**

```python
def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Build Your PC API"}


def test_docs(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
```

- [ ] **Step 8: Rodar os testes de smoke**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_app.py -v`
Expected: 2 PASS (requer `docker compose up -d` com banco `byp_test` criado pelo init.sql).

- [ ] **Step 9: Commit**

```bash
git add app/routers app/main.py tests/__init__.py tests/conftest.py tests/test_app.py
git commit -m "feat: deps de auth, router auth e esqueleto do main + infra de testes"
```

---

### Task 9: Router de componentes (CRUD + regras de admin) + testes de auth e componentes

**Files:**
- Modify: `app/routers/components.py`
- Create: `tests/test_auth.py`
- Create: `tests/test_components.py`

**Interfaces:**
- Consumes: deps `get_current_admin` (Task 8), `ComponentService` (Task 7), schemas (Task 5).
- Produces: endpoints `GET /api/v1/components`, `GET /api/v1/components/{id}`, `POST /api/v1/components`, `PUT /api/v1/components/{id}`, `DELETE /api/v1/components/{id}`; cobertura de testes de auth e catálogo.

- [ ] **Step 1: Substituir `app/routers/components.py`**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.deps import get_current_admin
from app.schemas.component import ComponentCreate, ComponentRead, ComponentUpdate
from app.services.component_service import ComponentService

router = APIRouter()


def _service(db: Session) -> ComponentService:
    return ComponentService(db)


@router.get("/components", response_model=list[ComponentRead])
def list_components(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return _service(db).list(category)


@router.get("/components/{component_id}", response_model=ComponentRead)
def get_component(component_id: int, db: Session = Depends(get_db)):
    return _service(db).get(component_id)


@router.post("/components", response_model=ComponentRead, status_code=201)
def create_component(
    data: ComponentCreate,
    db: Session = Depends(get_db),
    _admin: object = Depends(get_current_admin),
):
    return _service(db).create(data)


@router.put("/components/{component_id}", response_model=ComponentRead)
def update_component(
    component_id: int,
    data: ComponentUpdate,
    db: Session = Depends(get_db),
    _admin: object = Depends(get_current_admin),
):
    return _service(db).update(component_id, data)


@router.delete("/components/{component_id}", status_code=204)
def delete_component(
    component_id: int,
    db: Session = Depends(get_db),
    _admin: object = Depends(get_current_admin),
):
    _service(db).delete(component_id)
    return None
```

- [ ] **Step 2: Escrever `tests/test_auth.py`**

```python
from app.core import security
from app.models.user import User

VALID_USER = {
    "email": "user@test.com",
    "username": "user1",
    "password": "senha12345",
}


def _register(client, payload=None):
    return client.post("/api/v1/auth/register", json=payload or VALID_USER)


def _login(client, username, password):
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )


def test_register_ok(client):
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == VALID_USER["email"]
    assert body["username"] == VALID_USER["username"]
    assert "password" not in body


def test_register_duplicate_email(client):
    _register(client)
    resp = _register(client, {**VALID_USER, "username": "user2"})
    assert resp.status_code == 409


def test_register_duplicate_username(client):
    _register(client)
    resp = _register(client, {**VALID_USER, "email": "outro@test.com"})
    assert resp.status_code == 409


def test_register_short_password(client):
    resp = _register(client, {**VALID_USER, "password": "123"})
    assert resp.status_code == 422


def test_login_ok(client):
    _register(client)
    resp = _login(client, VALID_USER["username"], VALID_USER["password"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_by_email(client):
    _register(client)
    resp = _login(client, VALID_USER["email"], VALID_USER["password"])
    assert resp.status_code == 200


def test_login_wrong_password(client):
    _register(client)
    resp = _login(client, VALID_USER["username"], "senha-errada")
    assert resp.status_code == 401


def test_me(client):
    _register(client)
    tokens = _login(client, VALID_USER["username"], VALID_USER["password"]).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == VALID_USER["username"]


def test_me_unauthorized(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_refresh_rotates_token(client):
    _register(client)
    refresh_token = _login(client, VALID_USER["username"], VALID_USER["password"]).json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_refresh = resp.json()["refresh_token"]
    assert new_refresh != refresh_token
    # token antigo deve estar revogado
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401


def test_refresh_invalid_token(client):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "token-inexistente"})
    assert resp.status_code == 401


def test_logout_revokes_refresh(client):
    _register(client)
    tokens = _login(client, VALID_USER["username"], VALID_USER["password"]).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.post("/api/v1/auth/logout", headers=headers)
    assert resp.status_code == 204
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp2.status_code == 401
```

- [ ] **Step 3: Escrever `tests/test_components.py`**

```python
import pytest

from app.core import security
from app.models.user import User

CPU = {
    "name": "AMD Ryzen 5 5600",
    "category": "cpu",
    "brand": "AMD",
    "price": 899.0,
    "specs": {"cores": 6, "socket": "AM4"},
}


def _make_user(db_session, username, email, is_admin=False):
    user = User(
        email=email,
        username=username,
        password_hash=security.hash_password("senha12345"),
        is_admin=is_admin,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers_for(user):
    token = security.create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin(client, db_session):
    return _make_user(db_session, "admin", "admin@test.com", is_admin=True)


@pytest.fixture()
def regular(client, db_session):
    return _make_user(db_session, "regular", "regular@test.com")


def test_list_empty(client):
    resp = client.get("/api/v1/components")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_missing_returns_404(client):
    resp = client.get("/api/v1/components/9999")
    assert resp.status_code == 404


def test_create_requires_admin(client, regular, admin):
    resp_no_token = client.post("/api/v1/components", json=CPU)
    assert resp_no_token.status_code == 401

    resp_regular = client.post("/api/v1/components", json=CPU, headers=_headers_for(regular))
    assert resp_regular.status_code == 403

    resp_admin = client.post("/api/v1/components", json=CPU, headers=_headers_for(admin))
    assert resp_admin.status_code == 201


def test_crud_flow(client, admin):
    headers = _headers_for(admin)

    created = client.post("/api/v1/components", json=CPU, headers=headers)
    assert created.status_code == 201
    comp_id = created.json()["id"]

    listed = client.get("/api/v1/components")
    assert any(c["id"] == comp_id for c in listed.json())

    filtered = client.get("/api/v1/components", params={"category": "cpu"})
    assert any(c["id"] == comp_id for c in filtered.json())

    not_matched = client.get("/api/v1/components", params={"category": "gpu"})
    assert all(c["id"] != comp_id for c in not_matched.json())

    updated = client.put(
        f"/api/v1/components/{comp_id}",
        json={"price": 999.0},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == 999.0

    deleted = client.delete(f"/api/v1/components/{comp_id}", headers=headers)
    assert deleted.status_code == 204

    gone = client.get(f"/api/v1/components/{comp_id}")
    assert gone.status_code == 404


def test_invalid_category_422(client, admin):
    resp = client.post(
        "/api/v1/components",
        json={**CPU, "category": "placa-video"},
        headers=_headers_for(admin),
    )
    assert resp.status_code == 422
```

- [ ] **Step 4: Rodar os testes**

Run: `.\.venv\Scripts\python.exe -m pytest tests -v`
Expected: todos os testes de `test_auth.py`, `test_components.py` e `test_app.py` PASS. Se algum falhar, verificar `docker compose up -d` (banco `byp_test`) e `.env`.

- [ ] **Step 5: Commit**

```bash
git add app/routers/components.py tests/test_auth.py tests/test_components.py
git commit -m "feat: CRUD de componentes com regras de admin + testes de auth e catálogo"
```

---

### Task 10: Seed do catálogo

**Files:**
- Create: `seed.py`

**Interfaces:**
- Consumes: `SessionLocal` (Task 2), `ComponentService` (Task 7), `ComponentCreate` (Task 5).
- Produces: catálogo populado no banco `byp` via `python seed.py`.

- [ ] **Step 1: Escrever `seed.py`**

```python
from app.core.database import SessionLocal
from app.schemas.component import ComponentCreate
from app.services.component_service import ComponentService

SEED = [
    ComponentCreate(
        name="AMD Ryzen 5 5600", category="cpu", brand="AMD", price=899.00,
        specs={"cores": 6, "threads": 12, "socket": "AM4", "tdp": "65W"},
    ),
    ComponentCreate(
        name="Intel Core i5-12400F", category="cpu", brand="Intel", price=899.00,
        specs={"cores": 6, "threads": 12, "socket": "LGA1700", "tdp": "65W"},
    ),
    ComponentCreate(
        name="AMD Ryzen 7 7800X3D", category="cpu", brand="AMD", price=2499.00,
        specs={"cores": 8, "threads": 16, "socket": "AM5", "tdp": "120W"},
    ),
    ComponentCreate(
        name="NVIDIA GeForce RTX 4060", category="gpu", brand="NVIDIA", price=1999.00,
        specs={"vram": "8GB GDDR6", "interface": "PCIe 4.0"},
    ),
    ComponentCreate(
        name="AMD Radeon RX 7600", category="gpu", brand="AMD", price=1799.00,
        specs={"vram": "8GB GDDR6", "interface": "PCIe 4.0"},
    ),
    ComponentCreate(
        name="NVIDIA GeForce RTX 4070 Super", category="gpu", brand="NVIDIA", price=4599.00,
        specs={"vram": "12GB GDDR6X", "interface": "PCIe 4.0"},
    ),
    ComponentCreate(
        name="Corsair Vengeance 16GB DDR5", category="ram", brand="Corsair", price=399.00,
        specs={"capacity": "16GB", "type": "DDR5", "kit": "2x8GB", "speed": "6000MHz"},
    ),
    ComponentCreate(
        name="Kingston Fury 32GB DDR4", category="ram", brand="Kingston", price=549.00,
        specs={"capacity": "32GB", "type": "DDR4", "kit": "2x16GB", "speed": "3200MHz"},
    ),
    ComponentCreate(
        name="Samsung 980 Pro 1TB NVMe", category="storage", brand="Samsung", price=649.00,
        specs={"capacity": "1TB", "interface": "NVMe M.2", "form_factor": "2280"},
    ),
    ComponentCreate(
        name="WD Blue 1TB SATA", category="storage", brand="Western Digital", price=299.00,
        specs={"capacity": "1TB", "interface": "SATA III", "form_factor": "3.5\""},
    ),
]


def seed() -> None:
    db = SessionLocal()
    try:
        service = ComponentService(db)
        if service.list():
            print("Catálogo já populado. Nada a fazer.")
            return
        for component in SEED:
            service.create(component)
        print(f"Seed concluído: {len(SEED)} componentes inseridos.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: Rodar o seed**

Run: `.\.venv\Scripts\python.exe seed.py`
Expected: `Seed concluído: 10 componentes inseridos.`

- [ ] **Step 3: Verificar via API (opcional)**

Run: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` e abrir `http://127.0.0.1:8000/docs`. Testar `GET /api/v1/components` — deve retornar os 10 itens; filtrar por `?category=cpu` — deve retornar 3.

- [ ] **Step 4: Commit**

```bash
git add seed.py
git commit -m "feat: seed do catálogo de componentes"
```

---

### Task 11: README e verificação final

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: tudo.
- Produces: instruções de setup/runbook para qualquer dev.

- [ ] **Step 1: Escrever `README.md`**

```markdown
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
```

- [ ] **Step 2: Rodar suíte completa**

Run: `.\.venv\Scripts\python.exe -m pytest -v`
Expected: todos os testes PASS.

- [ ] **Step 3: Smoke final da API**

Run: `.\.venv\Scripts\python.exe -m uvicorn app.main:app` (em outro terminal)
Expected: `http://127.0.0.1:8000/` retorna `{"message": "Build Your PC API"}`.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: README com setup, runbook e endpoints"
```
