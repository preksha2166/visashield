# On Windows, torch must be loaded before scikit-learn/scipy native libraries,
# otherwise c10.dll fails to initialize (WinError 1114). Import it first.
try:
    import torch  # noqa: F401
except ImportError:  # torch is optional for the TF-IDF-only setup
    pass
