class LoginException(Exception):
    """Classe base para exceções relacionadas ao login."""
    pass

class LoginVazioException(LoginException):
    """Exceção lançada quando o login informado é vazio."""
    def __init__(self, message="O login não pode ser vazio."):
        self.message = message
        super().__init__(self.message)

class LoginMuitoLongoException(LoginException):
    """Exceção lançada quando o login ultrapassa 12 caracteres."""
    def __init__(self, message="O login deve ter no máximo 12 caracteres."):
        self.message = message
        super().__init__(self.message)

class LoginContemNumerosException(LoginException):
    """Exceção lançada quando o login contém números."""
    def __init__(self, message="O login não pode conter números."):
        self.message = message
        super().__init__(self.message)

class CredenciaisInvalidasException(LoginException):
    """Exceção lançada para erros de autenticação (senha incorreta ou usuário inexistente)."""
    def __init__(self, message="Login ou senha incorretos."):
        self.message = message
        super().__init__(self.message)



class DatabaseException(Exception):
    """
    Exceção lançada para erros de acesso ao banco de dados.

    Encapsula falhas de sqlite3.DatabaseError / sqlite3.OperationalError,
    análogo ao SQLException do Java, isolando a infra de banco da camada
    de domínio e serviço.
    """
    def __init__(self, message="Erro de acesso ao banco de dados."):
        self.message = message
        super().__init__(self.message)


class SenhaException(Exception):
    """Classe base para exceções relacionadas à política de senha."""
    pass

class SenhaCurtaException(SenhaException):
    def __init__(self, message="A senha deve ter no mínimo 8 caracteres."):
        self.message = message
        super().__init__(self.message)

class SenhaSemLetraMaiusculaException(SenhaException):
    def __init__(self, message="A senha deve conter pelo menos uma letra maiúscula."):
        self.message = message
        super().__init__(self.message)

class SenhaSemLetraMinusculaException(SenhaException):
    def __init__(self, message="A senha deve conter pelo menos uma letra minúscula."):
        self.message = message
        super().__init__(self.message)

class SenhaSemNumeroException(SenhaException):
    def __init__(self, message="A senha deve conter pelo menos um número."):
        self.message = message
        super().__init__(self.message)

class SenhaSemCaractereEspecialException(SenhaException):
    def __init__(self, message="A senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|')."):
        self.message = message
        super().__init__(self.message)


class UsuarioException(Exception):
    """Classe base para exceções de domínio de usuário."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class CamposObrigatoriosException(UsuarioException):
    def __init__(self, message="Preencha todos os campos obrigatórios para continuar"):
        super().__init__(message)


class EmailInvalidoException(UsuarioException):
    def __init__(self, message="E-mail inválido ou já cadastrado. Utilize seu e-mail institucional."):
        super().__init__(message)


class EmailJaCadastradoException(UsuarioException):
    def __init__(self, message="E-mail inválido ou já cadastrado. Utilize seu e-mail institucional."):
        super().__init__(message)


class UsuarioNaoEncontradoException(UsuarioException):
    def __init__(self, message="Usuário não encontrado."):
        super().__init__(message)


class UsuarioJaEMonitorException(UsuarioException):
    def __init__(self, message="Usuário já é um monitor."):
        super().__init__(message)


class PromocaoApenasParaDiscentesException(UsuarioException):
    def __init__(self, message="Apenas discentes podem ser promovidos a monitor."):
        super().__init__(message)


class DisciplinaVinculadaObrigatoriaException(UsuarioException):
    def __init__(self, message="Disciplina vinculada é obrigatória."):
        super().__init__(message)


class UsuarioNaoEMonitorException(UsuarioException):
    def __init__(self, message="O usuário não é um monitor."):
        super().__init__(message)


# ---------------------------------------------------------------------------
# Exceções de Disciplina
# ---------------------------------------------------------------------------

class DisciplinaException(Exception):
    """Classe base para exceções de domínio de disciplina."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DisciplinaCamposObrigatoriosException(DisciplinaException):
    def __init__(self, message="Preencha todos os campos obrigatórios para continuar."):
        super().__init__(message)


class DisciplinaCodigoJaExisteException(DisciplinaException):
    def __init__(self, message="Já existe uma disciplina com este código."):
        super().__init__(message)


class DisciplinaNaoEncontradaException(DisciplinaException):
    def __init__(self, message="Disciplina não encontrada."):
        super().__init__(message)


# ---------------------------------------------------------------------------
# Exceções de Inscrição de Monitoria
# ---------------------------------------------------------------------------

class InscricaoMonitoriaException(Exception):
    """Classe base para exceções de domínio de inscrição de monitoria."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InscricaoNaoEncontradaException(InscricaoMonitoriaException):
    def __init__(self, message="Inscrição de monitoria não encontrada."):
        super().__init__(message)


class InscricaoMotivacaoVaziaException(InscricaoMonitoriaException):
    def __init__(self, message="A motivação é obrigatória."):
        super().__init__(message)


class InscricaoStatusInvalidoException(InscricaoMonitoriaException):
    def __init__(self, message="Status deve ser PENDENTE, APROVADA ou REJEITADA."):
        super().__init__(message)


class InscricaoSemAtualizacaoParaDesfazerException(InscricaoMonitoriaException):
    def __init__(self, message="Não há atualização anterior para desfazer nesta inscrição."):
        super().__init__(message)


class InscricaoTransicaoInvalidaException(InscricaoMonitoriaException):
    def __init__(self, status_atual: str, status_destino: str):
        super().__init__(
            f"Não é possível transicionar de '{status_atual}' para '{status_destino}'."
        )

