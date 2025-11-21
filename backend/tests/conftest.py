import warnings
from unittest.mock import patch as _patch

import pytest


def pytest_configure(config):
    # Suppress deprecation warnings coming from python-jose that use naive utcnow()
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r".*datetime.datetime.utcnow\(\) is deprecated.*",
        module=r"jose\.jwt",
    )


def pytest_addoption(parser):
    # placeholder to ensure pytest sees plugins/options consistently
    pass


@pytest.fixture
def mocker(request):
    """Lightweight replacement for pytest-mock's `mocker` fixture.

    Provides a `.patch(target, **kwargs)` method that starts a patch and
    ensures it is stopped at test teardown. This is sufficient for the
    project's tests which only use `mocker.patch()`.
    """

    class Mocker:
        def patch(self, target, **kwargs):
            p = _patch(target, **kwargs)
            started = p.start()
            request.addfinalizer(p.stop)
            return started

    return Mocker()
