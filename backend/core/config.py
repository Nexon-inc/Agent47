from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv
# Load environment variables from project root .env explicitly
_ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
try:
    load_dotenv(dotenv_path=_ROOT_ENV_PATH)
except Exception:
    pass

# Note: Admin platform credentials are stored in database via OAuth flow
# No need to load from .env file - credentials come from system_platform_credentials table

class SupabaseSettings(BaseSettings):
    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_db_url: str = os.getenv("SUPABASE_DB_URL", "")
    
    # Storage Configuration
    storage_bucket: str = os.getenv("SUPABASE_STORAGE_BUCKET", "agent47-uploads")
    storage_url: str = os.getenv("SUPABASE_STORAGE_URL", "")
    
    # Realtime Configuration
    realtime_url: str = os.getenv("SUPABASE_REALTIME_URL", "")
    
    # Auth Configuration
    auth_url: str = os.getenv("SUPABASE_AUTH_URL", "")
    
    @property
    def database_url(self) -> str:
        """Get the database URL for direct PostgreSQL connection"""
        return self.supabase_db_url
    
    @property
    def api_url(self) -> str:
        """Get the Supabase API URL"""
        return self.supabase_url
    
    model_config = SettingsConfigDict(env_prefix="SUPABASE_", extra="allow")

class RedisSettings(BaseSettings):
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Production mode detection
    @property
    def is_production(self) -> bool:
        """Detect if running in production mode"""
        return (
            self.redis_host != "localhost" and
            self.redis_host != "127.0.0.1"
        )
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="allow")

class ChromaDBSettings(BaseSettings):
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_persist_directory: str = "./chroma_db"
    # Some modules may refer to this as persist_directory
    @property
    def persist_directory(self) -> str:
        return self.chroma_persist_directory
    
    @property
    def chroma_url(self) -> str:
        return f"http://{self.chroma_host}:{self.chroma_port}"
    
    model_config = SettingsConfigDict(env_prefix="CHROMA_", extra="allow")

class KafkaSettings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "agent47"
    kafka_group_id: str = "agent47_group"
    kafka_auto_offset_reset: str = "earliest"
    kafka_enable_auto_commit: bool = True
    
    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="allow")

# DEPRECATED: Chutes AI has been replaced by Groq API
# This class is kept for backward compatibility but is no longer used
# Migration: Use GroqSettings instead
class ChutesAISettings(BaseSettings):
    """DEPRECATED: Chutes AI Configuration - Replaced by Groq API
    
    This class is kept for backward compatibility only.
    All new code should use GroqSettings instead.
    """
    # Chutes AI Configuration
    chutes_api_key: str = os.getenv("CHUTES_API_KEY", "")  # Chutes AI API key
    chutes_api_url: str = os.getenv("CHUTES_API_URL", "https://llm.chutes.ai/v1")  # Chutes AI API URL
    
    # Primary LLM Model
    chutes_llm_model: str = "zai-org/GLM-4.5-Air"  # Primary LLM model (free)
    chutes_llm_max_tokens: int = 4000
    chutes_llm_temperature: float = 0.7
    chutes_llm_top_p: float = 0.9
    chutes_llm_frequency_penalty: float = 0.0
    chutes_llm_presence_penalty: float = 0.0
    
    # Image Generation Model
    chutes_image_model: str = "JuggernautXL"  # Primary image generation model
    chutes_image_max_tokens: int = 1000
    chutes_image_temperature: float = 0.8
    
    # Performance Settings
    chutes_batch_size: int = 1
    chutes_max_concurrent_requests: int = 10
    chutes_request_timeout: int = 30  # seconds
    
    # Health Monitoring
    chutes_health_check_interval: int = 60  # seconds
    chutes_max_retries: int = 3
    chutes_retry_delay: int = 1  # seconds
    
    # Rate Limiting
    chutes_rate_limit_per_minute: int = 100
    chutes_rate_limit_per_hour: int = 1000
    chutes_daily_limit: int = 10000  # Daily request limit
    
    # Production Settings
    chutes_enable_logging: bool = True
    chutes_log_level: str = "INFO"
    chutes_enable_metrics: bool = True
    
    model_config = SettingsConfigDict(env_prefix="CHUTES_", extra="allow")

