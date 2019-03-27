import pytest

from apiserver.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def payload():
    return {
        'memberKey': 'key1',
        'gender': 'F',
        'age': 58,
        'disabledFlag': True,
        'lineOfBusiness': 'Medicaid',
        'modelConditions': [{
                'name': 'CDPS',
                'version': '6.2',
                'state': 'KY',
                'type': 'Prospective',
                'input': 'Dx',
                'year': '2018',
                'conditions': [
                    {
                        'code': 'Z99.81',
                        'type': 'Dx',
                        'version': '10',
                        'status': 'Open'
                    }, 
                    {
                        'code': 'K21.9',
                        'type': 'Dx',
                        'version': '10',
                        'status': 'Confirmed-Claim'
                    }, 
                    {
                        'code': 'G62.9',
                        'type': 'Dx',
                        'version': '10',
                        'status': 'Confirmed-Claim'
                    }
                ]
            }
        ],
        'customScoreComponents': {
            'interceptFlag': True,
            'demographicsFlag': True
        }
    }


def test_score(client, payload):
    resp = client.post('/score', json=payload)

    assert resp.status_code == 200
    assert resp.json['memberKey'] == 'key1'
    assert 'customScores' in resp.json
    assert 'standardScores' in resp.json


def test_score_with_validation_invalid_payload(client):
    resp = client.post('/score_with_validation', json={})

    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_PARAMETER'
    assert 'gender' in resp.json['message']


def test_score_handle_engine_error(client):
    resp = client.post('/score_handle_engine_error')

    assert resp.status_code == 500
    assert resp.json['code'] == 'INTERNAL_ERROR'
