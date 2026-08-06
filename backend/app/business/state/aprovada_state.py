from app.business.state.inscricao_status_state import InscricaoStatusState


class AprovadaState(InscricaoStatusState):
    """Estado final: uma decisao de aprovacao ja tomada nao pode ser revertida via atualizacao."""

    nome = "APROVADA"
    transicoes_permitidas = frozenset({"APROVADA"})
