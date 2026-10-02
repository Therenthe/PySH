"""Keep test data in the workspace with inherited Windows permissions."""
from pathlib import Path
import uuid
import pytest


@pytest.fixture
def tmp_path():
    path = Path(__file__).resolve().parents[1] / ".runtime" / "test-data" / uuid.uuid4().hex
    path.mkdir(parents=True)
    return path
