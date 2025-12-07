try:
    # pydantic v2 moved BaseSettings to pydantic-settings package
    from pydantic_settings import BaseSettings
except Exception:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class AriaSettings(BaseSettings):
    service_name: str = "aria"
    kafka_topics_scheduling_created: str = "aria.scheduling.created"
    kafka_topics_scheduling_due: str = "aria.scheduling.due"
    kafka_topics_published_success: str = "aria.published.success"
    kafka_topics_published_failed: str = "aria.published.failed"
    slo_publish_p95_ms: int = 2000


aria_settings = AriaSettings()


