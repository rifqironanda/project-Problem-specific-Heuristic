"""Execute all notebook cells with IPython when the host forbids kernel sockets.
This is explicit in-process validation, not a separate Jupyter kernel launch.
"""
from pathlib import Path
import io,contextlib,base64
import nbformat
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.core.interactiveshell import InteractiveShell

root=Path(__file__).resolve().parents[1]
path=root/'notebooks/01_minvola_replication.ipynb'
notebook=nbformat.read(path,as_version=4)
shell=InteractiveShell.instance()
outputs=[]
def publish(data,metadata=None,**kwargs):
    outputs.append(nbformat.v4.new_output('display_data',data=data,metadata=metadata or {}))
shell.display_pub.publish=publish
shell.displayhook.write_format_data=lambda format_dict,md_dict=None:publish(format_dict,md_dict)
def show(*args,**kwargs):
    for number in plt.get_fignums():
        buffer=io.BytesIO(); plt.figure(number).savefig(buffer,format='png',bbox_inches='tight',dpi=110)
        publish({'image/png':base64.b64encode(buffer.getvalue()).decode(),'text/plain':'Matplotlib figure'})
    plt.close('all')
plt.show=show
count=0
for cell in notebook.cells:
    if cell.cell_type!='code': continue
    count+=1; outputs=[]; stdout=io.StringIO(); stderr=io.StringIO()
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        result=shell.run_cell(cell.source,store_history=False)
    if result.error_before_exec or result.error_in_exec:
        raise RuntimeError(f'Cell {count} failed: {stderr.getvalue()} {stdout.getvalue()}') from result.error_in_exec
    if stdout.getvalue(): outputs.insert(0,nbformat.v4.new_output('stream',name='stdout',text=stdout.getvalue()))
    if stderr.getvalue(): outputs.append(nbformat.v4.new_output('stream',name='stderr',text=stderr.getvalue()))
    cell.outputs=outputs; cell.execution_count=count
notebook.metadata['validation']={'executor':'IPython in-process; environment blocks Jupyter kernel sockets','code_cells':count}
nbformat.validate(notebook); nbformat.write(notebook,path)
print(f'All {count} notebook code cells executed with captured outputs (IPython in-process).')
