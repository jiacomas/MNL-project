import warnings


def pytest_configure(config):
    # Suppress deprecation warnings coming from python-jose that use naive utcnow()
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r".*datetime.datetime.utcnow\(\) is deprecated.*",
        module=r"jose\.jwt",
    )
