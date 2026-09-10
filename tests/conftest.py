"""Load standalone modules without importing HA's integration entry point."""

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Only the package initializer is bypassed. Transport/flow tests import real HA APIs.
package = types.ModuleType("custom_components")
package.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", package)
package = types.ModuleType("custom_components.ble_arrival")
package.__path__ = [str(ROOT / "custom_components/ble_arrival")]
sys.modules.setdefault("custom_components.ble_arrival", package)
