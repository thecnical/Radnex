"""Backward compatibility layer for legacy ZimZilla imports.

Redirects any `import zimzilla` or `from zimzilla import ...` directly to `radnex`.
"""
import sys
import importlib

import radnex

# Register zimzilla in sys.modules pointing to radnex
sys.modules["zimzilla"] = radnex

# Dynamic submodule loader for zimzilla.*
class _CompatFinder:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if fullname.startswith("zimzilla."):
            sub = fullname[len("zimzilla."):]
            try:
                mod = importlib.import_module(f"radnex.{sub}")
                sys.modules[fullname] = mod
                return mod.__spec__
            except Exception:
                return None
        return None

sys.meta_path.insert(0, _CompatFinder)
