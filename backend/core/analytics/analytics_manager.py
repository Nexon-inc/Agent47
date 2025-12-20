"""Compatibility shim: re-export AnalyticsManager from admin.analytics

Some modules import core.analytics.analytics_manager.AnalyticsManager
but the implementation lives in backend.admin.analytics.analytics_manager. This
module provides a thin wrapper so existing imports resolve.
"""
from typing import Optional

try:
    from admin.analytics.analytics_manager import (
        AnalyticsManager as AdminAnalyticsManager,
        init_analytics_manager as init_admin_analytics_manager,
        get_analytics_manager as get_admin_analytics_manager,
    )
except Exception:  # pragma: no cover - fail gracefully in tests/environments
    AdminAnalyticsManager = None
    def init_admin_analytics_manager():
        raise ImportError("admin.analytics.analytics_manager is not available")
    def get_admin_analytics_manager():
        raise ImportError("admin.analytics.analytics_manager is not available")

__all__ = [
    "AnalyticsManager",
    "init_analytics_manager",
    "get_analytics_manager",
]

AnalyticsManager = AdminAnalyticsManager
init_analytics_manager = init_admin_analytics_manager
get_analytics_manager = get_admin_analytics_manager