class GrokLLMSettings(BaseSettings):
    """Grok LLM Configuration (Local Emergency Fallback)
    
    NOTE: This is for LOCAL Grok LLM (not Groq API).
    Groq API configuration is in GroqSettings.
    This is kept as an emergency fallback option for local deployments.
    """
    # Grok LLM Configuration (Emergency Fallback)
    grok_model_path: str = "./models/grok-llm"  # Local model path
    grok_api_url: str = "http://localhost:8008"  # Local Grok service URL
    grok_api_key: str = ""  # Optional API key for local service
    
    # Model Parameters
    grok_max_tokens: int = 4000
    grok_temperature: float = 0.7
    grok_top_p: float = 0.9
    grok_frequency_penalty: float = 0.0
    grok_presence_penalty: float = 0.0
    
    # Performance Settings
    grok_batch_size: int = 1
    grok_max_concurrent_requests: int = 10
    grok_request_timeout: int = 30  # seconds
    
    # Health Monitoring
    grok_health_check_interval: int = 60  # seconds
    grok_max_retries: int = 3
    grok_retry_delay: int = 1  # seconds
    
    # Resource Management
    grok_max_memory_gb: int = 16
    grok_enable_quantization: bool = True
    grok_quantization_level: str = "int8"  # int8, int4, fp16
    
    # Production Settings
    grok_enable_logging: bool = True
    grok_log_level: str = "INFO"
    grok_enable_metrics: bool = True
    grok_metrics_port: int = 8002
    
    # Security Settings
    grok_enable_auth: bool = False
    grok_auth_token: str = ""
    grok_rate_limit_per_minute: int = 1000
    grok_rate_limit_per_hour: int = 10000
    
    # Docker Settings
    grok_docker_container: str = "grok-llm"
    grok_docker_image: str = "grok-llm:latest"
    grok_docker_network: str = "agent47-network"
    
    model_config = SettingsConfigDict(env_prefix="GROK_", extra="allow")

class OllamaSettings(BaseSettings):
    """Ollama LLM configuration for Llama 3 8B"""
    ollama_api_url: str = os.getenv("OLLAMA_API_URL", "http://localhost:8008")
    ollama_model_name: str = os.getenv("OLLAMA_MODEL_NAME", "llama3:8b")
    ollama_max_tokens: int = 16000  # Increased for complete responses
    ollama_temperature: float = 0.7
    ollama_top_p: float = 0.9
    ollama_frequency_penalty: float = 0.0
    ollama_presence_penalty: float = 0.0
    ollama_batch_size: int = 1
    ollama_max_concurrent_requests: int = 100
    ollama_request_timeout: int = 900  # 15 minutes for long responses
    ollama_health_check_interval: int = 60
    ollama_max_retries: int = 3
    ollama_retry_delay: int = 2
    
    # Resource Management
    ollama_max_memory_gb: int = 16
    ollama_enable_quantization: bool = True
    ollama_quantization_level: str = "int8"
    
    # Production Settings
    ollama_enable_logging: bool = True
    ollama_log_level: str = "INFO"
    ollama_enable_metrics: bool = True
    ollama_metrics_port: int = 8002
    
    # Security Settings
    ollama_enable_auth: bool = False
    ollama_auth_token: str = ""
    ollama_rate_limit_per_minute: int = 1000
    ollama_rate_limit_per_hour: int = 10000
    
    # Docker Settings
    ollama_docker_container: str = "ollama-llm"
    ollama_docker_image: str = "ollama-llm:latest"
    ollama_docker_network: str = "agent47-network"
    
    model_config = SettingsConfigDict(env_prefix="OLLAMA_", extra="allow")

