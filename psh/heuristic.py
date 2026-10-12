"""Appendix C implemented literally and with documented corrections."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize, linprog


@dataclass
class Problem:
    mu: np.ndarray
    cov: np.ndarray
    ub: np.ndarray
    target: float

    def __post_init__(self):
        self.mu, self.cov, self.ub = map(lambda x: np.asarray(x, dtype=float),
                                        (self.mu, self.cov, self.ub))
        n = len(self.mu)
        if n < 2 or self.cov.shape != (n, n) or self.ub.shape != (n,):
            raise ValueError('Incompatible problem dimensions')
        if not all(np.isfinite(v).all() for v in (self.mu, self.cov, self.ub)) or not np.isfinite(self.target):
            raise ValueError('Non-finite problem')
        if np.any(self.ub <= 0) or np.any(self.ub > 1) or self.ub.sum() < 1-1e-10:
            raise ValueError('Invalid bounds or insufficient total allocation capacity')
        if not np.allclose(self.cov, self.cov.T) or np.linalg.eigvalsh(self.cov).min() < -1e-9:
            raise ValueError('Covariance must be symmetric positive semidefinite')


def paper_bounds(n):
    return np.full(n, min(1., max(0.1, 3/n)))


def metrics(w, p, tolerance=1e-6):
    w = np.asarray(w, dtype=float)
    ret, var = float(w @ p.mu), float(w @ p.cov @ w)
    violations = {'sum': float(abs(w.sum()-1)), 'lower': float(max(0, -w.min())),
                  'upper': float(max(0, (w-p.ub).max())),
                  'return': float(max(0, p.target-ret))}
    return {'expected_return': ret, 'variance': var, 'volatility': float(np.sqrt(max(0,var))),
            'feasible': bool(all(v <= tolerance for v in violations.values())),
            'violations': violations}


def heuristic(p, delta=0.025, mode='corrected'):
    """n starts, fixed increments, min variance / max return fallback.

    literal: preserves line 50 multiplication and finite +/-1000 sentinels.
    corrected: divides by sum, excludes blocked candidates and checks final feasibility.
    Neither mode silently repairs failed portfolios. Final normalization can violate bounds.
    """
    if mode not in ('literal','corrected') or not 0 < delta <= 1:
        raise ValueError('Invalid mode or delta')
    candidates = []
    for start in range(len(p.mu)):
        if mode == 'corrected' and delta > p.ub[start]+1e-12:
            continue
        x = np.zeros(len(p.mu)); x[start] = delta
        trace = []; stopped = False
        for step in range(int(np.ceil(1/delta))+2):
            # Visual inspection confirms 1 - delta/2 (text extraction mangles fraction).
            if x.sum() >= 1-delta/2:
                break
            big = 1000. if mode == 'literal' else np.inf
            small = -1000. if mode == 'literal' else -np.inf
            variances = np.full(len(x), big); rets = np.full(len(x), small)
            for j in range(len(x)):
                y = x.copy(); y[j] += delta
                if y[j] <= p.ub[j]+1e-12:
                    rets[j] = y @ p.mu / y.sum()
                    if rets[j] >= p.target:
                        variances[j] = y @ p.cov @ y
            if mode == 'corrected' and not np.isfinite(rets).any():
                stopped = True; break
            fallback = variances.min() == big
            j = int(np.argmax(rets) if fallback else np.argmin(variances))
            x[j] += delta
            trace.append({'step':step+1, 'asset_index':j, 'sum':float(x.sum()),
                          'decision':'max_return_fallback' if fallback else 'min_variance'})
        w = x*x.sum() if mode == 'literal' else x/x.sum()
        result = metrics(w, p)
        candidates.append({'start':start, 'weights':w.tolist(), **result,
                           'capacity_exhausted':stopped, 'trace':trace})
    feasible = [c for c in candidates if c['feasible']]
    best = min(feasible, key=lambda c:c['variance']) if feasible else None
    return {'best':best, 'candidates':candidates, 'mode':mode,
            'feasible_fraction':len(feasible)/max(1,len(candidates))}


def continuous_solver(p, initial=None):
    """SLSQP reference for continuous MinVola, not a discrete optimality certificate."""
    feasible = linprog(np.zeros(len(p.mu)), A_ub=[-p.mu], b_ub=[-p.target],
                       A_eq=[np.ones(len(p.mu))], b_eq=[1], bounds=list(zip(np.zeros(len(p.mu)),p.ub)),
                       method='highs')
    if not feasible.success:
        return {'weights':None, 'feasible':False, 'message':'Target infeasible under bounds'}
    x0 = feasible.x if initial is None else np.asarray(initial)
    result = minimize(lambda w:float(w@p.cov@w), x0, jac=lambda w:2*p.cov@w,
                      bounds=list(zip(np.zeros(len(p.mu)),p.ub)),
                      constraints=[{'type':'eq','fun':lambda w:w.sum()-1,
                                    'jac':lambda w:np.ones(len(w))},
                                   {'type':'ineq','fun':lambda w:w@p.mu-p.target,
                                    'jac':lambda w:p.mu}], method='SLSQP',
                      options={'maxiter':1000,'ftol':1e-12})
    m = metrics(result.x,p)
    return {'weights':result.x.tolist(), **m, 'solver_success':bool(result.success),
            'message':str(result.message)}
