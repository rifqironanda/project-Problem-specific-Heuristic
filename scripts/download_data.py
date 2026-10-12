"""Free-source fetchers; remote data remains outside git. Provider terms apply."""
import argparse,io,re,zipfile,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
import httpx,pandas as pd,numpy as np

FRENCH='https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/30_Industry_Portfolios_Daily_CSV.zip'

def french(content):
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        name=next(n for n in z.namelist() if n.lower().endswith('.csv'))
        lines=z.read(name).decode('utf-8-sig').splitlines()
    start=next(i for i,line in enumerate(lines) if re.match(r'^\s*\d{8}\s*,',line))
    header=lines[start-1]; rows=[]
    for line in lines[start:]:
        if not re.match(r'^\s*\d{8}\s*,',line): break
        rows.append(line)
    df=pd.read_csv(io.StringIO('\n'.join([header]+rows)),index_col=0)
    df.index=pd.to_datetime(df.index.astype(str).str.strip(),format='%Y%m%d')
    df.columns=df.columns.str.strip()
    return df.replace([-99.99,-999.],np.nan)/100

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',choices=['french','yahoo'],default='french')
    parser.add_argument('--zip',help='Manual French ZIP path')
    parser.add_argument('--tickers',default='AAPL,MSFT,AMZN,GOOGL,META,NVDA')
    parser.add_argument('--start',default='2020-01-01'); parser.add_argument('--end',default='2024-01-01')
    parser.add_argument('--output',default='data/market/returns.csv')
    args=parser.parse_args()
    if args.source=='french':
        content=Path(args.zip).read_bytes() if args.zip else httpx.get(FRENCH,timeout=90,follow_redirects=True).raise_for_status().content
        frame=french(content); raw_hash=hashlib.sha256(content).hexdigest(); url=FRENCH
        frame=frame.loc[(frame.index>=args.start)&(frame.index<args.end)]
    else:
        import yfinance as yf
        raw=yf.download(args.tickers.split(','),start=args.start,end=args.end,auto_adjust=False,progress=False)
        prices=raw['Close'].dropna(axis=1,how='any')
        if prices.shape[1]<2: raise ValueError('Fewer than 2 complete tickers')
        frame=prices.pct_change(fill_method=None).iloc[1:]
        raw_hash=hashlib.sha256(prices.to_csv().encode()).hexdigest(); url='https://finance.yahoo.com/'
    frame=frame.dropna(axis=1,how='any')
    if frame.empty: raise ValueError('Empty source period')
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(output,index_label='date')
    output.with_suffix('.metadata.json').write_text(json.dumps({'source':args.source,'url':url,
        'retrieved_at':datetime.now(timezone.utc).isoformat(),'raw_sha256':raw_hash,
        'start_inclusive':args.start,'end_exclusive':args.end,'assets':list(frame.columns),
        'unit':'daily decimal return','price_adjustment':'raw Close for Yahoo; French value-weighted returns',
        'scope':'Alternative dataset; not original 1978-asset universe'},indent=2))
    print(f'Saved {frame.shape} to {output}')

if __name__=='__main__': main()
