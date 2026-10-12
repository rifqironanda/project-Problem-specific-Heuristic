from pathlib import Path
import nbformat
from nbclient import NotebookClient
import os
from jupyter_client import KernelManager

root=Path(__file__).resolve().parents[1]
path=root/'notebooks/01_minvola_replication.ipynb'
nb=nbformat.read(path,as_version=4)
options={}
if os.getenv('NOTEBOOK_IPC')=='1':
    # Optional restricted Linux environment: Unix IPC instead of TCP sockets.
    options['km']=KernelManager(kernel_name='python3',transport='ipc',ip='/tmp/psh-notebook-kernel')
client=NotebookClient(nb,timeout=300,kernel_name='python3',resources={'metadata':{'path':str(root)}},**options)
client.execute()
nbformat.write(nb,path)
print('Notebook executed successfully:',path)
