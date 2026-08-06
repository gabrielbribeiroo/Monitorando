"""
Subject (padrao Observer): mantem a lista de observadores interessados em
mudancas de status de InscricaoMonitoria e os notifica quando isso ocorre.
"""

from typing import List

from app.business.observer.inscricao_status_observer import InscricaoStatusObserver
from app.models.inscricao_monitoria import InscricaoMonitoria


class InscricaoStatusSubject:

    def __init__(self) -> None:
        self._observers: List[InscricaoStatusObserver] = []

    def inscrever(self, observer: InscricaoStatusObserver) -> None:
        self._observers.append(observer)

    def remover(self, observer: InscricaoStatusObserver) -> None:
        self._observers.remove(observer)

    def notificar_todos(self, inscricao: InscricaoMonitoria, status_anterior: str) -> None:
        if inscricao.status == status_anterior:
            return
        for observer in self._observers:
            observer.notificar(inscricao, status_anterior)
