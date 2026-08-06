from app.business.observer.inscricao_status_observer import InscricaoStatusObserver
from app.models.inscricao_monitoria import InscricaoMonitoria
from app.utils.logger.logger_interface import ILogger


class LogInscricaoStatusObserver(InscricaoStatusObserver):
    """Observer padrao: registra no log toda mudanca de status de inscricao."""

    def __init__(self, logger: ILogger) -> None:
        self._logger = logger

    def notificar(self, inscricao: InscricaoMonitoria, status_anterior: str) -> None:
        self._logger.info(
            f"[INSCRICAO] {inscricao.id}: status alterado de "
            f"'{status_anterior}' para '{inscricao.status}'."
        )
