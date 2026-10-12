from pathlib import Path
import json
from psh.data import synthetic
from psh.experiment import run_experiment

root=Path(__file__).resolve().parents[1]
frame=synthetic(n=6)
frame.to_csv(root/'data/demo_returns.csv',index_label='date')
report=run_experiment(frame,reads=50,sweeps=50,include_quantum=True)
(root/'data/demo_report.json').write_text(json.dumps(report,indent=2))
for row in report['results']:
    print(row['method'], 'feasible=',row['feasible'], 'variance=',row.get('variance'))
