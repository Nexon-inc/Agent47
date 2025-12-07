"""Shim package to forward agents.clara.app.core.* imports to the top-level core package.
This prevents import resolution from creating a separate module identity and avoids duplicate SQLAlchemy table registrations.
"""

from . import integration_manager, integrations, event_bus, nlp, nlp_utils, config, analytics, settings

__all__ = [
    "integration_manager",
    "integrations",
    "event_bus",
    "nlp",
    "nlp_utils",
    "config",
    "analytics",
    "settings",
]
