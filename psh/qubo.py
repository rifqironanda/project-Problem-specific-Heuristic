"""Paper equations (3),(4); all samplers use exactly the same QUBO."""
import time
import numpy as np
from scipy.optimize import minimize
from .heuristic import metrics


def build_qubo(p, d=1, penalty=1000., shift=0.01):
    if not 1 <= d <= 8 or penalty <= 0:
        raise ValueError('d must be 1..8 and penalty positive')
    n = len(p.mu)
    coefficients = np.array([2.**(-j) for j in range(1,d+1)]+[2.**(-d)])
    B = np.zeros((n,n*(d+1)))
    for i in range(n): B[i,i*(d+1):(i+1)*(d+1)] = p.ub[i]*coefficients
    a = B.T@p.mu; s = B.sum(axis=0); target = p.target+shift
    Q = B.T@p.cov@B + penalty*np.outer(a,a)+penalty*np.outer(s,s)
    Q[np.diag_indices_from(Q)] += -2*penalty*target*a - 2*penalty*s
    offset = penalty*(target**2+1)
    return Q,B,float(offset)


def sample_qubo(Q, method='sa', reads=200, sweeps=100, seed=42):
    """Educational implementations: random, SA, steepest and tabu bit-flip search."""
    if method not in ('random','sa','steepest','tabu'): raise ValueError('Unknown sampler')
    rng = np.random.default_rng(seed); samples=[]; start=time.perf_counter()
    scale=max(float(np.abs(Q).max()),1e-9)
    for _ in range(reads):
        x=rng.integers(0,2,len(Q)); energy=float(x@Q@x)
        best=x.copy(); best_e=energy; tabu={}
        if method != 'random':
            for step in range(sweeps):
                sign=1-2*x
                diff=sign*(2*Q@x)+np.diag(Q)
                if method == 'sa':
                    j=int(rng.integers(len(x)))
                    temp=scale*(1e-4**(step/max(1,sweeps-1)))
                    accept=diff[j]<=0 or rng.random()<np.exp(-max(0,diff[j])/temp)
                else:
                    allowed=np.ones(len(x),dtype=bool)
                    if method=='tabu':
                        allowed=np.array([tabu.get(j,-1)<=step or energy+diff[j]<best_e for j in range(len(x))])
                    if not allowed.any(): break
                    j=int(np.argmin(np.where(allowed,diff,np.inf)))
                    accept=method=='tabu' or diff[j]<-1e-12
                if not accept:
                    if method=='steepest': break
                    continue
                x[j]=1-x[j]; energy=float(x@Q@x)
                tabu[j]=step+max(2,len(x)//3)
                if energy<best_e: best=x.copy(); best_e=energy
        samples.append(best)
    return np.asarray(samples), {'runtime_seconds':time.perf_counter()-start,
                                 'samples':reads, 'method':method, 'seed':seed}


def bitstrings(bits):
    return ((np.arange(2**bits)[:,None] >> np.arange(bits)) & 1).astype(np.int8)


def exact_grid(p, B, max_bits=16):
    """Proven discrete optimum by enumeration of ORIGINAL constraints, not penalty energy."""
    if B.shape[1]>max_bits: raise ValueError('Enumeration limited to 16 bits')
    W=bitstrings(B.shape[1])@B.T
    mask=(np.abs(W.sum(axis=1)-1)<=1e-8)&(W@p.mu>=p.target-1e-8)
    if not mask.any(): return {'weights':None,'feasible':False,'message':'No feasible grid point'}
    valid=W[mask]; variance=np.einsum('bi,ij,bj->b',valid,p.cov,valid)
    w=valid[int(variance.argmin())]
    return {'weights':w.tolist(),**metrics(w,p),'message':'Exhaustive grid optimum'}


def postprocess(samples,Q,B,p,top=100):
    # Same top-100 penalty sorting and normalization as paper; preserve infeasible outputs.
    energy=np.einsum('bi,ij,bj->b',samples,Q,samples)
    candidates=[]
    for idx in np.argsort(energy)[:top]:
        w=B@samples[idx]
        if w.sum()<=0: continue
        w=w/w.sum()
        candidates.append({'weights':w.tolist(),**metrics(w,p),'qubo_energy_without_offset':float(energy[idx])})
    good=[c for c in candidates if c['feasible']]
    return {'best':min(good,key=lambda c:c['variance']) if good else None,
            'candidates':candidates,'feasible_fraction':len(good)/max(1,len(candidates))}


def qaoa_statevector(Q, layers=1, shots=512, maxiter=60, seed=42, parameters='cobyla', grid_size=7):
    """Ideal QAOA on a classical statevector simulator; NEVER label as QPU timing."""
    bits=len(Q)
    if bits>14 or not 1<=layers<=3: raise ValueError('QAOA capped at 14 qubits and 3 layers')
    X=bitstrings(bits); raw=np.einsum('bi,ij,bj->b',X,Q,X)
    E=raw-raw.min()  # Global-phase shift only; preserve paper cost scale.
    indexes=np.arange(len(X)); rng=np.random.default_rng(seed)
    def state(theta):
        psi=np.ones(len(X),dtype=complex)/np.sqrt(len(X))
        for k in range(layers):
            psi*=np.exp(-1j*theta[k]*E)
            beta=theta[layers+k]
            for j in range(bits):
                psi=np.cos(beta)*psi-1j*np.sin(beta)*psi[indexes^(1<<j)]
        return psi
    t=time.perf_counter()
    i=np.arange(1,layers+1)
    ramp=np.r_[(i+1)/layers*.6,(1-i/layers)*.3]
    expectation=lambda theta:float(np.abs(state(theta))**2@E)
    success=True; evaluations=0
    if parameters=='cobyla':
        fit=minimize(expectation,ramp,method='COBYLA',options={'maxiter':maxiter})
        theta=fit.x; success=bool(fit.success); evaluations=int(fit.nfev)
    elif parameters=='lr': theta=ramp
    elif parameters=='grid' and layers==1:
        grid=[np.array([g,b]) for g in np.linspace(0,2*np.pi,grid_size)
                                for b in np.linspace(0,np.pi,grid_size)]
        theta=min(grid,key=expectation); evaluations=len(grid)
    else: raise ValueError('Parameters must be cobyla, lr, or grid with p=1')
    probabilities=np.abs(state(theta))**2; probabilities/=probabilities.sum()
    samples=X[rng.choice(len(X),shots,p=probabilities)]
    return samples, {'method':'qaoa_classical_simulator','runtime_seconds':time.perf_counter()-t,
                     'samples':shots,'qubits':bits,'layers':layers,'optimizer_evaluations':evaluations,
                     'theta':theta.tolist(),'parameter_strategy':parameters,
                     'optimizer_success':success,'seed':seed}
