"""Streamlit UI calls REST API; does not bypass server or PostgreSQL."""
import os,json
import httpx,pandas as pd,streamlit as st
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='MinVola Lab',layout='wide')
st.title('Problem-specific Heuristic Lab')
st.caption('Eksperimen alokasi aset: heuristik klasik, AI, dan QAOA simulator')
st.info('Data demo bersifat sintetis. Setiap hasil menampilkan kelayakan; hasil tidak layak tidak dipakai untuk evaluasi test.')
base=os.getenv('API_BASE_URL','http://127.0.0.1:8000')
headers={'X-API-Key':os.getenv('API_KEY','')}

def call(method,path,**kwargs):
    try:
        r=httpx.request(method,base+path,headers=headers,timeout=300,trust_env=False,**kwargs)
        r.raise_for_status(); return r.json()
    except httpx.HTTPError as e:
        detail=e.response.text if isinstance(e,httpx.HTTPStatusError) else str(e)
        st.error(detail); return None

with st.sidebar:
    st.header('Data & eksperimen')
    if st.button('Buat dataset demo'):
        ds=call('POST','/datasets/demo')
        if ds: st.session_state['dataset_id']=ds['id']; st.success('Demo tersimpan')
    uploaded=st.file_uploader('CSV: date dan kolom setiap aset',type=['csv'])
    kind=st.selectbox('Isi CSV',['returns','prices'])
    if uploaded and st.button('Simpan CSV'):
        ds=call('POST','/datasets',files={'file':(uploaded.name,uploaded.getvalue(),'text/csv')},data={'kind':kind})
        if ds: st.session_state['dataset_id']=ds['id']; st.success('CSV tersimpan')
    options=call('GET','/datasets') or []
    mapping={f"{x['name']} · {x['id'][:8]}":x['id'] for x in options}
    if mapping:
        selected=st.selectbox('Dataset tersimpan',list(mapping))
        st.session_state['dataset_id']=mapping[selected]
    auto=st.checkbox('Target otomatis: quantile 70%',value=True)
    target=st.number_input('Target return tahunan (desimal)',value=.1,min_value=-1.,max_value=10.,disabled=auto)
    d=st.slider('Presisi biner d',1,3,1)
    qaoa=st.checkbox('Sertakan QAOA simulator (maks. 14 qubit)',value=False)
    if st.button('Jalankan perbandingan',type='primary',disabled='dataset_id' not in st.session_state):
        with st.spinner('Mengolah data, melatih AI, dan menjalankan algoritma…'):
            report=call('POST','/experiments',json={'dataset_id':st.session_state['dataset_id'],
                        'target':None if auto else target,'d':d,'include_quantum':qaoa,'reads':100,'sweeps':100})
            if report: st.session_state['report']=report

report=st.session_state.get('report')
if report:
    st.write(f"Target: {report['target_annual_return']:.2%} · δ: {report['delta']:.4f} · seed: {report['seed']}")
    table=pd.DataFrame([{k:r.get(k) for k in ['method','feasible','expected_return','volatility','variance','runtime_seconds',
                           'training_seconds','variance_ratio_to_continuous_reference']} for r in report['results']])
    st.dataframe(table,hide_index=True,use_container_width=True)
    feasible=[r for r in report['results'] if r.get('feasible')]
    if feasible:
        weights=pd.DataFrame({r['method']:r['weights'] for r in feasible},index=report['assets'])
        st.subheader('Bobot aset pada hasil layak'); st.bar_chart(weights)
        st.subheader('Hasil pada data test yang tidak digunakan untuk pelatihan')
        st.dataframe(pd.DataFrame([{'method':r['method'],**r.get('heldout',{})} for r in feasible]),hide_index=True)
    else: st.warning('Tidak ada hasil layak. Periksa target return dan batas bobot.')
    st.caption(report['timing_note'])
    with st.expander('Penjelasan AI dan algoritma'):
        st.write('AI surrogate adalah Random Forest yang meniru bobot solver kontinu. MAE validasi bukan ukuran keuntungan. '
                 'Hybrid memilih hasil terbaik dari heuristik dan solver yang dimulai dari prediksi AI. '
                 'QAOA berjalan pada simulator klasik ideal; waktunya bukan waktu komputer kuantum.')
    st.download_button('Unduh laporan JSON',json.dumps(report,indent=2),'experiment.json','application/json')
else:
    st.write('Mulai dengan **Buat dataset demo**, lalu **Jalankan perbandingan**. Untuk data nyata, unggah CSV sesuai DATA_CONTRACT.md.')
