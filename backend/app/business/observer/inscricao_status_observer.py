"""
Contrato (padrao Observer) para quem quer ser avisado quando o status
de uma InscricaoMonitoria muda.
"""

from abc import ABC, abstractmethod

from app.models.inscricao_monitoria import InscricaoMonitoria


class InscricaoStatusObserver(ABC):
    @abstractmethod
    def notificar(self, inscricao: InscricaoMonitoria, status_anterior: str) -> None:
        ...