class GroqSettings(BaseSettings):
    """Groq API configuration for LLM, TTS, and STT services"""
    # API Configuration
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_api_base_url: str = os.getenv("GROQ_API_BASE_URL", "https://api.groq.com/openai/v1")
    
    # LLM Configuration
    groq_default_model: str = os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile")
    groq_max_tokens: int = int(os.getenv("GROQ_MAX_TOKENS", "12000"))  # Max output for llama-3.3-70b-versatile
    groq_temperature: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    groq_top_p: float = float(os.getenv("GROQ_TOP_P", "0.9"))
    groq_request_timeout: int = int(os.getenv("GROQ_REQUEST_TIMEOUT", "60"))  # seconds
    
    # LLM Rate Limiting (Free tier: 30 req/min, 1000/day)
    groq_rate_limit_per_minute: int = int(os.getenv("GROQ_RATE_LIMIT_PER_MINUTE", "30"))
    groq_rate_limit_per_day: int = int(os.getenv("GROQ_RATE_LIMIT_PER_DAY", "1000"))
    
    # TTS Configuration
    groq_tts_model: str = os.getenv("GROQ_TTS_MODEL", "playai-tts")  # playai-tts or playai-tts-arabic
    groq_tts_rate_limit_per_minute: int = int(os.getenv("GROQ_TTS_RATE_LIMIT_PER_MINUTE", "30"))
    groq_tts_rate_limit_per_day: int = int(os.getenv("GROQ_TTS_RATE_LIMIT_PER_DAY", "1000"))
    
    # STT Configuration
    groq_stt_model: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
    groq_stt_rate_limit_per_minute: int = int(os.getenv("GROQ_STT_RATE_LIMIT_PER_MINUTE", "30"))
    groq_stt_rate_limit_per_day: int = int(os.getenv("GROQ_STT_RATE_LIMIT_PER_DAY", "1000"))
    groq_stt_enabled: bool = os.getenv("GROQ_STT_ENABLED", "true").lower() == "true"
    groq_stt_language: str = os.getenv("GROQ_STT_LANGUAGE", "auto")
    
    # Voice Output Settings
    voice_output_enabled: bool = os.getenv("VOICE_OUTPUT_ENABLED", "true").lower() == "true"
    voice_output_language: str = os.getenv("VOICE_OUTPUT_LANGUAGE", "auto")
    voice_output_natural: bool = os.getenv("VOICE_OUTPUT_NATURAL", "true").lower() == "true"
    voice_output_speed: float = float(os.getenv("VOICE_OUTPUT_SPEED", "1.0"))
    voice_output_pitch: float = float(os.getenv("VOICE_OUTPUT_PITCH", "1.0"))
    
    # Agent Voice Overrides (from .env)
    agent_voice_shakes: str = os.getenv("AGENT_VOICE_SHAKES", "adam")
    agent_voice_eric: str = os.getenv("AGENT_VOICE_ERIC", "arnold")
    agent_voice_joe: str = os.getenv("AGENT_VOICE_JOE", "josh")
    agent_voice_clara: str = os.getenv("AGENT_VOICE_CLARA", "bella")
    agent_voice_jackie: str = os.getenv("AGENT_VOICE_JACKIE", "rachel")
    agent_voice_purity: str = os.getenv("AGENT_VOICE_PURITY", "emily")
    agent_voice_aria: str = os.getenv("AGENT_VOICE_ARIA", "nova")
    
    # Performance Settings
    groq_max_concurrent_requests: int = int(os.getenv("GROQ_MAX_CONCURRENT_REQUESTS", "10"))
    groq_max_retries: int = int(os.getenv("GROQ_MAX_RETRIES", "3"))
    groq_retry_delay: int = int(os.getenv("GROQ_RETRY_DELAY", "1"))  # seconds
    
    # Health Monitoring
    groq_health_check_interval: int = int(os.getenv("GROQ_HEALTH_CHECK_INTERVAL", "60"))  # seconds
    groq_enable_logging: bool = os.getenv("GROQ_ENABLE_LOGGING", "true").lower() == "true"
    groq_log_level: str = os.getenv("GROQ_LOG_LEVEL", "INFO")
    groq_enable_metrics: bool = os.getenv("GROQ_ENABLE_METRICS", "true").lower() == "true"
    
    model_config = SettingsConfigDict(env_prefix="GROQ_", extra="allow")

