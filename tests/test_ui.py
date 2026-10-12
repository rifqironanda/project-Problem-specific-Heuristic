from pathlib import Path
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from psh.api import app
import psh.database as database

def test_streamlit_demo_run(monkeypatch):
    import httpx
    database.Base.metadata.drop_all(database.engine)
    with TestClient(app) as client:
        def request(method,url,**kwargs):
            kwargs.pop('trust_env',None); kwargs.pop('timeout',None)
            path=url.split(':8000')[-1]
            return client.request(method,path,**kwargs)
        monkeypatch.setattr(httpx,'request',request)
        ui=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=60)
        ui.run()
        assert not ui.exception
        ui.button[0].click().run()
        assert not ui.exception
        # Demo button, upload button (not shown without file), run button.
        run_button=next(b for b in ui.button if b.label=='Jalankan perbandingan')
        run_button.click().run()
        assert not ui.exception
        assert len(ui.dataframe)>=2
