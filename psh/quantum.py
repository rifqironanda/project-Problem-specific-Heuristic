"""Optional adapters, never invoked by the app automatically."""
import numpy as np

def qiskit_circuit(Q,theta,layers=1):
    from qiskit import QuantumCircuit
    bits=len(Q)
    if bits>14: raise ValueError('Educational circuit limit: 14 qubits')
    qc=QuantumCircuit(bits); qc.h(range(bits))
    h=-.5*np.diag(Q)-.5*(Q.sum(axis=1)-np.diag(Q))
    for k in range(layers):
        gamma,beta=theta[k],theta[layers+k]
        for j in range(bits): qc.rz(2*gamma*h[j],j)
        for i in range(bits):
            for j in range(i+1,bits):
                if Q[i,j]: qc.rzz(gamma*Q[i,j],i,j)
        for j in range(bits): qc.rx(2*beta,j)
    return qc

def dwave_sample(Q,reads=100,annealing_time=20,chain_strength=None):
    """Explicit user-invoked QPU call. Requires Leap credentials/entitlement.
    DWaveCliqueSampler matches paper sampler; available hardware may differ.
    """
    import dimod
    from dwave.system import DWaveCliqueSampler
    linear={i:float(Q[i,i]) for i in range(len(Q))}
    quadratic={(i,j):float(2*Q[i,j]) for i in range(len(Q)) for j in range(i+1,len(Q))}
    bqm=dimod.BinaryQuadraticModel(linear,quadratic,0.,dimod.BINARY)
    options={'num_reads':reads,'annealing_time':annealing_time}
    if chain_strength is not None: options['chain_strength']=chain_strength
    with DWaveCliqueSampler() as sampler:
        result=sampler.sample(bqm,**options)
        samples=np.asarray([[record.sample[i] for i in range(len(Q))]
                            for record in result.data(fields=['sample'])],dtype=int)
        return samples,dict(result.info)