# S3Settings removed - replaced with Supabase Storage

class OpenAISettings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "")
    openai_default_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    model_config = SettingsConfigDict(env_prefix="OPENAI_", extra="allow")

class BrandwatchSettings(BaseSettings):
    api_key: str = ""
    base_url: str = "https://api.brandwatch.com"

    model_config = SettingsConfigDict(env_prefix="BRANDWATCH_", extra="allow")

class SemrushSettings(BaseSettings):
    api_key: str = ""
    base_url: str = "https://api.semrush.com"

    model_config = SettingsConfigDict(env_prefix="SEMRUSH_", extra="allow")

class CanvaSettings(BaseSettings):
    api_key: str = ""
    base_url: str = "https://api.canva.com"

    model_config = SettingsConfigDict(env_prefix="CANVA_", extra="allow")

class SlackSettings(BaseSettings):
    bot_token: str = ""
    signing_secret: str = ""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    base_url: str = "https://slack.com/api"
    auth_url: str = "https://slack.com/oauth/v2/authorize"
    token_url: str = "https://slack.com/api/oauth.v2.access"

    model_config = SettingsConfigDict(env_prefix="SLACK_", extra="allow")

class BufferSettings(BaseSettings):
    access_token: str = ""
    base_url: str = "https://api.bufferapp.com/1"
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""

    model_config = SettingsConfigDict(env_prefix="BUFFER_", extra="allow")

class LinkedInSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    base_url: str = "https://api.linkedin.com/v2"
    auth_url: str = "https://www.linkedin.com/oauth/v2/authorization"
    token_url: str = "https://www.linkedin.com/oauth/v2/accessToken"

    model_config = SettingsConfigDict(env_prefix="LINKEDIN_", extra="allow")

class FacebookSettings(BaseSettings):
    app_id: str = ""
    app_secret: str = ""
    redirect_uri: str = ""
    graph_url: str = "https://graph.facebook.com"
    auth_url: str = "https://www.facebook.com/v18.0/dialog/oauth"
    token_url: str = "https://graph.facebook.com/v18.0/oauth/access_token"

    model_config = SettingsConfigDict(env_prefix="FACEBOOK_", extra="allow")

class TwitterSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    access_token_secret: str = ""
    bearer_token: str = ""
    base_url: str = "https://api.twitter.com/2"
    auth_url: str = "https://twitter.com/i/oauth2/authorize"
    token_url: str = "https://api.twitter.com/2/oauth2/token"

    model_config = SettingsConfigDict(env_prefix="TWITTER_", extra="allow")

class InstagramSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    base_url: str = "https://graph.instagram.com"
    auth_url: str = "https://api.instagram.com/oauth/authorize"
    token_url: str = "https://api.instagram.com/oauth/access_token"

    model_config = SettingsConfigDict(env_prefix="INSTAGRAM_", extra="allow")

class YouTubeSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    api_key: str = ""
    base_url: str = "https://www.googleapis.com/youtube/v3"
    auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"

    model_config = SettingsConfigDict(env_prefix="YOUTUBE_", extra="allow")

class TikTokSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    base_url: str = "https://open.tiktokapis.com/v2"
    auth_url: str = "https://www.tiktok.com/auth/authorize"
    token_url: str = "https://open.tiktokapis.com/v2/oauth/token"

    model_config = SettingsConfigDict(env_prefix="TIKTOK_", extra="allow")

class PinterestSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    base_url: str = "https://api.pinterest.com/v5"
    auth_url: str = "https://www.pinterest.com/oauth"
    token_url: str = "https://api.pinterest.com/v5/oauth/token"

    model_config = SettingsConfigDict(env_prefix="PINTEREST_", extra="allow")

class HubSpotSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    api_key: str = ""
    base_url: str = "https://api.hubapi.com"
    auth_url: str = "https://app.hubspot.com/oauth/authorize"
    token_url: str = "https://api.hubapi.com/oauth/v1/token"

    model_config = SettingsConfigDict(env_prefix="HUBSPOT_", extra="allow")

class SalesforceSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    username: str = ""
    password: str = ""
    security_token: str = ""
    base_url: str = "https://api.salesforce.com"
    auth_url: str = "https://login.salesforce.com/services/oauth2/authorize"
    token_url: str = "https://login.salesforce.com/services/oauth2/token"

    model_config = SettingsConfigDict(env_prefix="SALESFORCE_", extra="allow")

class MailchimpSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    api_key: str = ""
    server_prefix: str = "us1"
    base_url: str = "https://us1.api.mailchimp.com/3.0"
    auth_url: str = "https://login.mailchimp.com/oauth2/authorize"
    token_url: str = "https://login.mailchimp.com/oauth2/token"

    model_config = SettingsConfigDict(env_prefix="MAILCHIMP_", extra="allow")

class ShopifySettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    shop_domain: str = ""
    base_url: str = "https://admin.shopify.com/store"
    auth_url: str = "https://{shop}.myshopify.com/admin/oauth/authorize"
    token_url: str = "https://{shop}.myshopify.com/admin/oauth/access_token"

    model_config = SettingsConfigDict(env_prefix="SHOPIFY_", extra="allow")

class EmailSettings(BaseSettings):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "agent47assist@gmail.com"
    smtp_password: str = ""
    from_email: str = "agent47assist@gmail.com"
    from_name: str = "Agent47 Support"
    use_tls: bool = True

    model_config = SettingsConfigDict(env_prefix="EMAIL_", extra="allow")

class GmailAPISettings(BaseSettings):
    client_id: str = os.getenv("GMAIL_CLIENT_ID", "")
    client_secret: str = os.getenv("GMAIL_CLIENT_SECRET", "")
    refresh_token: str = os.getenv("GMAIL_REFRESH_TOKEN", "")
    access_token: str = os.getenv("GMAIL_ACCESS_TOKEN", "")
    credentials_file: str = os.getenv("GMAIL_CREDENTIALS_FILE", "./credentials/gmail_credentials.json")
    token_file: str = os.getenv("GMAIL_TOKEN_FILE", "./credentials/gmail_token.json")
    scopes: list = ["https://www.googleapis.com/auth/gmail.send"]
    from_email: str = os.getenv("GMAIL_FROM_EMAIL", "agent47assist@gmail.com")
    from_name: str = os.getenv("GMAIL_FROM_NAME", "Agent47 Support")
    verification_token_expiry_hours: int = int(os.getenv("GMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS", "24"))
    
    model_config = SettingsConfigDict(env_prefix="GMAIL_", extra="allow")

class WebhookSettings(BaseSettings):
    shared_secrets_json: str = "{}"  # JSON map of platform->secret

    @property
    def shared_secrets(self) -> Dict[str, str]:
        try:
            import json
            return json.loads(self.shared_secrets_json)
        except Exception:
            return {}

    model_config = SettingsConfigDict(env_prefix="WEBHOOK_", extra="allow")

