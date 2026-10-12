import io
import os
import secrets
from uuid import uuid4
from contextlib import asynccontextmanager
import pandas as pd
from fastapi import FastAPI,UploadFile,File,Form,HTTPException,Depends,Header
from pydantic import BaseModel,Field
from sqlalchemy import select,text
from .data import read_csv,synthetic,fingerprint
from .database import init_db,SessionLocal,Dataset,Observation,Run,Allocation
from .experiment import run_experiment


def authorize(x_api_key: str|None=Header(default=None)):
    key=os.getenv('API_KEY','')
    if key and not secrets.compare_digest(x_api_key or '',key):
        raise HTTPException(401,'Invalid API key')


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app=FastAPI(title='Problem-specific Heuristic Lab',version='0.1.0',lifespan=lifespan)


class ExperimentRequest(BaseModel):
    dataset_id: str
    target: float|None=Field(default=None,ge=-1,le=10)
    delta: float|None=Field(default=None,ge=.005,le=1)
    d: int=Field(default=1,ge=1,le=3)
    max_weight: float|None=Field(default=None,gt=0,le=1)
    seed: int=Field(default=42,ge=0,le=2**32-1)
    include_quantum: bool=False
    reads: int=Field(default=100,ge=1,le=1000)
    sweeps: int=Field(default=100,ge=1,le=1000)


def persist_dataset(frame,name,source):
    dataset_id=str(uuid4())
    with SessionLocal() as db:
        db.add(Dataset(id=dataset_id,name=name[:200],sha256=fingerprint(frame),source=source,assets=list(frame.columns)))
        db.flush()
        db.add_all([Observation(dataset_id=dataset_id,date=date.date(),asset=asset,value=float(value))
                    for date,row in frame.iterrows() for asset,value in row.items()])
        db.commit()
    return {'id':dataset_id,'name':name,'rows':len(frame),'assets':list(frame.columns),'sha256':fingerprint(frame)}


@app.get('/health')
def health():
    with SessionLocal() as db: db.execute(text('SELECT 1'))
    return {'status':'ok'}


@app.post('/datasets/demo',dependencies=[Depends(authorize)])
def demo(): return persist_dataset(synthetic(n=6), 'Synthetic correlated demo', 'synthetic seed=42; not real market data')


@app.post('/datasets',dependencies=[Depends(authorize)])
async def upload(file:UploadFile=File(...),kind:str=Form('returns')):
    content=await file.read(5*1024*1024+1)
    if len(content)>5*1024*1024: raise HTTPException(413,'CSV limit: 5 MB')
    try: frame=read_csv(io.BytesIO(content),kind)
    except (ValueError,TypeError) as e: raise HTTPException(422,str(e)) from e
    if len(frame.columns)>12 or len(frame)>3000:
        raise HTTPException(422,'Interactive API limit: 12 assets and 3000 dates; use notebook for larger experiments')
    return persist_dataset(frame,file.filename or 'uploaded.csv','user CSV '+kind)


@app.get('/datasets',dependencies=[Depends(authorize)])
def datasets():
    with SessionLocal() as db:
        return [{'id':r.id,'name':r.name,'assets':r.assets,'sha256':r.sha256}
                for r in db.scalars(select(Dataset).order_by(Dataset.created_at.desc()).limit(100))]


@app.post('/experiments',dependencies=[Depends(authorize)])
def experiment(request:ExperimentRequest):
    with SessionLocal() as db:
        ds=db.get(Dataset,request.dataset_id)
        if ds is None: raise HTTPException(404,'Dataset not found')
        obs=list(db.scalars(select(Observation).where(Observation.dataset_id==ds.id)))
        frame=pd.DataFrame([{'date':o.date,'asset':o.asset,'value':o.value} for o in obs])
        frame=frame.pivot(index='date',columns='asset',values='value').reindex(columns=ds.assets)
        frame.index=pd.to_datetime(frame.index)
    if request.include_quantum and len(frame.columns)*(request.d+1)>14:
        raise HTTPException(422,'QAOA simulator allows at most 14 qubits: assets*(d+1)')
    try:
        report=run_experiment(frame,**request.model_dump(exclude={'dataset_id'}))
    except ValueError as e: raise HTTPException(422,str(e)) from e
    run_id=str(uuid4())
    with SessionLocal() as db:
        db.add(Run(id=run_id,dataset_id=request.dataset_id,report=report)); db.flush()
        for row in report['results']:
            if row.get('weights') is not None:
                db.add_all([Allocation(run_id=run_id,method=row['method'],asset=asset,weight=weight)
                            for asset,weight in zip(report['assets'],row['weights'])])
        db.commit()
    return {'id':run_id,**report}


@app.get('/experiments',dependencies=[Depends(authorize)])
def runs():
    with SessionLocal() as db:
        return [{'id':r.id,'dataset_id':r.dataset_id,'created_at':r.created_at.isoformat()}
                for r in db.scalars(select(Run).order_by(Run.created_at.desc()).limit(100))]


@app.get('/experiments/{run_id}',dependencies=[Depends(authorize)])
def run(run_id:str):
    with SessionLocal() as db:
        result=db.get(Run,run_id)
        if result is None: raise HTTPException(404,'Run not found')
        return {'id':result.id,**result.report}
