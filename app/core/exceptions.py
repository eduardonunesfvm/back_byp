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
