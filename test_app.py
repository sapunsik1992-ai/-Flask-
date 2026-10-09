import pytest

from server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_create_ad(client):
    response = client.post('/ads', json={'title': 'Квартира', 'owner': 'Иван'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == 'Квартира'
    assert data['owner'] == 'Иван'
    assert data['description'] == ''
    assert 'id' in data


def test_invalid_create_ad_returns_400(client):
    response = client.post('/ads', json={'title': '', 'owner': ''})
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_get_all_ads(client):
    response = client.get('/ads')
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
