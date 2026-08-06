"""
Testes de integração para o módulo de Disciplinas.

Isolamento: a fixture `reset_repositorios` (autouse, definida em conftest.py)
limpa o store InMemory antes e após cada teste — sem I/O de disco.
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# O client e o reset são fornecidos pelo conftest.py via fixture.
# Aqui apenas declaramos que precisamos do `client`.
# ---------------------------------------------------------------------------


# ===========================================================================
# CADASTRO DE DISCIPLINAS (POST /disciplinas/)
# ===========================================================================

def test_criar_disciplina_com_sucesso(client: TestClient):
    payload = {
        "codigo": "COMP001",
        "nome": "Introdução à Programação",
        "ementa": "Lógica de programação, variáveis, laços de repetição e funções.",
        "periodo": 1
    }

    response = client.post("/disciplinas/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "COMP001"
    assert data["nome"] == "Introdução à Programação"
    assert data["periodo"] == 1
    assert "id" in data


def test_criar_disciplina_codigo_normalizado_maiusculo(client: TestClient):
    """O código deve ser normalizado para letras maiúsculas pelo service."""
    payload = {
        "codigo": "comp010",
        "nome": "Banco de Dados",
        "ementa": "Modelagem relacional e SQL.",
        "periodo": 3
    }

    response = client.post("/disciplinas/", json=payload)
    assert response.status_code == 201
    assert response.json()["codigo"] == "COMP010"


def test_criar_disciplina_codigo_duplicado(client: TestClient):
    payload = {
        "codigo": "COMP002",
        "nome": "Estrutura de Dados",
        "ementa": "Listas, pilhas, filas e árvores.",
        "periodo": 3
    }
    # Primeira criação — deve ter sucesso
    res1 = client.post("/disciplinas/", json=payload)
    assert res1.status_code == 201

    # Segunda criação com mesmo código — deve falhar
    response = client.post("/disciplinas/", json=payload)
    assert response.status_code == 409
    assert "Já existe uma disciplina com este código" in response.json()["detail"]


def test_criar_disciplina_dados_invalidos(client: TestClient):
    payload = {
        "codigo": "",
        "nome": "Materia Vazia",
        "ementa": "",
        "periodo": 1
    }
    response = client.post("/disciplinas/", json=payload)
    assert response.status_code == 400
    assert "Preencha todos os campos obrigatórios" in response.json()["detail"]


def test_criar_disciplina_nome_vazio(client: TestClient):
    payload = {
        "codigo": "COMP003",
        "nome": "",
        "ementa": "Ementa válida.",
        "periodo": 2
    }
    response = client.post("/disciplinas/", json=payload)
    assert response.status_code == 400
    assert "Preencha todos os campos obrigatórios" in response.json()["detail"]


# ===========================================================================
# LISTAGEM DE DISCIPLINAS (GET /disciplinas/)
# ===========================================================================

def test_listar_disciplinas_vazio(client: TestClient):
    """Sem disciplinas cadastradas, deve retornar lista vazia."""
    response = client.get("/disciplinas/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_listar_disciplinas_com_registros(client: TestClient):
    """Disciplinas cadastradas devem aparecer na listagem."""
    payloads = [
        {"codigo": "COMP004", "nome": "Cálculo I", "ementa": "Limites e derivadas.", "periodo": 1},
        {"codigo": "COMP005", "nome": "Álgebra Linear", "ementa": "Matrizes e vetores.", "periodo": 2},
    ]
    for p in payloads:
        client.post("/disciplinas/", json=p)

    response = client.get("/disciplinas/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    codigos = [d["codigo"] for d in data]
    assert "COMP004" in codigos
    assert "COMP005" in codigos


def test_listar_disciplinas_estrutura_de_resposta(client: TestClient):
    """Cada item da listagem deve conter os campos esperados."""
    payload = {
        "codigo": "COMP006",
        "nome": "Programação Orientada a Objetos",
        "ementa": "Classes, objetos, herança e polimorfismo.",
        "periodo": 2
    }
    client.post("/disciplinas/", json=payload)

    response = client.get("/disciplinas/")
    assert response.status_code == 200
    item = response.json()[0]
    assert "id" in item
    assert "codigo" in item
    assert "nome" in item
    assert "ementa" in item
    assert "periodo" in item
