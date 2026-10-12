import numpy as np
import pytest

def test_qiskit_circuit_matches_cost_mixer_state():
    pytest.importorskip('qiskit')
    from qiskit.quantum_info import Statevector
    from psh.quantum import qiskit_circuit
    from psh.qubo import bitstrings
    Q=np.array([[1.,.3],[.3,-.2]])
    gamma,beta=.4,.2
    X=bitstrings(2); E=np.einsum('bi,ij,bj->b',X,Q,X)
    psi=np.exp(-1j*gamma*E)/2
    idx=np.arange(4)
    for j in range(2): psi=np.cos(beta)*psi-1j*np.sin(beta)*psi[idx^(1<<j)]
    qstate=Statevector.from_instruction(qiskit_circuit(Q,[gamma,beta])).data
    np.testing.assert_allclose(np.abs(qstate)**2,np.abs(psi)**2,atol=1e-12)
