"""Supervised allocation surrogate, trained on continuous-solver labels.

AI comparator may be infeasible. Hybrid retains the paper heuristic and adds
an AI warm-started continuous candidate. Both are additions, not paper methods.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from .data import statistics
from .heuristic import Problem, continuous_solver, metrics


def features(p):
    i=np.triu_indices(len(p.mu))
    return np.r_[p.mu,p.cov[i],p.ub,p.target]


def capped_simplex(v, ub):
    """Euclidean projection to nonnegative weights summing to one under caps."""
    v=np.asarray(v,dtype=float); ub=np.asarray(ub,dtype=float)
    lo=float(np.min(v-ub))-1; hi=float(np.max(v))+1
    for _ in range(100):
        mid=(lo+hi)/2
        if np.clip(v-mid,0,ub).sum()>1: lo=mid
        else: hi=mid
    return np.clip(v-(lo+hi)/2,0,ub)


def training_pairs(frame,ub,window=60,stride=15):
    X=[]; Y=[]; dates=[]
    # Each label and feature uses only its own historical window. No future-return labels.
    for end in range(window,len(frame)+1,stride):
        mu,cov=statistics(frame.iloc[end-window:end])
        for q in (0.3,0.5,0.7):
            p=Problem(mu,cov,ub,float(np.quantile(mu,q)))
            label=continuous_solver(p)
            if label.get('solver_success') and label['feasible']:
                X.append(features(p)); Y.append(label['weights']); dates.append(str(frame.index[end-1].date()))
    return np.asarray(X),np.asarray(Y),dates


def fit_surrogate(train,val,ub,seed=42):
    X,Y,dates=training_pairs(train,ub)
    XV,YV,val_dates=training_pairs(val,ub)
    if len(X)<6 or len(XV)<3:
        raise ValueError('AI needs >=6 train and >=3 validation labels; use longer data or looser caps')
    best=None; trials=[]
    for depth in (4,8):
        model=RandomForestRegressor(n_estimators=80,max_depth=depth,min_samples_leaf=2,
                                    random_state=seed,n_jobs=1)
        model.fit(X,Y)
        prediction=np.array([capped_simplex(v,ub) for v in model.predict(XV)])
        error=float(mean_absolute_error(YV,prediction))
        trials.append({'max_depth':depth,'validation_weight_mae':error})
        if best is None or error<best[0]: best=(error,model)
    return best[1],{'training_labels':len(X),'validation_labels':len(XV),
                   'validation_weight_mae':best[0],'trials':trials,
                   'train_last_label_date':dates[-1],'validation_last_label_date':val_dates[-1],
                   'teacher':'continuous SLSQP; solver success and feasible labels only',
                   'meaning':'MAE measures imitation of teacher, not future profitability'}


def predict(model,p):
    w=capped_simplex(model.predict(features(p).reshape(1,-1))[0],p.ub)
    return {'weights':w.tolist(),**metrics(w,p)}


def complement(model,p,heuristic_result):
    ai=predict(model,p)
    refined=continuous_solver(p,initial=ai['weights'])
    pool=[]
    if heuristic_result['best']: pool.append(('heuristic',heuristic_result['best']))
    if refined.get('solver_success') and refined['feasible']: pool.append(('ai_warmstart_slsqp',refined))
    if not pool: return {'weights':None,'feasible':False,'message':'No feasible hybrid candidate'}
    source,best=min(pool,key=lambda item:item[1]['variance'])
    return {**best,'selected_source':source,
            'note':'Hybrid includes continuous solver; improvement cannot be attributed to AI alone'}
