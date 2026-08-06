"""
Contrato (padrao State) para o status de uma InscricaoMonitoria.

Cada estado concreto sabe para quais status pode transicionar, retirando
essa regra de negocio do service e evitando condicionais espalhadas por
"if status == ...".
"""

from abc import ABC
from typing import ClassVar, FrozenSet

from app.exceptions import InscricaoTransicaoInvalidaException


class InscricaoStatusState(ABC):
    nome: ClassVar[str]
    transicoes_permitidas: ClassVar[FrozenSet[str]]

    def transicionar(self, novo_status: str) -> "InscricaoStatusState":
        from app.business.state.inscricao_status_state_factory import obter_estado

        if novo_status not in self.transicoes_permitidas:
            raise InscricaoTransicaoInvalidaException(self.nome, novo_status)
        return obter_estado(novo_status)
