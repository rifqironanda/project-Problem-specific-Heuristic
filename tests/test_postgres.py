import os
import pytest
from sqlalchemy import create_engine,select,text
from sqlalchemy.orm import Session
from psh.database import Base,Dataset,Observation,Run,Allocation

@pytest.mark.skipif(not os.getenv('TEST_POSTGRES_URL'),reason='Set TEST_POSTGRES_URL to isolated PostgreSQL test database')
def test_postgres_structured_roundtrip():
    from datetime import date
    from uuid import uuid4
    engine=create_engine(os.environ['TEST_POSTGRES_URL'])
    Base.metadata.create_all(engine)
    dsid,runid=str(uuid4()),str(uuid4())
    try:
        with Session(engine) as db:
            db.add(Dataset(id=dsid,name='test',sha256='0'*64,source='test',assets=['A','B'])); db.flush()
            db.add(Observation(dataset_id=dsid,date=date(2020,1,1),asset='A',value=.01))
            db.add(Run(id=runid,dataset_id=dsid,report={'results':[{'method':'test','feasible':True}]})); db.flush()
            db.add(Allocation(run_id=runid,method='test',asset='A',weight=1.)); db.commit()
            assert db.get(Run,runid).report['results'][0]['feasible'] is True
            assert db.execute(text('SELECT AVG(value) FROM daily_returns WHERE dataset_id=:id'),{'id':dsid}).scalar()==pytest.approx(.01)
    finally:
        with Session(engine) as db:
            db.query(Allocation).filter_by(run_id=runid).delete()
            db.query(Run).filter_by(id=runid).delete()
            db.query(Observation).filter_by(dataset_id=dsid).delete()
            db.query(Dataset).filter_by(id=dsid).delete(); db.commit()
        engine.dispose()
