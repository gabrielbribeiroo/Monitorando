from app.business.state.inscricao_status_state import InscricaoStatusState


class RejeitadaState(InscricaoStatusState):
    """Estado final: uma decisao de rejeicao ja tomada nao pode ser revertida via atualizacao."""

    nome = "REJEITADA"
    transicoes_permitidas = frozenset({"REJEITADA"})
