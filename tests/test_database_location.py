import importlib.util
import sys
from pathlib import Path

DATABASE_PY = Path(__file__).parent.parent / "src" / "database" / "database.py"


def load_database_module(monkeypatch, exe_path):
    """Load a fresh copy of database.py as if running from a PyInstaller exe."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_path))
    spec = importlib.util.spec_from_file_location("database_under_test", DATABASE_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_packaged_db_lives_in_user_dir_and_legacy_db_is_copied_once(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("CV_CLASSIFIER_DATA_DIR", raising=False)
    old_install = tmp_path / "install" / "app-1"
    (old_install / "data").mkdir(parents=True)
    (old_install / "data" / "cv_analyzer.db").write_text("legacy")

    db = load_database_module(monkeypatch, old_install / "backend.exe")
    assert tmp_path / "install" not in db.data_dir.parents
    assert (db.data_dir / "cv_analyzer.db").read_text() == "legacy"

    # A new install folder must neither lose nor overwrite the user's database.
    (db.data_dir / "cv_analyzer.db").write_text("user-data")
    new_install = tmp_path / "install" / "app-2"
    (new_install / "data").mkdir(parents=True)
    (new_install / "data" / "cv_analyzer.db").write_text("other-legacy")

    db2 = load_database_module(monkeypatch, new_install / "backend.exe")
    assert db2.data_dir == db.data_dir
    assert (db2.data_dir / "cv_analyzer.db").read_text() == "user-data"


def test_data_dir_override(tmp_path, monkeypatch):
    monkeypatch.setenv("CV_CLASSIFIER_DATA_DIR", str(tmp_path / "custom"))
    db = load_database_module(monkeypatch, tmp_path / "backend.exe")
    assert db.data_dir == tmp_path / "custom"
