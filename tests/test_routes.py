import pytest
import requests
from unittest.mock import patch, Mock, MagicMock
from app import create_app
from app.routes import allowed_file


@pytest.fixture
def client():
    with patch("app.routes.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value.data = []

        app = create_app()
        app.config["TESTING"] = True

        with app.test_client() as client:
            yield client

def test_search_sem_parametro(client):
    response = client.get("/books/search")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_search_openlibrary_sucesso(client):
    mock_response = {
        "docs": [{
            "title": "Dom Casmurro",
            "author_name": ["Machado de Assis"],
            "first_publish_year": 1899,
            "cover_i": 12345
        }]
    }

    with patch("app.routes.http_requests.get") as mock_get:
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = mock_response

        response = client.get("/books/search?q=Dom+Casmurro")

        assert response.status_code == 200

        data = response.get_json()

        assert data[0]["title"] == "Dom Casmurro"
        assert data[0]["author"] == "Machado de Assis"
        assert data[0]["year"] == "1899"


def test_search_openlibrary_nao_encontrado(client):
    with patch("app.routes.http_requests.get") as mock_get:
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {"docs": []}

        response = client.get("/books/search?q=livroinexistente")

        assert response.status_code == 404


def test_get_books(client):
    mock_result = MagicMock()
    mock_result.data = []

    with patch("app.routes.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_result

        response = client.get("/books")

        assert response.status_code == 200
        assert response.get_json() == []


def test_add_book_sem_titulo(client):
    response = client.post("/books", data={
        "title": "",
        "author": "Autor"
    })

    assert response.status_code == 400
    assert "error" in response.get_json()

def test_import_books_sem_arquivo(client):
    response = client.post("/books/import")

    assert response.status_code == 400
    assert "error" in response.get_json()

    import requests

def test_search_openlibrary_erro_conexao(client):
    with patch("app.routes.http_requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException(
            "Erro de conexão"
        )

        response = client.get("/books/search?q=teste")

        assert response.status_code == 502
        assert "error" in response.get_json()

        from app.routes import allowed_file

def test_allowed_file():
    assert allowed_file("capa.jpg") is True
    assert allowed_file("livro.png") is True
    assert allowed_file("arquivo.pdf") is False
