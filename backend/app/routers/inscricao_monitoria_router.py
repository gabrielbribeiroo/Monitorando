from fastapi import APIRouter, Request, status, HTTPException
from typing import List
from uuid import UUID

from app.models.inscricao_monitoria import (
    InscricaoMonitoriaAtualizacao,
    InscricaoMonitoriaCadastro,
    InscricaoMonitoriaResponse,
)
from app.exceptions import (
    InscricaoNaoEncontradaException,
    InscricaoMotivacaoVaziaException,
    InscricaoSemAtualizacaoParaDesfazerException,
    InscricaoStatusInvalidoException,
    InscricaoTransicaoInvalidaException,
    UsuarioNaoEncontradoException,
    DisciplinaNaoEncontradaException,
)

router = APIRouter(prefix="/inscricoes-monitoria", tags=["Inscricoes de Monitoria"])


@router.post("/", response_model=InscricaoMonitoriaResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_inscricao(cadastro: InscricaoMonitoriaCadastro, request: Request):
    try:
        return request.app.state.inscricao_monitoria_service.cadastrar_inscricao(cadastro)
    except (UsuarioNaoEncontradoException, DisciplinaNaoEncontradaException) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InscricaoMotivacaoVaziaException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/", response_model=List[InscricaoMonitoriaResponse])
def listar_inscricoes(request: Request):
    return request.app.state.inscricao_monitoria_service.listar_inscricoes()


@router.get("/{id}", response_model=InscricaoMonitoriaResponse)
def detalhar_inscricao(id: UUID, request: Request):
    try:
        return request.app.state.inscricao_monitoria_service.buscar_inscricao_por_id(id)
    except InscricaoNaoEncontradaException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.put("/{id}", response_model=InscricaoMonitoriaResponse)
def atualizar_inscricao(id: UUID, atualizacao: InscricaoMonitoriaAtualizacao, request: Request):
    try:
        return request.app.state.inscricao_monitoria_service.atualizar_inscricao(id, atualizacao)
    except InscricaoNaoEncontradaException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except (UsuarioNaoEncontradoException, DisciplinaNaoEncontradaException) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except (InscricaoMotivacaoVaziaException, InscricaoStatusInvalidoException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except InscricaoTransicaoInvalidaException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.post("/{id}/desfazer-atualizacao", response_model=InscricaoMonitoriaResponse)
def desfazer_atualizacao_inscricao(id: UUID, request: Request):
    try:
        return request.app.state.inscricao_monitoria_service.desfazer_ultima_atualizacao(id)
    except InscricaoNaoEncontradaException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InscricaoSemAtualizacaoParaDesfazerException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_inscricao(id: UUID, request: Request):
    try:
        request.app.state.inscricao_monitoria_service.remover_inscricao(id)
    except InscricaoNaoEncontradaException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
