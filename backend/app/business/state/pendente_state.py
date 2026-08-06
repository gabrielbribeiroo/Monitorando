from app.business.state.inscricao_status_state import InscricaoStatusState


class PendenteState(InscricaoStatusState):
    """Estado inicial: ainda pode ser aprovada, rejeitada ou mantida pendente."""

    nome = "PENDENTE"
    transicoes_permitidas = frozenset({"PENDENTE", "APROVADA", "REJEITADA"})
