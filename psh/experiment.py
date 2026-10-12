import platform
import time
import importlib.metadata
import numpy as np
from .data import chronological_split, statistics, fingerprint
from .heuristic import Problem,paper_bounds,heuristic,continuous_solver,metrics
from .qubo import build_qubo,sample_qubo,postprocess,qaoa_statevector,exact_grid
from .ai import fit_surrogate,predict,complement


def heldout(w,test):
    # Static target weights, daily rebalance, zero costs: explicit educational convention.
    daily=test.to_numpy()@np.asarray(w)
    wealth=np.cumprod(1+daily); peak=np.maximum.accumulate(np.r_[1.,wealth])[1:]
    return {'realized_annual_return':float(np.expm1(np.log1p(daily).mean()*252)),
            'realized_annual_volatility':float(np.std(daily,ddof=0)*np.sqrt(252)),
            'max_drawdown':float(np.min(wealth/peak-1)),
            'cumulative_return':float(wealth[-1]-1),
            'evaluation':'held-out static weights; daily rebalance; zero transaction costs'}


def run_experiment(frame,target=None,delta=None,d=1,seed=42,include_quantum=False,
                   reads=200,sweeps=100,max_weight=None):
    train,val,test=chronological_split(frame)
    history=frame.iloc[:len(train)+len(val)]
    mu,cov=statistics(history)
    ub=paper_bounds(len(mu)) if max_weight is None else np.full(len(mu),max_weight)
    epsilon=float(np.quantile(mu,.7)) if target is None else float(target)
    delta=float(ub[0]/2**d) if delta is None else float(delta)
    p=Problem(mu,cov,ub,epsilon)
    rows=[]; h=None; t=time.perf_counter()
    def record(name,result,seconds,extra=None):
        row={'method':name,'runtime_seconds':seconds,**result}
        if extra: row.update(extra)
        if row.get('weights') is not None and row.get('feasible'):
            row['heldout']=heldout(row['weights'],test)
        rows.append(row)
    t0=time.perf_counter(); h=heuristic(p,delta)
    record('problem_specific_heuristic', h['best'] or {'weights':None,'feasible':False},time.perf_counter()-t0,
           {'candidate_feasible_fraction':h['feasible_fraction'],'candidates':len(h['candidates'])})
    t0=time.perf_counter(); ref=continuous_solver(p)
    record('continuous_slsqp',ref,time.perf_counter()-t0)
    uniform=np.ones(len(mu))/len(mu)
    record('equal_weight',{'weights':uniform.tolist(),**metrics(uniform,p)},0.)
    try:
        t0=time.perf_counter(); model,meta=fit_surrogate(train,val,ub,seed)
        train_seconds=time.perf_counter()-t0
        t0=time.perf_counter(); ai=predict(model,p)
        record('ai_surrogate',ai,time.perf_counter()-t0,{'training_seconds':train_seconds,'model':meta})
        t0=time.perf_counter(); hybrid=complement(model,p,h)
        record('ai_complement_heuristic',hybrid,time.perf_counter()-t0,{'training_seconds':train_seconds})
    except ValueError as e:
        record('ai_surrogate',{'weights':None,'feasible':False,'message':str(e)},0.)
    Q,B,offset=build_qubo(p,d)
    for method in ('random','sa','steepest','tabu'):
        t0=time.perf_counter(); samples,meta=sample_qubo(Q,method,reads,sweeps,seed)
        result=postprocess(samples,Q,B,p)
        record('qubo_'+method,result['best'] or {'weights':None,'feasible':False},time.perf_counter()-t0,
               {'samples':reads,'candidate_feasible_fraction':result['feasible_fraction']})
    if B.shape[1]<=16:
        t0=time.perf_counter(); grid=exact_grid(p,B)
        record('exact_discrete_grid',grid,time.perf_counter()-t0)
    if include_quantum:
        t0=time.perf_counter(); samples,meta=qaoa_statevector(Q,seed=seed)
        result=postprocess(samples,Q,B,p)
        record('qaoa_classical_simulator',result['best'] or {'weights':None,'feasible':False},time.perf_counter()-t0,
               {'sampler':meta,'candidate_feasible_fraction':result['feasible_fraction']})
    # Continuous reference ratio differs from paper's discrete approximation ratio.
    if ref.get('solver_success') and ref.get('feasible') and ref['variance']>1e-12:
        for row in rows:
            if row.get('feasible'):
                row['variance_ratio_to_continuous_reference']=row['variance']/ref['variance']
    return {'assets':list(frame.columns),'target_annual_return':epsilon,'delta':delta,
            'upper_bounds':ub.tolist(),'seed':seed,'d':d,'dataset_sha256':fingerprint(frame),
            'periods':{'train':[str(train.index[0].date()),str(train.index[-1].date())],
                       'validation':[str(val.index[0].date()),str(val.index[-1].date())],
                       'test':[str(test.index[0].date()),str(test.index[-1].date())]},
            'runtime_seconds':time.perf_counter()-t,'results':rows,
            'versions':{pkg:importlib.metadata.version(pkg) for pkg in ['numpy','pandas','scipy','scikit-learn']},
            'python':platform.python_version(),
            'scope':'Small-scale principle replication; no hardware quantum advantage claim',
            'timing_note':'Method-specific budgets differ; training included separately; not paper fixed-time benchmark',
            'qubo':{'bits':len(Q),'penalty':1000,'return_target_shift':.01,'offset':offset}}