class SecuritySettings(BaseSettings):
    secret_key: str = os.getenv("SECURITY_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"))
    algorithm: str = os.getenv("SECURITY_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours default
    refresh_token_expire_days: int = int(os.getenv("SECURITY_REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days default
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_", extra="allow")

class BillingSettings(BaseSettings):
    paystack_secret_key: str = os.getenv("BILLING_PAYSTACK_SECRET_KEY", os.getenv("PAYSTACK_SECRET_KEY", ""))
    paystack_public_key: str = os.getenv("BILLING_PAYSTACK_PUBLIC_KEY", os.getenv("PAYSTACK_PUBLIC_KEY", ""))
    paystack_webhook_secret: str = os.getenv("BILLING_PAYSTACK_WEBHOOK_SECRET", os.getenv("PAYSTACK_WEBHOOK_SECRET", ""))
    webhook_base_url: str = os.getenv("BILLING_WEBHOOK_BASE_URL", os.getenv("BASE_URL", "http://localhost:8000"))
    
    model_config = SettingsConfigDict(env_prefix="BILLING_", extra="allow")

class ProductionMonitoringSettings(BaseSettings):
    # Monitoring Configuration
    enable_monitoring: bool = True
    monitoring_interval: int = 30  # seconds
    
    # Alerting Settings
    enable_alerts: bool = True
    alert_email: str = "agent47assist@gmail.com"
    alert_webhook: str = ""
    
    # Performance Thresholds
    max_response_time: int = 15  # seconds
    max_error_rate: float = 0.05  # 5%
    min_success_rate: float = 0.95  # 95%
    
    # Auto-scaling Settings
    enable_auto_scaling: bool = True
    min_instances: int = 1
    max_instances: int = 5
    scale_up_threshold: float = 0.8  # 80% CPU/RAM
    scale_down_threshold: float = 0.3  # 30% CPU/RAM
    
    # Disaster Recovery
    enable_backup: bool = True
    backup_interval: int = 3600  # 1 hour
    backup_retention_days: int = 7
    enable_auto_recovery: bool = True
    
    # Prometheus Metrics
    prometheus_port: int = 8003
    prometheus_metrics_path: str = "/metrics"
    
    # Grafana Dashboard
    grafana_url: str = "http://localhost:3000"
    grafana_api_key: str = ""
    
    # Sentry Error Tracking
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    
    model_config = SettingsConfigDict(env_prefix="MONITORING_", extra="allow")

class AgentSettings(BaseSettings):
    """Agent-specific configuration settings"""
    
    # Agent Ports
    aria_port: int = 8001
    clara_port: int = 8002
    eric_port: int = 8003
    jackie_port: int = 8004
    joe_port: int = 8005
    purity_port: int = 8006
    shakes_port: int = 8007
    
    # Agent Health Check
    health_check_interval: int = 30
    restart_threshold: int = 3
    max_restart_attempts: int = 5
    
    # Agent Communication
    inter_communication_enabled: bool = True
    task_delegation_enabled: bool = True
    shared_memory_enabled: bool = True
    
    model_config = SettingsConfigDict(env_prefix="AGENT_", extra="allow")

class PhoneScrapingSettings(BaseSettings):
    """Phone scraping configuration"""
    phone_scraping_enabled: bool = os.getenv("PHONE_SCRAPING_ENABLED", "true").lower() == "true"
    phone_scraping_rate_limit: int = int(os.getenv("PHONE_SCRAPING_RATE_LIMIT", "100"))
    model_config = SettingsConfigDict(env_prefix="PHONE_SCRAPING_", extra="allow")

class TwilioSettings(BaseSettings):
    """Twilio phone calling configuration"""
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    twilio_enabled: bool = os.getenv("TWILIO_ENABLED", "false").lower() == "true"
    model_config = SettingsConfigDict(env_prefix="TWILIO_", extra="allow")

class GoogleMapsSettings(BaseSettings):
    """Google Maps API configuration"""
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    google_maps_enabled: bool = os.getenv("GOOGLE_MAPS_ENABLED", "false").lower() == "true"
    google_maps_rate_limit: int = int(os.getenv("GOOGLE_MAPS_RATE_LIMIT", "1000"))
    model_config = SettingsConfigDict(env_prefix="GOOGLE_MAPS_", extra="allow")

class GeolocationSettings(BaseSettings):
    """Geo-location targeting configuration"""
    geolocation_enabled: bool = os.getenv("GEOLOCATION_ENABLED", "true").lower() == "true"
    geolocation_consent_required: bool = os.getenv("GEOLOCATION_CONSENT_REQUIRED", "true").lower() == "true"
    geolocation_accuracy: str = os.getenv("GEOLOCATION_ACCURACY", "high")
    geolocation_timeout: int = int(os.getenv("GEOLOCATION_TIMEOUT", "5000"))
    geolocation_max_age: int = int(os.getenv("GEOLOCATION_MAX_AGE", "300000"))
    model_config = SettingsConfigDict(env_prefix="GEOLOCATION_", extra="allow")

class GoogleGeminiImageSettings(BaseSettings):
    """Google Gemini Image Generation Configuration"""
    # API Configuration
    google_gemini_api_key: str = os.getenv("GOOGLE_GEMINI_API_KEY", "")
    google_gemini_api_base_url: str = os.getenv("GOOGLE_GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    
    # Model Configuration
    # Pro tier: Gemini 3 Pro Image Preview (Nano Banana Pro Preview)
    google_gemini_pro_model: str = os.getenv("GOOGLE_GEMINI_PRO_MODEL", "gemini-3.0-pro-image-preview")
    # Starter tier: Gemini 2.5 Flash Image (Nano Banana)
    google_gemini_flash_model: str = os.getenv("GOOGLE_GEMINI_FLASH_MODEL", "gemini-2.5-flash-image")
    
    # Default Settings
    google_gemini_default_width: int = int(os.getenv("GOOGLE_GEMINI_DEFAULT_WIDTH", "1024"))
    google_gemini_default_height: int = int(os.getenv("GOOGLE_GEMINI_DEFAULT_HEIGHT", "1024"))
    google_gemini_max_width: int = int(os.getenv("GOOGLE_GEMINI_MAX_WIDTH", "4096"))  # 4K for Pro
    google_gemini_max_height: int = int(os.getenv("GOOGLE_GEMINI_MAX_HEIGHT", "4096"))  # 4K for Pro
    google_gemini_flash_max_width: int = int(os.getenv("GOOGLE_GEMINI_FLASH_MAX_WIDTH", "1024"))
    google_gemini_flash_max_height: int = int(os.getenv("GOOGLE_GEMINI_FLASH_MAX_HEIGHT", "1024"))
    
    # Performance Settings
    google_gemini_request_timeout: int = int(os.getenv("GOOGLE_GEMINI_REQUEST_TIMEOUT", "120"))  # seconds
    google_gemini_max_retries: int = int(os.getenv("GOOGLE_GEMINI_MAX_RETRIES", "3"))
    google_gemini_retry_delay: int = int(os.getenv("GOOGLE_GEMINI_RETRY_DELAY", "2"))  # seconds
    
    # Rate Limiting
    google_gemini_rate_limit_per_minute: int = int(os.getenv("GOOGLE_GEMINI_RATE_LIMIT_PER_MINUTE", "60"))
    google_gemini_rate_limit_per_day: int = int(os.getenv("GOOGLE_GEMINI_RATE_LIMIT_PER_DAY", "1000"))
    
    # Health Monitoring
    google_gemini_health_check_interval: int = int(os.getenv("GOOGLE_GEMINI_HEALTH_CHECK_INTERVAL", "60"))  # seconds
    google_gemini_enable_logging: bool = os.getenv("GOOGLE_GEMINI_ENABLE_LOGGING", "true").lower() == "true"
    google_gemini_log_level: str = os.getenv("GOOGLE_GEMINI_LOG_LEVEL", "INFO")
    google_gemini_enable_metrics: bool = os.getenv("GOOGLE_GEMINI_ENABLE_METRICS", "true").lower() == "true"
    
    model_config = SettingsConfigDict(env_prefix="GOOGLE_GEMINI_", extra="allow")

# Note: Admin platform credentials are stored in the database via OAuth flow
# (system_platform_credentials table), not in .env files.
# Agents access credentials through SystemPlatformManager, not through config.

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True
    project_name: str = "Agent47"
    version: str = "1.0.0"
    
    # Primary LLM Provider
    primary_llm_provider: str = os.getenv("PRIMARY_LLM_PROVIDER", "groq")
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Frontend Settings
    frontend_url: str = "http://localhost:3000"
    
    # Base URL for OAuth callbacks and redirects
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Supabase (Database, Auth, Storage, Realtime)
    supabase: SupabaseSettings = SupabaseSettings()
    
    # Cache (Redis - optional, can use Supabase for caching)
    redis: RedisSettings = RedisSettings()
    
    # Vector Database
    chroma: ChromaDBSettings = ChromaDBSettings()
    
    # Message Broker
    kafka: KafkaSettings = KafkaSettings()
    
    # AI Services
    groq: GroqSettings = GroqSettings()
    ollama: OllamaSettings = OllamaSettings()
    grok: GrokLLMSettings = GrokLLMSettings()
    openai: OpenAISettings = OpenAISettings()
    brandwatch: BrandwatchSettings = BrandwatchSettings()
    semrush: SemrushSettings = SemrushSettings()
    canva: CanvaSettings = CanvaSettings()
    slack: SlackSettings = SlackSettings()
    email: EmailSettings = EmailSettings()
    gmail: GmailAPISettings = GmailAPISettings()
    webhooks: WebhookSettings = WebhookSettings()
    buffer: BufferSettings = BufferSettings()
    linkedin: LinkedInSettings = LinkedInSettings()
    facebook: FacebookSettings = FacebookSettings()
    twitter: TwitterSettings = TwitterSettings()
    instagram: InstagramSettings = InstagramSettings()
    youtube: YouTubeSettings = YouTubeSettings()
    tiktok: TikTokSettings = TikTokSettings()
    pinterest: PinterestSettings = PinterestSettings()
    hubspot: HubSpotSettings = HubSpotSettings()
    salesforce: SalesforceSettings = SalesforceSettings()
    mailchimp: MailchimpSettings = MailchimpSettings()
    shopify: ShopifySettings = ShopifySettings()
    
    # Security
    security: SecuritySettings = SecuritySettings()
    
    # Billing
    billing: BillingSettings = BillingSettings()
    
    # Production Monitoring
    monitoring: ProductionMonitoringSettings = ProductionMonitoringSettings()
    
    # Agent Configuration
    agents: AgentSettings = AgentSettings()
    
    # Phone & Location Services
    phone_scraping: PhoneScrapingSettings = PhoneScrapingSettings()
    twilio: TwilioSettings = TwilioSettings()
    google_maps: GoogleMapsSettings = GoogleMapsSettings()
    geolocation: GeolocationSettings = GeolocationSettings()
    
    # Google Gemini Image Generation
    google_gemini_image: GoogleGeminiImageSettings = GoogleGeminiImageSettings()
    
    # Admin Configuration
    admin_default_email: str = os.getenv("ADMIN_DEFAULT_EMAIL", "agent47assist@gmail.com")
    admin_default_password: str = os.getenv("ADMIN_DEFAULT_PASSWORD", "")
    admin_session_timeout_hours: int = int(os.getenv("ADMIN_SESSION_TIMEOUT_HOURS", "24"))
    admin_enable_2fa: bool = os.getenv("ADMIN_ENABLE_2FA", "false").lower() == "true"
    admin_ip_whitelist: list = os.getenv("ADMIN_IP_WHITELIST", "").split(",") if os.getenv("ADMIN_IP_WHITELIST") else []
    
    # Note: Admin platform credentials are stored in database via OAuth
    # Access through SystemPlatformManager, not through config
    
    # File Storage
    upload_dir: str = "./uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/agent47.log"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow")

# Global settings instance
settings = Settings()

# Ensure directories exist
def ensure_directories():
    directories = [
        settings.upload_dir,
        Path(settings.log_file).parent,
        settings.chroma.chroma_persist_directory
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Initialize directories
ensure_directories()

# Convenience accessors for compatibility across modules
def get_settings() -> Settings:
    return settings

def get_config() -> Settings:
    return settings
