"""Basic tests for the lab handlers.
"""

import json
import pytest
import re
import tornado

from .utils import expected_http_error


@pytest.fixture
def notebooks(jp_create_notebook, labserverapp):
    nbpaths = (
        'notebook1.ipynb',
        'jlab_test_notebooks/notebook2.ipynb',
        'jlab_test_notebooks/level2/notebook3.ipynb'
    )
    for nb in nbpaths:
        jp_create_notebook(nb)
    return nbpaths


async def test_lab_handler(notebooks, jp_fetch):
    r = await jp_fetch('lab', 'jlab_test_notebooks')
    assert r.code == 200
    # Check that the lab template is loaded
    html = r.body.decode()
    assert "Files" in html
    assert "JupyterLab Server Application" in html


async def test_page_config(labserverapp, jp_fetch):
    settings = labserverapp.serverapp.web_app.settings
    page_config = settings.setdefault('page_config_data', {})
    # In labserverapp fixture, we dump a page_config file that also disables "@foo/bar:plugin"
    # Here we check that we correctly merge those settings with page_config_data in settings
    page_config.setdefault("disabledExtensions", {"@acme/paint:plugin": True})
    r = await jp_fetch('lab', 'jlab_test_notebooks')
    assert r.code == 200
    # Check that the lab template is loaded
    html = r.body.decode()
    m = re.search(
        r'<script id="jupyter-config-data" type="application/json">(?P<page_config>.*?)</script>',
        html,
        re.MULTILINE | re.DOTALL
    )
    page_config = json.loads(m.group("page_config"))
    assert sorted(page_config['disabledExtensions']) == ["@acme/paint:plugin", "@foo/bar:plugin"]

async def test_notebook_handler(notebooks, jp_fetch):
    for nbpath in notebooks:
        r = await jp_fetch('lab', nbpath)
        assert r.code == 200
        # Check that the lab template is loaded
        html = r.body.decode()
        assert "JupyterLab Server Application" in html


async def test_404(notebooks, jp_fetch):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch('foo')
    assert expected_http_error(e, 404)
