from typing import Dict

from app.business.state.aprovada_state import AprovadaState
from app.business.state.inscricao_status_state import InscricaoStatusState
from app.business.state.pendente_state import PendenteState
from app.business.state.rejeitada_state import RejeitadaState
from app.exceptions import InscricaoStatusInvalidoException

_ESTADOS: Dict[str, InscricaoStatusState] = {
    "PENDENTE": PendenteState(),
    "APROVADA": AprovadaState(),
    "REJEITADA": RejeitadaState(),
}


def obter_estado(status: str) -> InscricaoStatusState:
    try:
        return _ESTADOS[status]
    except KeyError as exc:
        raise InscricaoStatusInvalidoException() from exc
