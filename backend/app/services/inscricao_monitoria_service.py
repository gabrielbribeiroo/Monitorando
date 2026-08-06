from typing import List
from uuid import UUID

from app.business.memento import InscricaoMonitoriaCaretaker
from app.business.observer import InscricaoStatusObserver, InscricaoStatusSubject, LogInscricaoStatusObserver
from app.business.state import obter_estado
from app.models.inscricao_monitoria import (
    InscricaoMonitoria,
    InscricaoMonitoriaAtualizacao,
    InscricaoMonitoriaCadastro,
    InscricaoMonitoriaResponse,
)
from app.repositories.abstract_disciplina_repository import AbstractDisciplinaRepository
from app.repositories.abstract_inscricao_monitoria_repository import AbstractInscricaoMonitoriaRepository
from app.repositories.abstract_usuario_repository import AbstractUsuarioRepository
from app.exceptions import (
    InscricaoNaoEncontradaException,
    InscricaoMotivacaoVaziaException,
    InscricaoSemAtualizacaoParaDesfazerException,
    InscricaoStatusInvalidoException,
    UsuarioNaoEncontradoException,
    DisciplinaNaoEncontradaException,
)
from app.utils.logger.factory import get_logger


class InscricaoMonitoriaService:
    def __init__(
        self,
        inscricao_repo: AbstractInscricaoMonitoriaRepository,
        usuario_repo: AbstractUsuarioRepository,
        disciplina_repo: AbstractDisciplinaRepository,
    ) -> None:
        """
        Injeção de dependência: o service depende apenas das interfaces,
        nunca de implementações concretas (DIP).
        """
        self._inscricao_repo  = inscricao_repo
        self._usuario_repo    = usuario_repo
        self._disciplina_repo = disciplina_repo
        # Caretaker do padrao Memento: guarda o estado anterior a ultima
        # atualizacao de cada inscricao, para permitir desfaze-la.
        self._caretaker = InscricaoMonitoriaCaretaker()
        # Subject do padrao Observer: avisa interessados sempre que o
        # status de uma inscricao muda (atualizacao ou desfazer).
        self._status_subject = InscricaoStatusSubject()
        self._status_subject.inscrever(LogInscricaoStatusObserver(get_logger()))

    def registrar_observador_status(self, observer: InscricaoStatusObserver) -> None:
        self._status_subject.inscrever(observer)

    def remover_observador_status(self, observer: InscricaoStatusObserver) -> None:
        self._status_subject.remover(observer)

    def cadastrar_inscricao(self, cadastro: InscricaoMonitoriaCadastro) -> InscricaoMonitoria:
        self._validar_relacionamentos(cadastro.usuario_id, cadastro.disciplina_id)
        motivacao = self._validar_motivacao(cadastro.motivacao)

        inscricao = InscricaoMonitoria(
            usuario_id=cadastro.usuario_id,
            disciplina_id=cadastro.disciplina_id,
            motivacao=motivacao,
        )
        self._inscricao_repo.add(inscricao)
        return inscricao

    def listar_inscricoes(self) -> List[InscricaoMonitoriaResponse]:
        return [
            self._to_response(inscricao)
            for inscricao in self._inscricao_repo.find_all()
        ]

    def buscar_inscricao_por_id(self, id: UUID) -> InscricaoMonitoria:
        inscricao = self._inscricao_repo.find_by_id(id)
        if inscricao is None:
            raise InscricaoNaoEncontradaException(
                f"Inscrição de monitoria com id '{id}' não encontrada."
            )
        return inscricao

    def atualizar_inscricao(
        self,
        id: UUID,
        atualizacao: InscricaoMonitoriaAtualizacao,
    ) -> InscricaoMonitoria:
        inscricao_atual = self.buscar_inscricao_por_id(id)
        self._validar_relacionamentos(atualizacao.usuario_id, atualizacao.disciplina_id)
        motivacao = self._validar_motivacao(atualizacao.motivacao)
        status    = self._validar_status(atualizacao.status)

        # State: o status atual decide para quais status a inscricao pode
        # transicionar (ex.: uma decisao ja tomada — APROVADA/REJEITADA —
        # nao pode ser revertida por uma atualizacao comum).
        novo_estado = obter_estado(inscricao_atual.status).transicionar(status)

        # Memento: guarda o estado atual antes de sobrescreve-lo, para
        # permitir desfazer apenas esta atualizacao.
        self._caretaker.salvar(inscricao_atual.criar_memento())

        inscricao = InscricaoMonitoria(
            id=id,
            usuario_id=atualizacao.usuario_id,
            disciplina_id=atualizacao.disciplina_id,
            motivacao=motivacao,
            status=novo_estado.nome,
        )
        self._inscricao_repo.update(inscricao)
        self._status_subject.notificar_todos(inscricao, inscricao_atual.status)
        return inscricao

    def desfazer_ultima_atualizacao(self, id: UUID) -> InscricaoMonitoria:
        inscricao_atual = self.buscar_inscricao_por_id(id)

        memento = self._caretaker.obter(id)
        if memento is None:
            raise InscricaoSemAtualizacaoParaDesfazerException()

        inscricao_restaurada = InscricaoMonitoria.restaurar_memento(memento)
        self._inscricao_repo.update(inscricao_restaurada)
        # So e possivel desfazer a atualizacao mais recente: uma vez
        # restaurado, o memento e descartado.
        self._caretaker.descartar(id)
        self._status_subject.notificar_todos(inscricao_restaurada, inscricao_atual.status)
        return inscricao_restaurada

    def remover_inscricao(self, id: UUID) -> None:
        removida = self._inscricao_repo.delete(id)
        if not removida:
            raise InscricaoNaoEncontradaException(
                f"Inscrição de monitoria com id '{id}' não encontrada."
            )
        self._caretaker.descartar(id)

    def contar_inscricoes(self) -> int:
        return self._inscricao_repo.count()

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _validar_relacionamentos(self, usuario_id: UUID, disciplina_id: UUID) -> None:
        if self._usuario_repo.find_by_id(usuario_id) is None:
            raise UsuarioNaoEncontradoException(
                f"Usuário com id '{usuario_id}' não encontrado."
            )
        disciplina_existe = any(
            d.id == disciplina_id for d in self._disciplina_repo.find_all()
        )
        if not disciplina_existe:
            raise DisciplinaNaoEncontradaException(
                f"Disciplina com id '{disciplina_id}' não encontrada."
            )

    def _validar_motivacao(self, motivacao: str) -> str:
        if not motivacao or not motivacao.strip():
            raise InscricaoMotivacaoVaziaException()
        return motivacao.strip()

    def _validar_status(self, status: str) -> str:
        status_normalizado = status.strip().upper() if status else ""
        status_validos = {"PENDENTE", "APROVADA", "REJEITADA"}
        if status_normalizado not in status_validos:
            raise InscricaoStatusInvalidoException()
        return status_normalizado

    def _to_response(self, inscricao: InscricaoMonitoria) -> InscricaoMonitoriaResponse:
        return InscricaoMonitoriaResponse(
            id=inscricao.id,
            usuario_id=inscricao.usuario_id,
            disciplina_id=inscricao.disciplina_id,
            motivacao=inscricao.motivacao,
            status=inscricao.status,
        )
