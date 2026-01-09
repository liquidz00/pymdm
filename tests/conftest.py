import shutil
import tempfile
from pathlib import Path

import pytest

from pymdm.logger import MdmLogger


@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def temp_log_file(temp_dir):
    return temp_dir / "test.log"


@pytest.fixture
def mock_logger():
    return MdmLogger(debug=True)
