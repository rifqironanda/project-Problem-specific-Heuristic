import os
import pytest
os.environ['DATABASE_URL']='sqlite://'
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
import psh.database as database
database.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
database.SessionLocal.configure(bind=database.engine)
from fastapi.testclient import TestClient
from psh.api import app

@pytest.fixture
def client():
    database.Base.metadata.drop_all(database.engine)
    with TestClient(app) as c: yield c

def test_complete_rest_pipeline(client):
    assert client.get('/health').status_code==200
    ds=client.post('/datasets/demo').json()
    assert len(client.get('/datasets').json())==1
    response=client.post('/experiments',json={'dataset_id':ds['id'],'reads':5,'sweeps':10})
    assert response.status_code==200,response.text
    report=response.json()
    assert any(r['method']=='ai_surrogate' and r.get('weights') for r in report['results'])
    assert report['periods']['validation'][1]<report['periods']['test'][0]
    assert client.get('/experiments/'+report['id']).json()['dataset_sha256']==report['dataset_sha256']
    assert len(client.get('/experiments').json())==1

def test_auth_and_validation(client,monkeypatch):
    monkeypatch.setenv('API_KEY','test_key')
    assert client.post('/datasets/demo').status_code==401
    headers={'X-API-Key':'test_key'}
    assert client.post('/datasets',files={'file':('bad.csv',b'date,A,B\n2020-01-01,1,2')},headers=headers).status_code==422
    ds=client.post('/datasets/demo',headers=headers).json()
    assert client.post('/experiments',json={'dataset_id':ds['id'],'d':3,'include_quantum':True},headers=headers).status_code==422
    assert client.get('/experiments/missing',headers=headers).status_code==404
