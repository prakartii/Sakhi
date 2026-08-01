"""Re-exports app.core.config's Settings under the conventional `settings.py`
name. app.core.config is the implementation; import from either — both refer
to the same cached singleton.
"""

from app.core.config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
