# On Windows, torch must be loaded before scikit-learn/scipy native libraries,
# otherwise c10.dll fails to initialize (WinError 1114). Import it first.
# The lite runtime (VISASHIELD_RUNTIME=onnx, or torch not installed) skips it entirely.
import os

if os.getenv("VISASHIELD_RUNTIME", "").lower() != "onnx":
    try:
        import torch  # noqa: F401
    except ImportError:
        pass
