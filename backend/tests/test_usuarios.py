import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.usuario import Discente, Docente
from app.models.enums import TipoPerfil
from uuid import uuid4


def _index_to_letters(index: int) -> str:
    letters = ""
    while index >= 0:
        letters = chr(97 + (index % 26)) + letters
        index = (index // 26) - 1
    return letters


# Isolamento é feito pela fixture `reset_repositorios` (autouse) do conftest.py.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
DISCENTE_PAYLOAD = {
    "nome": "João Silva",
    "login": "joaosilva",
    "email": "joao.silva@discente.ufpb.br",
    "senha": "Password123!",
    "matricula": "2023001234",
    "curso": "Engenharia de Computação",
    "periodo": 3,
}

DOCENTE_PAYLOAD = {
    "nome": "Maria Souza",
    "login": "mariasouza",
    "email": "maria.souza@ufpb.br",
    "senha": "DocentePass1!",
    "siape": "1122334",
    "departamento": "Departamento de Informática",
    "isCoordenador": True,
}


def _criar_discente(client: TestClient, **overrides):
    """Cria um discente via API e retorna o JSON de resposta."""
    payload = {**DISCENTE_PAYLOAD, **overrides}
    res = client.post("/usuarios", json=payload)
    assert res.status_code == 201, res.json()
    return res.json()


def _seed_discentes(quantidade: int, prefixo: str = "Aluno"):
    """Insere `quantidade` discentes diretamente no repositório InMemory."""
    repo = app.state.usuario_service._repo
    for i in range(quantidade):
        repo.add(
            Discente(
                id=uuid4(),
                nome=f"{prefixo} {i + 1}",
                login=f"aluno{_index_to_letters(i)}",
                email=f"aluno{i + 1}@discente.ufpb.br",
                senha="Hash123!",
                perfil=TipoPerfil.DISCENTE,
                ativo=True,
                matricula=f"20230{i + 1:05d}",
                curso="Ciência da Computação",
                periodo=i % 8 + 1,
            )
        )


# ===========================================================================
# CADASTRO DE USUÁRIOS (POST /usuarios)
# ===========================================================================

class TestCadastroUsuario:
    def test_criar_discente_com_sucesso(self, client: TestClient):
        response = client.post("/usuarios", json=DISCENTE_PAYLOAD)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["nome"] == "João Silva"
        assert data["email"] == "joao.silva@discente.ufpb.br"
        assert data["perfil"] == "DISCENTE"
        assert data["matricula"] == "2023001234"
        assert data["curso"] == "Engenharia de Computação"
        assert data["periodo"] == 3
        assert data["ativo"] is True
        assert "senha" not in data

    def test_criar_docente_com_sucesso(self, client: TestClient):
        response = client.post("/usuarios", json=DOCENTE_PAYLOAD)

        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Maria Souza"
        assert data["email"] == "maria.souza@ufpb.br"
        assert data["perfil"] == "DOCENTE"
        assert data["siape"] == "1122334"
        assert data["departamento"] == "Departamento de Informática"
        assert data["isCoordenador"] is True
        assert data["ativo"] is True
        assert "senha" not in data

    def test_criar_docente_ci_com_sucesso(self, client: TestClient):
        payload = {"nome": "Carlos Roberto", "login": "carlosrob", "email": "carlos@ci.ufpb.br", "senha": "DocentePass2!"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["perfil"] == "DOCENTE"
        assert data["siape"] == ""
        assert data["departamento"] == ""
        assert data["isCoordenador"] is False

    def test_erro_email_nao_institucional(self, client: TestClient):
        payload = {**DISCENTE_PAYLOAD, "email": "joao@gmail.com"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "E-mail inválido ou já cadastrado. Utilize seu e-mail institucional."

    def test_erro_senha_curta(self, client: TestClient):
        payload = {**DISCENTE_PAYLOAD, "senha": "Pas1!"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 400
        assert "8 caracteres" in response.json()["detail"]

    def test_erro_senha_sem_maiuscula(self, client: TestClient):
        payload = {**DISCENTE_PAYLOAD, "senha": "password123!"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 400
        assert "letra maiúscula" in response.json()["detail"]

    def test_erro_senha_sem_numero(self, client: TestClient):
        payload = {**DISCENTE_PAYLOAD, "senha": "Password!"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 400
        assert "número" in response.json()["detail"]

    def test_erro_senha_sem_minuscula(self, client: TestClient):
        payload = {**DISCENTE_PAYLOAD, "senha": "PASSWORD123!"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 400
        assert "letra minúscula" in response.json()["detail"]

    def test_erro_senha_sem_especial(self, client: TestClient):
        payload = {**DISCENTE_PAYLOAD, "senha": "Password123"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 400
        assert "caractere especial" in response.json()["detail"]

    def test_erro_discente_sem_matricula(self, client: TestClient):
        payload = {k: v for k, v in DISCENTE_PAYLOAD.items() if k != "matricula"}
        response = client.post("/usuarios", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Preencha todos os campos obrigatórios para continuar"

    def test_erro_email_ja_cadastrado(self, client: TestClient):
        client.post("/usuarios", json=DISCENTE_PAYLOAD)
        payload2 = {**DISCENTE_PAYLOAD, "nome": "Outro Nome", "matricula": "9999999999"}
        response = client.post("/usuarios", json=payload2)

        assert response.status_code == 400
        assert response.json()["detail"] == "E-mail inválido ou já cadastrado. Utilize seu e-mail institucional."


# ===========================================================================
# LISTAGEM COM PAGINAÇÃO (GET /usuarios) — RF007
# ===========================================================================

class TestListarUsuarios:
    def test_listar_vazio_retorna_lista_vazia(self, client: TestClient):
        response = client.get("/usuarios")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["usuarios"] == []
        assert data["pagina"] == 1
        assert data["limite"] == 50

    def test_listar_estrutura_de_resposta(self, client: TestClient):
        _seed_discentes(3)
        response = client.get("/usuarios")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pagina" in data
        assert "limite" in data
        assert "usuarios" in data

    def test_paginacao_padrao_50_registros(self, client: TestClient):
        _seed_discentes(120)
        response = client.get("/usuarios")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 120
        assert data["pagina"] == 1
        assert data["limite"] == 50
        assert len(data["usuarios"]) == 50

    def test_paginacao_segunda_pagina(self, client: TestClient):
        _seed_discentes(120)
        response = client.get("/usuarios?pagina=2&limite=50")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 120
        assert data["pagina"] == 2
        assert len(data["usuarios"]) == 50

    def test_paginacao_ultima_pagina_parcial(self, client: TestClient):
        _seed_discentes(35)
        response = client.get("/usuarios?pagina=2&limite=20")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 35
        assert len(data["usuarios"]) == 15  # 35 - 20 = 15 restantes

    def test_limite_customizado(self, client: TestClient):
        _seed_discentes(30)
        response = client.get("/usuarios?limite=10")

        assert response.status_code == 200
        data = response.json()
        assert data["limite"] == 10
        assert len(data["usuarios"]) == 10

    def test_limite_maximo_200_respeitado(self, client: TestClient):
        _seed_discentes(250)
        response = client.get("/usuarios?limite=200")

        assert response.status_code == 200
        data = response.json()
        assert len(data["usuarios"]) == 200

    def test_limite_acima_do_maximo_retorna_422(self, client: TestClient):
        # FastAPI valida le=200 no Query param e rejeita com 422
        response = client.get("/usuarios?limite=201")

        assert response.status_code == 422

    def test_pagina_invalida_retorna_422(self, client: TestClient):
        response = client.get("/usuarios?pagina=0")

        assert response.status_code == 422

    def test_senha_nunca_exposta_na_listagem(self, client: TestClient):
        _seed_discentes(1)
        response = client.get("/usuarios")

        assert response.status_code == 200
        for usuario in response.json()["usuarios"]:
            assert "senha" not in usuario


# ===========================================================================
# DETALHE POR ID (GET /usuarios/{id})
# ===========================================================================

class TestDetalharUsuario:
    def test_detalhar_discente_com_sucesso(self, client: TestClient):
        criado = _criar_discente(client)
        usuario_id = criado["id"]

        response = client.get(f"/usuarios/{usuario_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == usuario_id
        assert data["nome"] == DISCENTE_PAYLOAD["nome"]
        assert data["email"] == DISCENTE_PAYLOAD["email"]
        assert data["perfil"] == "DISCENTE"
        assert data["matricula"] == DISCENTE_PAYLOAD["matricula"]
        assert "senha" not in data

    def test_detalhar_docente_com_sucesso(self, client: TestClient):
        criado = client.post("/usuarios", json=DOCENTE_PAYLOAD).json()
        usuario_id = criado["id"]

        response = client.get(f"/usuarios/{usuario_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == usuario_id
        assert data["perfil"] == "DOCENTE"
        assert data["siape"] == DOCENTE_PAYLOAD["siape"]
        assert "senha" not in data

    def test_detalhar_id_inexistente_retorna_404(self, client: TestClient):
        id_fake = str(uuid4())
        response = client.get(f"/usuarios/{id_fake}")

        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]

    def test_detalhar_uuid_invalido_retorna_422(self, client: TestClient):
        response = client.get("/usuarios/nao-e-um-uuid-valido")

        assert response.status_code == 422


# ===========================================================================
# FILTROS (GET /usuarios?nome=...&matricula=...) — RF008
# ===========================================================================

class TestFiltrarUsuarios:
    def _seed_mix(self):
        """Insere 3 discentes e 1 docente com nomes e matrículas conhecidos."""
        repo = app.state.usuario_service._repo
        repo.add(Discente(
            id=uuid4(), nome="Ana Paula", login="anapaula", email="ana@discente.ufpb.br",
            senha="Hash1!", perfil=TipoPerfil.DISCENTE, ativo=True,
            matricula="2023000001", curso="CC", periodo=1,
        ))
        repo.add(Discente(
            id=uuid4(), nome="Ana Beatriz", login="anabeatriz", email="anab@discente.ufpb.br",
            senha="Hash2!", perfil=TipoPerfil.DISCENTE, ativo=True,
            matricula="2023000002", curso="SI", periodo=2,
        ))
        repo.add(Discente(
            id=uuid4(), nome="Carlos Eduardo", login="carlosedu", email="carlos@discente.ufpb.br",
            senha="Hash3!", perfil=TipoPerfil.DISCENTE, ativo=True,
            matricula="2023000003", curso="EC", periodo=3,
        ))
        repo.add(Docente(
            id=uuid4(), nome="Ana Professora", login="anaprof", email="ana.prof@ufpb.br",
            senha="Hash4!", perfil=TipoPerfil.DOCENTE, ativo=True,
        ))

    # --- Filtro por nome ---

    def test_filtro_nome_parcial_retorna_correspondencias(self, client: TestClient):
        self._seed_mix()
        response = client.get("/usuarios?nome=Ana")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # Ana Paula, Ana Beatriz, Ana Professora
        nomes = [u["nome"] for u in data["usuarios"]]
        assert all("Ana" in n for n in nomes)

    def test_filtro_nome_case_insensitive(self, client: TestClient):
        self._seed_mix()
        response = client.get("/usuarios?nome=ana")

        assert response.status_code == 200
        assert response.json()["total"] == 3

    def test_filtro_nome_sem_resultado_retorna_404(self, client: TestClient):
        self._seed_mix()
        response = client.get("/usuarios?nome=Inexistente")

        assert response.status_code == 404
        assert "Inexistente" in response.json()["detail"]

    def test_filtro_nome_retorna_somente_correspondencias(self, client: TestClient):
        self._seed_mix()
        response = client.get("/usuarios?nome=Carlos")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["usuarios"][0]["nome"] == "Carlos Eduardo"

    # --- Filtro por matrícula ---

    def test_filtro_matricula_exata_retorna_discente(self, client: TestClient):
        self._seed_mix()
        response = client.get("/usuarios?matricula=2023000001")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["usuarios"][0]["nome"] == "Ana Paula"

    def test_filtro_matricula_inexistente_retorna_404(self, client: TestClient):
        self._seed_mix()
        response = client.get("/usuarios?matricula=9999999999")

        assert response.status_code == 404
        assert "9999999999" in response.json()["detail"]

    def test_filtro_matricula_nao_corresponde_a_docente(self, client: TestClient):
        """Docentes não têm matrícula — qualquer busca por matrícula não deve retorná-los."""
        self._seed_mix()
        response = client.get("/usuarios?matricula=0000000000")

        assert response.status_code == 404

    # --- Filtros combinados ---

    def test_filtro_nome_e_matricula_combinados(self, client: TestClient):
        self._seed_mix()
        response = client.get("/usuarios?nome=Ana&matricula=2023000002")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["usuarios"][0]["nome"] == "Ana Beatriz"

    def test_filtro_nome_e_matricula_sem_resultado_retorna_404(self, client: TestClient):
        self._seed_mix()
        # Nome existe, mas matrícula não corresponde ao mesmo usuário
        response = client.get("/usuarios?nome=Carlos&matricula=2023000001")

        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "Carlos" in detail
        assert "2023000001" in detail

    # --- Filtros com paginação ---

    def test_filtro_nome_com_paginacao(self, client: TestClient):
        # Insere 15 discentes com "Teste" no nome
        repo = app.state.usuario_service._repo
        for i in range(15):
            repo.add(Discente(
                id=uuid4(), nome=f"Teste Usuario {i + 1}",
                login=f"teste{_index_to_letters(i)}",
                email=f"teste{i + 1}@discente.ufpb.br",
                senha="Hash1!", perfil=TipoPerfil.DISCENTE, ativo=True,
                matricula=f"2024{i + 1:06d}",
            ))

        response = client.get("/usuarios?nome=Teste&pagina=1&limite=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["usuarios"]) == 10
        assert data["pagina"] == 1

    def test_filtro_nome_segunda_pagina(self, client: TestClient):
        repo = app.state.usuario_service._repo
        for i in range(15):
            repo.add(Discente(
                id=uuid4(), nome=f"Teste Usuario {i + 1}",
                login=f"teste{_index_to_letters(i)}",
                email=f"teste{i + 1}@discente.ufpb.br",
                senha="Hash1!", perfil=TipoPerfil.DISCENTE, ativo=True,
                matricula=f"2024{i + 1:06d}",
            ))

        response = client.get("/usuarios?nome=Teste&pagina=2&limite=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["usuarios"]) == 5  # 15 - 10 = 5 restantes


# ===========================================================================
# PROMOÇÃO E REVOGAÇÃO DE MONITORES (PATCH /usuarios/{id}/promover e /revogar)
# ===========================================================================

class TestPromocaoRevogacao:
    def test_promover_discente_com_sucesso(self, client: TestClient):
        # 1. Criar um discente
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        # 2. Promover discente a monitor
        payload = {
            "disciplinaVinculada": "Métodos de Projeto de Software",
            "cargaHoraria": 12
        }
        headers = {"X-Perfil": "COORDENADOR"}
        response = client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == aluno_id
        assert data["perfil"] == "MONITOR"
        assert data["disciplinaVinculada"] == "Métodos de Projeto de Software"
        assert data["cargaHoraria"] == 12
        assert data["disponivel"] is True

        # 3. Verificar que o detalhe do usuário retorna MonitorResponse
        detail_res = client.get(f"/usuarios/{aluno_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["perfil"] == "MONITOR"
        assert detail_data["cargaHoraria"] == 12
        assert detail_data["disciplinaVinculada"] == "Métodos de Projeto de Software"
        assert detail_data["matricula"] == aluno["matricula"]

    def test_promover_erro_sem_cabecalho_coordenador(self, client: TestClient):
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        payload = {
            "disciplinaVinculada": "Métodos de Projeto de Software",
            "cargaHoraria": 12
        }

        # Sem cabeçalho
        response = client.patch(f"/usuarios/{aluno_id}/promover", json=payload)
        assert response.status_code == 403
        assert "apenas coordenadores" in response.json()["detail"]

        # Cabeçalho incorreto
        headers = {"X-Perfil": "DISCENTE"}
        response = client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)
        assert response.status_code == 403
        assert "apenas coordenadores" in response.json()["detail"]

    def test_promover_erro_usuario_inexistente(self, client: TestClient):
        fake_id = str(uuid4())
        payload = {
            "disciplinaVinculada": "MPS",
            "cargaHoraria": 12
        }
        headers = {"X-Perfil": "COORDENADOR"}
        response = client.patch(f"/usuarios/{fake_id}/promover", json=payload, headers=headers)
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]

    def test_promover_erro_usuario_ja_monitor(self, client: TestClient):
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        payload = {
            "disciplinaVinculada": "MPS",
            "cargaHoraria": 12
        }
        headers = {"X-Perfil": "COORDENADOR"}

        # Primeira promoção
        res1 = client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)
        assert res1.status_code == 200

        # Segunda promoção
        res2 = client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)
        assert res2.status_code == 400
        assert "já é um monitor" in res2.json()["detail"]

    def test_promover_erro_usuario_docente(self, client: TestClient):
        docente = client.post("/usuarios", json=DOCENTE_PAYLOAD).json()
        docente_id = docente["id"]

        payload = {
            "disciplinaVinculada": "MPS",
            "cargaHoraria": 12
        }
        headers = {"X-Perfil": "COORDENADOR"}
        response = client.patch(f"/usuarios/{docente_id}/promover", json=payload, headers=headers)
        assert response.status_code == 400
        assert "Apenas discentes" in response.json()["detail"]

    def test_promover_erro_carga_horaria_negativa(self, client: TestClient):
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        payload = {
            "disciplinaVinculada": "MPS",
            "cargaHoraria": -5
        }
        headers = {"X-Perfil": "COORDENADOR"}
        response = client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)
        # Pydantic deve rejeitar cargaHoraria menor que 0 com 422
        assert response.status_code == 422

    def test_promover_erro_disciplina_vazia(self, client: TestClient):
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        # Disciplina vazia
        payload = {
            "disciplinaVinculada": "   ",
            "cargaHoraria": 12
        }
        headers = {"X-Perfil": "COORDENADOR"}
        response = client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)
        assert response.status_code == 400
        assert "Disciplina vinculada é obrigatória" in response.json()["detail"]

    def test_revogar_monitor_com_sucesso(self, client: TestClient):
        # 1. Criar e promover discente
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        payload = {
            "disciplinaVinculada": "MPS",
            "cargaHoraria": 12
        }
        headers = {"X-Perfil": "COORDENADOR"}
        res_promo = client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)
        assert res_promo.status_code == 200

        # 2. Revogar monitor
        res_revoke = client.patch(f"/usuarios/{aluno_id}/revogar", headers=headers)
        assert res_revoke.status_code == 200
        data = res_revoke.json()
        assert data["id"] == aluno_id
        assert data["perfil"] == "DISCENTE"
        assert "disciplinaVinculada" not in data

        # 3. Detalhar usuário para certificar que voltou a ser DISCENTE
        detail_res = client.get(f"/usuarios/{aluno_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["perfil"] == "DISCENTE"
        assert "disciplinaVinculada" not in detail_data

    def test_revogar_erro_sem_cabecalho_coordenador(self, client: TestClient):
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        # 1. Promover
        headers = {"X-Perfil": "COORDENADOR"}
        res_promo = client.patch(f"/usuarios/{aluno_id}/promover", json={"disciplinaVinculada": "MPS", "cargaHoraria": 12}, headers=headers)
        assert res_promo.status_code == 200

        # 2. Revogar sem cabeçalho
        response = client.patch(f"/usuarios/{aluno_id}/revogar")
        assert response.status_code == 403
        assert "apenas coordenadores" in response.json()["detail"]

    def test_revogar_erro_usuario_nao_monitor(self, client: TestClient):
        # Aluno comum
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        headers = {"X-Perfil": "COORDENADOR"}
        response = client.patch(f"/usuarios/{aluno_id}/revogar", headers=headers)
        assert response.status_code == 400
        assert "não é um monitor" in response.json()["detail"]

        # Docente
        docente = client.post("/usuarios", json=DOCENTE_PAYLOAD).json()
        docente_id = docente["id"]

        response = client.patch(f"/usuarios/{docente_id}/revogar", headers=headers)
        assert response.status_code == 400
        assert "não é um monitor" in response.json()["detail"]


# ===========================================================================
# VALIDAÇÃO E ERROS DE LOGIN (POST /usuarios/login)
# ===========================================================================

class TestLoginUsuario:
    def test_login_sucesso(self, client: TestClient):
        # Cadastra um discente válido
        _criar_discente(client, login="joaosilva")

        # Tenta realizar login
        payload = {
            "login": "joaosilva",
            "senha": "Password123!"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["login"] == "joaosilva"
        assert data["email"] == "joao.silva@discente.ufpb.br"
        assert "senha" not in data

    def test_login_limite_caracteres_valido(self, client: TestClient):
        # Login com exatamente 12 caracteres alfabéticos
        login_12_chars = "abcdefghijkl"
        _criar_discente(client, login=login_12_chars, email="outro@discente.ufpb.br")

        payload = {
            "login": login_12_chars,
            "senha": "Password123!"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 200
        assert response.json()["login"] == login_12_chars

    def test_login_erro_login_vazio(self, client: TestClient):
        payload = {
            "login": "",
            "senha": "Password123!"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "O login não pode ser vazio."

    def test_login_erro_login_espacos(self, client: TestClient):
        payload = {
            "login": "    ",
            "senha": "Password123!"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "O login não pode ser vazio."

    def test_login_erro_login_muito_longo(self, client: TestClient):
        # 13 caracteres alfabéticos
        payload = {
            "login": "abcdefghijklm",
            "senha": "Password123!"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "O login deve ter no máximo 12 caracteres."

    def test_login_erro_login_contem_numeros(self, client: TestClient):
        payload = {
            "login": "user123",
            "senha": "Password123!"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "O login não pode conter números."

    def test_login_erro_usuario_inexistente(self, client: TestClient):
        payload = {
            "login": "inexistente",
            "senha": "Password123!"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 401
        assert response.json()["detail"] == "Login ou senha incorretos."

    def test_login_erro_senha_incorreta(self, client: TestClient):
        _criar_discente(client, login="joaosilva")
        payload = {
            "login": "joaosilva",
            "senha": "SenhaIncorreta"
        }
        response = client.post("/usuarios/login", json=payload)
        assert response.status_code == 401
        assert response.json()["detail"] == "Login ou senha incorretos."

    def test_cadastro_erro_login_invalido(self, client: TestClient):
        # Valida que as regras de login também barram o cadastro de usuários inválidos
        payload = {**DISCENTE_PAYLOAD, "login": "logincom123"}
        response = client.post("/usuarios", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "O login não pode conter números."


# ===========================================================================
# PERSISTÊNCIA EM BANCO DE DADOS SQLITE
# ===========================================================================

class TestPersistenciaUsuario:
    def test_salvar_persiste_no_repositorio(self):
        """Após adicionar um usuário, o repositório deve retorná-lo em find_all."""
        repo = app.state.usuario_service._repo

        usuario = Discente(
            id=uuid4(),
            nome="Test Persistência",
            login="testpersist",
            email="test@discente.ufpb.br",
            senha="Password123!",
            perfil=TipoPerfil.DISCENTE,
            ativo=True,
            matricula="2023000999",
            curso="CC"
        )
        repo.add(usuario)

        assert len(repo.find_all()) == 1

    def test_recuperar_dados_apos_adicao(self):
        """
        Dados inseridos devem ser recuperados pelo mesmo repositório.
        """
        repo = app.state.usuario_service._repo

        usuario = Discente(
            id=uuid4(),
            nome="Test Persistência 2",
            login="testpersisttwo",
            email="test2@discente.ufpb.br",
            senha="Password123!",
            perfil=TipoPerfil.DISCENTE,
            ativo=True,
            matricula="2023000998",
            curso="CC"
        )
        repo.add(usuario)

        usuarios_carregados = repo.find_all()

        assert len(usuarios_carregados) == 1
        assert usuarios_carregados[0].nome == "Test Persistência 2"
        assert usuarios_carregados[0].login == "testpersisttwo"
        assert usuarios_carregados[0].email == "test2@discente.ufpb.br"

    def test_update_reflete_na_recuperacao(self):
        """Após update, o repositório deve refletir a alteração na próxima leitura."""
        repo = app.state.usuario_service._repo

        usuario = Discente(
            id=uuid4(),
            nome="Test Persistência 3",
            login="testpersistthree",
            email="test3@discente.ufpb.br",
            senha="Password123!",
            perfil=TipoPerfil.DISCENTE,
            ativo=True,
            matricula="2023000997",
            curso="CC"
        )
        repo.add(usuario)

        # Atualiza o nome do usuário via objeto mutável
        usuario_atualizado = usuario.model_copy(update={"nome": "Test Persistência Alterado"})
        repo.update(usuario_atualizado)

        usuarios_carregados = repo.find_all()
        assert len(usuarios_carregados) == 1
        assert usuarios_carregados[0].nome == "Test Persistência Alterado"

    def test_find_by_id_retorna_monitor_corretamente(self, client: TestClient):
        """
        Garante que Monitor é recuperado corretamente do repositório
        com todos os seus atributos específicos.
        """
        from uuid import UUID
        aluno = _criar_discente(client)
        aluno_id = aluno["id"]

        headers = {"X-Perfil": "COORDENADOR"}
        payload = {"disciplinaVinculada": "MPS", "cargaHoraria": 8}
        client.patch(f"/usuarios/{aluno_id}/promover", json=payload, headers=headers)

        # Busca direto no repositório via app.state
        repo = app.state.usuario_service._repo
        monitor = repo.find_by_id(UUID(aluno_id))

        assert monitor is not None
        assert monitor.perfil == TipoPerfil.MONITOR
        assert monitor.disciplinaVinculada == "MPS"
        assert monitor.cargaHoraria == 8
        assert monitor.disponivel is True
