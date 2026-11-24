"""SYNTHETIC TEST BACKEND ONLY. This is not the NCLEdetector software."""
import os

if os.environ.get("NCEMS_ALLOW_SYNTHETIC_BACKEND") != "YES_FOR_TESTS":
    raise RuntimeError("Synthetic NCLEdetector fixture requires explicit test-only opt-in")
