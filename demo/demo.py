"""Launch: python demo/demo.py (also works outside the repository directory)."""

import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    # Set the profile before importing any eagerly initialized shared managers.
    previous_profile = os.environ.get("MOKISS_PROFILE_ROOT")
    previous_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="mokiss-demo-") as profile:
        os.environ["MOKISS_PROFILE_ROOT"] = profile
        Path(profile, "current_state").mkdir()
        os.chdir(ROOT)
        try:
            # On Windows even importing the PyQt5 package changes DLL lookup.
            # Load ORT before Qt so its native runtime can initialize.
            try:
                import onnxruntime
            except ImportError:
                pass
            # Windows venvs below a Japanese path need an explicit Qt path.
            import PyQt5
            plugins = Path(PyQt5.__file__).parent / "Qt5" / "plugins"
            os.environ.setdefault("QT_PLUGIN_PATH", str(plugins))
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(plugins / "platforms"))
            from demo.application import DemoApplication
            return 0 if DemoApplication().run() else 1
        finally:
            os.chdir(previous_cwd)
            if previous_profile is None:
                os.environ.pop("MOKISS_PROFILE_ROOT", None)
            else:
                os.environ["MOKISS_PROFILE_ROOT"] = previous_profile


if __name__ == "__main__":
    sys.exit(main())
