"""Apply paper_freeze.env to os.environ before importing config/vessel_gym.

Usage:
  from apply_paper_freeze import apply_paper_freeze
  apply_paper_freeze()          # defaults
  apply_paper_freeze(overrides={"VESSEL_MSG_DIM": "8"})
"""
from __future__ import annotations
import os
from pathlib import Path

FREEZE_PATH = Path(__file__).resolve().parent / "paper_freeze.env"
FREEZE_VERSION = "common_freeze_v11"


def apply_paper_freeze(overrides: dict | None = None, force: bool = True) -> str:
    if not FREEZE_PATH.exists():
        raise FileNotFoundError(FREEZE_PATH)
    for k in list(os.environ):
        if k.startswith("VESSEL_"):
            del os.environ[k]
    for line in FREEZE_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if force or k not in os.environ:
            os.environ[k] = v
    if overrides:
        for k, v in overrides.items():
            os.environ[str(k)] = str(v)
    os.environ["VESSEL_PAPER_FREEZE"] = FREEZE_VERSION
    return FREEZE_VERSION


if __name__ == "__main__":
    print(apply_paper_freeze())
    for k in sorted(os.environ):
        if k.startswith("VESSEL_") or k == "PYTHONUNBUFFERED":
            print(f"{k}={os.environ[k]}")
