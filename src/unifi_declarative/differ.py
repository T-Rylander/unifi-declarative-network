from typing import Any, Dict
from deepdiff import DeepDiff


def diff_configs(desired: Dict[str, Any], live: Dict[str, Any]) -> Dict[str, Any]:
    """Return a concise diff between desired and live controller objects."""
    dd = DeepDiff(live, desired, ignore_order=True)
    return dd.to_dict() if hasattr(dd, 'to_dict') else dict(dd)
