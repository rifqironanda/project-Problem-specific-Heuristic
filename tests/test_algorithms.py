import numpy as np
import pandas as pd
import pytest
from psh.data import statistics,synthetic,chronological_split,read_csv
from psh.heuristic import Problem,heuristic,continuous_solver,metrics
from psh.qubo import build_qubo,bitstrings,exact_grid,sample_qubo,qaoa_statevector
from psh.ai import capped_simplex,fit_surrogate

def problem():
    return Problem(np.array([.05,.1,.2]),np.diag([.01,.02,.04]),np.ones(3),.08)

def test_paper_statistics():
    f=synthetic(n=3,days=100)
    mu,cov=statistics(f)
    np.testing.assert_allclose(mu,(1+f).prod().to_numpy()**(252/len(f))-1)
    centered=f.to_numpy()-f.to_numpy().mean(0)
    np.testing.assert_allclose(cov,252*centered.T@centered/len(f))

def test_solver_respects_constraints():
    p=problem(); r=continuous_solver(p)
    assert r['solver_success'] and r['feasible']
    assert r['variance']<=np.ones(3)/3@p.cov@(np.ones(3)/3)+1e-8

def test_infeasible_target():
    p=problem(); p.target=.9
    assert not continuous_solver(p)['feasible']
    assert heuristic(p,.1)['best'] is None

def test_literal_normalization_bug_visible():
    p=problem(); p.target=0
    corrected=heuristic(p,.3,'corrected'); literal=heuristic(p,.3,'literal')
    assert corrected['best'] is not None
    assert all(abs(sum(c['weights'])-1)<1e-10 for c in corrected['candidates'])
    assert all(abs(sum(c['weights'])-.81)<1e-10 for c in literal['candidates'])
    assert literal['best'] is None

def test_normalized_cap_violation_not_hidden():
    p=Problem([.1,.2],np.eye(2),[.6,.4],.05)
    result=heuristic(p,.3)
    assert result['best'] is None
    assert any(c['violations']['upper']>0 for c in result['candidates'])

def test_qubo_equals_paper_objective_for_all_bits():
    p=problem(); Q,B,offset=build_qubo(p,d=1)
    for b in bitstrings(len(Q)):
        w=B@b
        expected=w@p.cov@w+1000*(w@p.mu-p.target-.01)**2+1000*(w.sum()-1)**2
        assert b@Q@b+offset==pytest.approx(expected,abs=1e-9)

def test_grid_optimum_and_stochastic_repeatability():
    p=problem(); Q,B,_=build_qubo(p)
    grid=exact_grid(p,B)
    assert grid['feasible']
    for method in ['random','sa','steepest','tabu']:
        a,_=sample_qubo(Q,method,reads=8,sweeps=15,seed=2)
        b,_=sample_qubo(Q,method,reads=8,sweeps=15,seed=2)
        np.testing.assert_array_equal(a,b)

def test_qaoa_probability_samples_and_limit():
    a,meta=qaoa_statevector(np.diag([1.,2.]),shots=20,maxiter=10)
    assert a.shape==(20,2) and set(np.unique(a))<={0,1}
    assert meta['method']=='qaoa_classical_simulator'
    with pytest.raises(ValueError): qaoa_statevector(np.eye(15))

def test_chronology_and_ai_projection():
    train,val,test=chronological_split(synthetic(n=3))
    assert train.index.max()<val.index.min()<test.index.min()
    model,meta=fit_surrogate(train,val,np.full(3,.6))
    assert meta['train_last_label_date']<meta['validation_last_label_date']<str(test.index.min().date())
    w=capped_simplex([5,-3,1],[.6,.6,.6])
    assert sum(w)==pytest.approx(1) and (w>=0).all() and (w<=.6).all()

def test_return_csv_rejects_missing_data():
    import io
    f=synthetic(n=3,days=100); f.iloc[5,1]=np.nan
    with pytest.raises(ValueError): read_csv(io.StringIO(f.to_csv(index_label='date')))

def test_french_first_block_only():
    import io,zipfile
    from scripts.download_data import french
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        z.writestr('daily.csv','Source\nValue weighted\n, A, B\n20200101,1.0,2.0\n20200102,-99.99,3.0\n\nEqual weighted\n,A,B\n20200101,99,99\n')
    f=french(buf.getvalue())
    assert f.shape==(2,2) and f.iloc[0,0]==.01 and np.isnan(f.iloc[1,0])
