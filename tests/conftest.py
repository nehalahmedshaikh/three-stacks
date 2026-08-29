import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# A permutation found unsortable by three stacks in series during the M4
# sweep (results/witnesses.jsonl).  Used by tests that need a k=3 negative
# instance, since none exists below length 14.
K3_WITNESS = (
    27, 11, 36, 33, 10, 5, 1, 8, 20, 19, 40, 13, 18, 23, 29, 25, 22, 37, 16,
    12, 4, 2, 6, 30, 38, 7, 24, 17, 31, 21, 39, 14, 34, 32, 35, 15, 3, 28, 26, 9,
)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: takes minutes; deselect with -m 'not slow'")


@pytest.fixture(scope="session")
def k3_witness():
    return K3_WITNESS
