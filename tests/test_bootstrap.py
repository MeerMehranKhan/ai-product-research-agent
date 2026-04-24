from __future__ import annotations

import sys

from bootstrap import ROOT, VENDOR, configure_paths


def test_configure_paths_prefers_active_environment(monkeypatch) -> None:
    fake_site_packages = str(ROOT / ".venv" / "Lib" / "site-packages")
    root_path = str(ROOT)
    vendor_path = str(VENDOR)
    original_path = list(sys.path)

    monkeypatch.setattr(sys, "path", [fake_site_packages, vendor_path, root_path, vendor_path], raising=False)

    configure_paths()

    assert sys.path[0] == root_path
    assert sys.path.count(root_path) == 1
    assert sys.path.count(vendor_path) == 1
    assert sys.path.index(vendor_path) > sys.path.index(fake_site_packages)
    assert sys.path[-1] == vendor_path

    monkeypatch.setattr(sys, "path", original_path, raising=False)
