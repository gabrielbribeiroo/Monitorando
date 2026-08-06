import pytest
from fastapi.testclient import TestClient

from app.controllers.facade_singleton_controller import FacadeSingletonController
from app.main import app

# Isolamento é feito pela fixture `reset_repositorios` (autouse) do conftest.py.


def _criar_usuario(client: TestClient):
    response = client.post("/usuarios", json={
        "nome": "Ana Silva",
        "login": "anasilva",
        "email": "ana.silva@discente.ufpb.br",
        "senha": "Password123!",
        "matricula": "2023001111",
        "curso": "Ciencia da Computacao",
        "periodo": 4,
    })
    assert response.status_code == 201, response.json()
    return response.json()


def _criar_disciplina(client: TestClient):
    response = client.post("/disciplinas/", json={
        "codigo": "MPS001",
        "nome": "Metodos de Projeto de Software",
        "ementa": "Processos, arquitetura e padroes de projeto.",
        "periodo": 5,
    })
    assert response.status_code == 201, response.json()
    return response.json()


def _criar_inscricao(client: TestClient):
    usuario    = _criar_usuario(client)
    disciplina = _criar_disciplina(client)
    response = client.post("/inscricoes-monitoria/", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Tenho interesse em apoiar a turma na disciplina.",
    })
    assert response.status_code == 201, response.json()
    return response.json(), usuario, disciplina


def test_criar_inscricao_monitoria_com_relacionamentos(client: TestClient):
    inscricao, usuario, disciplina = _criar_inscricao(client)

    assert inscricao["usuario_id"] == usuario["id"]
    assert inscricao["disciplina_id"] == disciplina["id"]
    assert inscricao["motivacao"] == "Tenho interesse em apoiar a turma na disciplina."
    assert inscricao["status"] == "PENDENTE"


def test_listar_e_detalhar_inscricao_monitoria(client: TestClient):
    inscricao, _, _ = _criar_inscricao(client)

    listagem = client.get("/inscricoes-monitoria/")
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1
    assert listagem.json()[0]["id"] == inscricao["id"]

    detalhe = client.get(f"/inscricoes-monitoria/{inscricao['id']}")
    assert detalhe.status_code == 200
    assert detalhe.json()["id"] == inscricao["id"]


def test_atualizar_inscricao_monitoria(client: TestClient):
    inscricao, usuario, disciplina = _criar_inscricao(client)

    response = client.put(f"/inscricoes-monitoria/{inscricao['id']}", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Atualizei minha motivacao para a monitoria.",
        "status": "APROVADA",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["motivacao"] == "Atualizei minha motivacao para a monitoria."
    assert data["status"] == "APROVADA"


def test_atualizar_inscricao_monitoria_permite_reenvio_no_mesmo_status(client: TestClient):
    inscricao, usuario, disciplina = _criar_inscricao(client)

    client.put(f"/inscricoes-monitoria/{inscricao['id']}", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Motivacao inicial.",
        "status": "APROVADA",
    })

    response = client.put(f"/inscricoes-monitoria/{inscricao['id']}", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Motivacao revisada apos aprovacao.",
        "status": "APROVADA",
    })

    assert response.status_code == 200
    assert response.json()["motivacao"] == "Motivacao revisada apos aprovacao."


def test_atualizar_inscricao_monitoria_rejeita_transicao_de_estado_final(client: TestClient):
    inscricao, usuario, disciplina = _criar_inscricao(client)

    client.put(f"/inscricoes-monitoria/{inscricao['id']}", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Motivacao inicial.",
        "status": "APROVADA",
    })

    response = client.put(f"/inscricoes-monitoria/{inscricao['id']}", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Tentando reverter a decisao.",
        "status": "REJEITADA",
    })

    assert response.status_code == 409


def test_desfazer_atualizacao_inscricao_monitoria_restaura_estado_anterior(client: TestClient):
    inscricao, usuario, disciplina = _criar_inscricao(client)

    response = client.put(f"/inscricoes-monitoria/{inscricao['id']}", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Atualizei minha motivacao para a monitoria.",
        "status": "APROVADA",
    })
    assert response.status_code == 200

    desfazer = client.post(f"/inscricoes-monitoria/{inscricao['id']}/desfazer-atualizacao")
    assert desfazer.status_code == 200
    data = desfazer.json()
    assert data["motivacao"] == inscricao["motivacao"]
    assert data["status"] == inscricao["status"]

    detalhe = client.get(f"/inscricoes-monitoria/{inscricao['id']}")
    assert detalhe.json()["motivacao"] == inscricao["motivacao"]
    assert detalhe.json()["status"] == inscricao["status"]


def test_desfazer_atualizacao_inscricao_monitoria_so_permite_a_ultima(client: TestClient):
    inscricao, usuario, disciplina = _criar_inscricao(client)

    client.put(f"/inscricoes-monitoria/{inscricao['id']}", json={
        "usuario_id": usuario["id"],
        "disciplina_id": disciplina["id"],
        "motivacao": "Primeira atualizacao.",
        "status": "APROVADA",
    })

    primeiro_desfazer = client.post(f"/inscricoes-monitoria/{inscricao['id']}/desfazer-atualizacao")
    assert primeiro_desfazer.status_code == 200

    segundo_desfazer = client.post(f"/inscricoes-monitoria/{inscricao['id']}/desfazer-atualizacao")
    assert segundo_desfazer.status_code == 409


def test_desfazer_atualizacao_inscricao_monitoria_inexistente(client: TestClient):
    response = client.post(
        "/inscricoes-monitoria/00000000-0000-0000-0000-000000000001/desfazer-atualizacao"
    )
    assert response.status_code == 404


def test_remover_inscricao_monitoria(client: TestClient):
    inscricao, _, _ = _criar_inscricao(client)

    response = client.delete(f"/inscricoes-monitoria/{inscricao['id']}")
    assert response.status_code == 204

    detalhe = client.get(f"/inscricoes-monitoria/{inscricao['id']}")
    assert detalhe.status_code == 404


def test_criar_inscricao_rejeita_usuario_inexistente(client: TestClient):
    disciplina = _criar_disciplina(client)

    response = client.post("/inscricoes-monitoria/", json={
        "usuario_id": "00000000-0000-0000-0000-000000000001",
        "disciplina_id": disciplina["id"],
        "motivacao": "Quero participar.",
    })

    assert response.status_code == 404
    assert "Usuário" in response.json()["detail"]


def test_facade_singleton_controller_retorna_quantidade_total_de_entidades(client: TestClient):
    """
    Testa:
    1. Que FacadeSingletonController é um Singleton (mesma instância).
    2. Que o endpoint /facade/quantidade-entidades conta corretamente.
    """
    _criar_inscricao(client)  # cria 1 usuario + 1 disciplina + 1 inscricao

    # Singleton: duas instanciações retornam o mesmo objeto
    facade = FacadeSingletonController()
    assert facade is FacadeSingletonController()
    assert facade.execute_command(
        FacadeSingletonController.QUANTIDADE_ENTIDADES_CADASTRADAS
    ) == 3

    response = client.get("/facade/quantidade-entidades")
    assert response.status_code == 200
    assert response.json()["quantidade"] == 3
