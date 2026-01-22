from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any, List
import os
from pathlib import Path
from dotenv import load_dotenv
import json

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
    # Direct access to GCP Secret Manager secrets
    host: str = os.getenv("REDIS_HOST", "localhost")  # e.g., clear-hamster-30497.upstash.io
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD") or None  # Upstash token only (no "default:")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    @property
    def is_production(self) -> bool:
        """Detect if running in production (not localhost)"""
        return self.host not in {"localhost", "127.0.0.1", "host.docker.internal"}

    @property
    def redis_url(self) -> str:
        """Build full Upstash-compatible Redis URL with TLS"""
        if self.password:
            # Upstash requires username "default"
            auth = f"default:{self.password}" if not self.password.startswith("default:") else self.password
            return f"rediss://{auth}@{self.host}:{self.port}/{self.redis_db}"
        return f"rediss://{self.host}:{self.port}/{self.redis_db}"

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",  # Reads REDIS_HOST, REDIS_PORT, REDIS_PASSWORD from Cloud Run
        extra="allow"
    )

class ChromaDBSettings(BaseSettings):
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_persist_directory: str = "./chroma_db"
    
    @property
    def persist_directory(self) -> str:
        return self.chroma_persist_directory
    
    @property
    def chroma_url(self) -> str:
        return f"http://{self.chroma_host}:{self.chroma_port}"
    
    model_config = SettingsConfigDict(env_prefix="CHROMA_", extra="allow")

class KafkaSettings(BaseSettings):
    bootstrap_servers: str = "localhost:9092"
    client_id: str = "agent47"
    group_id: str = "agent47_group"
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    security_protocol: str = "PLAINTEXT"  # PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
    sasl_mechanism: Optional[str] = None  # PLAIN, SCRAM-SHA-256, SCRAM-SHA-512, OAUTHBEARER
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_check_hostname: bool = True
    ssl_cafile: Optional[str] = None  # Path to CA certificate file
    ssl_certfile: Optional[str] = None  # Path to client certificate file
    ssl_keyfile: Optional[str] = None  # Path to client key file
    
    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="allow")

class ChutesAISettings(BaseSettings):
    """DEPRECATED: Chutes AI Configuration - Replaced by Groq API
    
    This class is kept for backward compatibility only.
    All new code should use GroqSettings instead.
    """
    chutes_api_key: str = os.getenv("CHUTES_API_KEY", "")
    chutes_api_url: str = os.getenv("CHUTES_API_URL", "https://llm.chutes.ai/v1")
    
    chutes_llm_model: str = "zai-org/GLM-4.5-Air"
    chutes_llm_max_tokens: int = 4000
    chutes_llm_temperature: float = 0.7
    chutes_llm_top_p: float = 0.9
    chutes_llm_frequency_penalty: float = 0.0
    chutes_llm_presence_penalty: float = 0.0
    
    chutes_image_model: str = "JuggernautXL"
    chutes_image_max_tokens: int = 1000
    chutes_image_temperature: float = 0.8
    
    chutes_batch_size: int = 1
    chutes_max_concurrent_requests: int = 10
    chutes_request_timeout: int = 30
    
    chutes_health_check_interval: int = 60
    chutes_max_retries: int = 3
    chutes_retry_delay: int = 1
    
    chutes_rate_limit_per_minute: int = 100
    chutes_rate_limit_per_hour: int = 1000
    chutes_daily_limit: int = 10000
    
    chutes_enable_logging: bool = True
    chutes_log_level: str = "INFO"
    chutes_enable_metrics: bool = True
    
    model_config = SettingsConfigDict(env_prefix="CHUTES_", extra="allow")

class GrokLLMSettings(BaseSettings):
    """Grok LLM Configuration (Local Emergency Fallback)"""
    grok_model_path: str = "./models/grok-llm"
    grok_api_url: str = "http://localhost:8008"
    grok_api_key: str = ""
    
    grok_max_tokens: int = 4000
    grok_temperature: float = 0.7
    grok_top_p: float = 0.9
    grok_frequency_penalty: float = 0.0
    grok_presence_penalty: float = 0.0
    
    grok_batch_size: int = 1
    grok_max_concurrent_requests: int = 10
    grok_request_timeout: int = 30
    
    grok_health_check_interval: int = 60
    grok_max_retries: int = 3
    grok_retry_delay: int = 1
    
    grok_max_memory_gb: int = 16
    grok_enable_quantization: bool = True
    grok_quantization_level: str = "int8"
    
    grok_enable_logging: bool = True
    grok_log_level: str = "INFO"
    grok_enable_metrics: bool = True
    grok_metrics_port: int = 8002
    
    grok_enable_auth: bool = False
    grok_auth_token: str = ""
    grok_rate_limit_per_minute: int = 1000
    grok_rate_limit_per_hour: int = 10000
    
    grok_docker_container: str = "grok-llm"
    grok_docker_image: str = "grok-llm:latest"
    grok_docker_network: str = "agent47-network"
    
    model_config = SettingsConfigDict(env_prefix="GROK_", extra="allow")

class OllamaSettings(BaseSettings):
    """Ollama LLM configuration for Llama 3 8B"""
    ollama_api_url: str = os.getenv("OLLAMA_API_URL", "http://localhost:8008")
    ollama_model_name: str = os.getenv("OLLAMA_MODEL_NAME", "llama3:8b")
    ollama_max_tokens: int = 16000
    ollama_temperature: float = 0.7
    ollama_top_p: float = 0.9
    ollama_frequency_penalty: float = 0.0
    ollama_presence_penalty: float = 0.0
    ollama_batch_size: int = 1
    ollama_max_concurrent_requests: int = 100
    ollama_request_timeout: int = 900
    ollama_health_check_interval: int = 60
    ollama_max_retries: int = 3
    ollama_retry_delay: int = 2
    
    ollama_max_memory_gb: int = 16
    ollama_enable_quantization: bool = True
    ollama_quantization_level: str = "int8"
    
    ollama_enable_logging: bool = True
    ollama_log_level: str = "INFO"
    ollama_enable_metrics: bool = True
    ollama_metrics_port: int = 8002
    
    ollama_enable_auth: bool = False
    ollama_auth_token: str = ""
    ollama_rate_limit_per_minute: int = 1000
    ollama_rate_limit_per_hour: int = 10000
    
    ollama_docker_container: str = "ollama-llm"
    ollama_docker_image: str = "ollama-llm:latest"
    ollama_docker_network: str = "agent47-network"
    
    model_config = SettingsConfigDict(env_prefix="OLLAMA_", extra="allow")

class GroqSettings(BaseSettings):
    """Groq API configuration for LLM, TTS, and STT services"""
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_api_base_url: str = os.getenv("GROQ_API_BASE_URL", "https://api.groq.com/openai/v1")
    
    groq_default_model: str = os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile")
    groq_max_tokens: int = int(os.getenv("GROQ_MAX_TOKENS", "12000"))
    groq_temperature: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    groq_top_p: float = float(os.getenv("GROQ_TOP_P", "0.9"))
    groq_request_timeout: int = int(os.getenv("GROQ_REQUEST_TIMEOUT", "60"))
    
    groq_rate_limit_per_minute: int = int(os.getenv("GROQ_RATE_LIMIT_PER_MINUTE", "30"))
    groq_rate_limit_per_day: int = int(os.getenv("GROQ_RATE_LIMIT_PER_DAY", "1000"))
    
    groq_tts_model: str = os.getenv("GROQ_TTS_MODEL", "playai-tts")
    groq_tts_rate_limit_per_minute: int = int(os.getenv("GROQ_TTS_RATE_LIMIT_PER_MINUTE", "30"))
    groq_tts_rate_limit_per_day: int = int(os.getenv("GROQ_TTS_RATE_LIMIT_PER_DAY", "1000"))
    
    groq_stt_model: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
    groq_stt_rate_limit_per_minute: int = int(os.getenv("GROQ_STT_RATE_LIMIT_PER_MINUTE", "30"))
    groq_stt_rate_limit_per_day: int = int(os.getenv("GROQ_STT_RATE_LIMIT_PER_DAY", "1000"))
    groq_stt_enabled: bool = os.getenv("GROQ_STT_ENABLED", "true").lower() == "true"
    groq_stt_language: str = os.getenv("GROQ_STT_LANGUAGE", "auto")
    
    voice_output_enabled: bool = os.getenv("VOICE_OUTPUT_ENABLED", "true").lower() == "true"
    voice_output_language: str = os.getenv("VOICE_OUTPUT_LANGUAGE", "auto")
    voice_output_natural: bool = os.getenv("VOICE_OUTPUT_NATURAL", "true").lower() == "true"
    voice_output_speed: float = float(os.getenv("VOICE_OUTPUT_SPEED", "1.0"))
    voice_output_pitch: float = float(os.getenv("VOICE_OUTPUT_PITCH", "1.0"))
    
    agent_voice_shakes: str = os.getenv("AGENT_VOICE_SHAKES", "adam")
    agent_voice_eric: str = os.getenv("AGENT_VOICE_ERIC", "arnold")
    agent_voice_joe: str = os.getenv("AGENT_VOICE_JOE", "josh")
    agent_voice_clara: str = os.getenv("AGENT_VOICE_CLARA", "bella")
    agent_voice_jackie: str = os.getenv("AGENT_VOICE_JACKIE", "rachel")
    agent_voice_purity: str = os.getenv("AGENT_VOICE_PURITY", "emily")
    agent_voice_aria: str = os.getenv("AGENT_VOICE_ARIA", "nova")
    
    groq_max_concurrent_requests: int = int(os.getenv("GROQ_MAX_CONCURRENT_REQUESTS", "10"))
    groq_max_retries: int = int(os.getenv("GROQ_MAX_RETRIES", "3"))
    groq_retry_delay: int = int(os.getenv("GROQ_RETRY_DELAY", "1"))
    
    groq_health_check_interval: int = int(os.getenv("GROQ_HEALTH_CHECK_INTERVAL", "60"))
    groq_enable_logging: bool = os.getenv("GROQ_ENABLE_LOGGING", "true").lower() == "true"
    groq_log_level: str = os.getenv("GROQ_LOG_LEVEL", "INFO")
    groq_enable_metrics: bool = os.getenv("GROQ_ENABLE_METRICS", "true").lower() == "true"
    
    model_config = SettingsConfigDict(env_prefix="GROQ_", extra="allow")

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
    app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")
    credentials_file: str = os.getenv("GMAIL_CREDENTIALS_FILE", "./credentials/gmail_credentials.json")
    token_file: str = os.getenv("GMAIL_TOKEN_FILE", "./credentials/gmail_token.json")
    scopes: list = ["https://www.googleapis.com/auth/gmail.send"]
    from_email: str = os.getenv("GMAIL_FROM_EMAIL", "agent47assist@gmail.com")
    from_name: str = os.getenv("GMAIL_FROM_NAME", "Agent47 Support")
    verification_token_expiry_hours: int = int(os.getenv("GMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS", "24"))
    model_config = SettingsConfigDict(env_prefix="GMAIL_", extra="allow")

class WebhookSettings(BaseSettings):
    shared_secrets_json: str = "{}"

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
    access_token_expire_minutes: int = int(os.getenv("SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    refresh_token_expire_days: int = int(os.getenv("SECURITY_REFRESH_TOKEN_EXPIRE_DAYS", "90"))
    model_config = SettingsConfigDict(env_prefix="SECURITY_", extra="allow")

class BillingSettings(BaseSettings):
    paystack_secret_key: str = os.getenv("BILLING_PAYSTACK_SECRET_KEY", os.getenv("PAYSTACK_SECRET_KEY", ""))
    paystack_public_key: str = os.getenv("BILLING_PAYSTACK_PUBLIC_KEY", os.getenv("PAYSTACK_PUBLIC_KEY", ""))
    paystack_webhook_secret: str = os.getenv("BILLING_PAYSTACK_WEBHOOK_SECRET", os.getenv("PAYSTACK_WEBHOOK_SECRET", ""))
    webhook_base_url: str = os.getenv("BILLING_WEBHOOK_BASE_URL", os.getenv("BASE_URL", "http://localhost:8000"))
    model_config = SettingsConfigDict(env_prefix="BILLING_", extra="allow")

class ProductionMonitoringSettings(BaseSettings):
    enable_monitoring: bool = True
    monitoring_interval: int = 30
    enable_alerts: bool = True
    alert_email: str = "agent47assist@gmail.com"
    alert_webhook: str = ""
    max_response_time: int = 15
    max_error_rate: float = 0.05
    min_success_rate: float = 0.95
    enable_auto_scaling: bool = True
    min_instances: int = 1
    max_instances: int = 5
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    enable_backup: bool = True
    backup_interval: int = 3600
    backup_retention_days: int = 7
    enable_auto_recovery: bool = True
    prometheus_port: int = 8003
    prometheus_metrics_path: str = "/metrics"
    grafana_url: str = "http://localhost:3000"
    grafana_api_key: str = ""
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    model_config = SettingsConfigDict(env_prefix="MONITORING_", extra="allow")

class AgentSettings(BaseSettings):
    aria_port: int = 8001
    clara_port: int = 8002
    eric_port: int = 8003
    jackie_port: int = 8004
    joe_port: int = 8005
    purity_port: int = 8006
    shakes_port: int = 8007
    health_check_interval: int = 30
    restart_threshold: int = 3
    max_restart_attempts: int = 5
    inter_communication_enabled: bool = True
    task_delegation_enabled: bool = True
    shared_memory_enabled: bool = True
    model_config = SettingsConfigDict(env_prefix="AGENT_", extra="allow")

class PhoneScrapingSettings(BaseSettings):
    phone_scraping_enabled: bool = os.getenv("PHONE_SCRAPING_ENABLED", "true").lower() == "true"
    phone_scraping_rate_limit: int = int(os.getenv("PHONE_SCRAPING_RATE_LIMIT", "100"))
    model_config = SettingsConfigDict(env_prefix="PHONE_SCRAPING_", extra="allow")

class TwilioSettings(BaseSettings):
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    twilio_enabled: bool = os.getenv("TWILIO_ENABLED", "false").lower() == "true"
    model_config = SettingsConfigDict(env_prefix="TWILIO_", extra="allow")

class GoogleMapsSettings(BaseSettings):
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    google_maps_enabled: bool = os.getenv("GOOGLE_MAPS_ENABLED", "false").lower() == "true"
    google_maps_rate_limit: int = int(os.getenv("GOOGLE_MAPS_RATE_LIMIT", "1000"))
    model_config = SettingsConfigDict(env_prefix="GOOGLE_MAPS_", extra="allow")

class GeolocationSettings(BaseSettings):
    geolocation_enabled: bool = os.getenv("GEOLOCATION_ENABLED", "true").lower() == "true"
    geolocation_consent_required: bool = os.getenv("GEOLOCATION_CONSENT_REQUIRED", "true").lower() == "true"
    geolocation_accuracy: str = os.getenv("GEOLOCATION_ACCURACY", "high")
    geolocation_timeout: int = int(os.getenv("GEOLOCATION_TIMEOUT", "5000"))
    geolocation_max_age: int = int(os.getenv("GEOLOCATION_MAX_AGE", "300000"))
    model_config = SettingsConfigDict(env_prefix="GEOLOCATION_", extra="allow")

class GoogleGeminiImageSettings(BaseSettings):
    google_gemini_api_key: str = os.getenv("GOOGLE_GEMINI_API_KEY", "")
    google_gemini_api_base_url: str = os.getenv("GOOGLE_GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    
    google_gemini_pro_model: str = os.getenv("GOOGLE_GEMINI_PRO_MODEL", "gemini-3.0-pro-image-preview")
    google_gemini_flash_model: str = os.getenv("GOOGLE_GEMINI_FLASH_MODEL", "gemini-2.5-flash-image")
    
    google_gemini_default_width: int = int(os.getenv("GOOGLE_GEMINI_DEFAULT_WIDTH", "1024"))
    google_gemini_default_height: int = int(os.getenv("GOOGLE_GEMINI_DEFAULT_HEIGHT", "1024"))
    google_gemini_max_width: int = int(os.getenv("GOOGLE_GEMINI_MAX_WIDTH", "4096"))
    google_gemini_max_height: int = int(os.getenv("GOOGLE_GEMINI_MAX_HEIGHT", "4096"))
    google_gemini_flash_max_width: int = int(os.getenv("GOOGLE_GEMINI_FLASH_MAX_WIDTH", "1024"))
    google_gemini_flash_max_height: int = int(os.getenv("GOOGLE_GEMINI_FLASH_MAX_HEIGHT", "1024"))
    
    google_gemini_request_timeout: int = int(os.getenv("GOOGLE_GEMINI_REQUEST_TIMEOUT", "120"))
    google_gemini_max_retries: int = int(os.getenv("GOOGLE_GEMINI_MAX_RETRIES", "3"))
    google_gemini_retry_delay: int = int(os.getenv("GOOGLE_GEMINI_RETRY_DELAY", "2"))
    
    google_gemini_rate_limit_per_minute: int = int(os.getenv("GOOGLE_GEMINI_RATE_LIMIT_PER_MINUTE", "60"))
    google_gemini_rate_limit_per_day: int = int(os.getenv("GOOGLE_GEMINI_RATE_LIMIT_PER_DAY", "1000"))
    
    google_gemini_health_check_interval: int = int(os.getenv("GOOGLE_GEMINI_HEALTH_CHECK_INTERVAL", "60"))
    google_gemini_enable_logging: bool = os.getenv("GOOGLE_GEMINI_ENABLE_LOGGING", "true").lower() == "true"
    google_gemini_log_level: str = os.getenv("GOOGLE_GEMINI_LOG_LEVEL", "INFO")
    google_gemini_enable_metrics: bool = os.getenv("GOOGLE_GEMINI_ENABLE_METRICS", "true").lower() == "true"
    
    model_config = SettingsConfigDict(env_prefix="GOOGLE_GEMINI_", extra="allow")

def _parse_backend_cors_origins() -> List[str]:
    """
    Parse BACKEND_CORS_ORIGINS from the environment.
    
    Supports either:
      - JSON array string, e.g. '["https://agent47-eight.vercel.app","http://localhost:3000"]'
      - Comma-separated list, e.g. 'https://agent47-eight.vercel.app,http://localhost:3000'
    Falls back to localhost defaults if parsing fails or env is not set.
    """
    default_origins = ["http://localhost:3000", "http://localhost:8000"]
    raw = os.getenv("BACKEND_CORS_ORIGINS", "").strip()
    if not raw:
        return default_origins
    try:
        if raw.startswith("["):
            parsed = json.loads(raw)
            if isinstance(parsed, list) and all(isinstance(o, str) for o in parsed):
                return parsed
        # Fallback: comma-separated
        parts = [o.strip() for o in raw.split(",") if o.strip()]
        return parts or default_origins
    except Exception:
        return default_origins


class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = True
    project_name: str = "Agent47"
    version: str = "1.0.0"
    
    primary_llm_provider: str = os.getenv("PRIMARY_LLM_PROVIDER", "groq")
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Public frontend URL (e.g. https://agent47-eight.vercel.app)
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Public backend base URL (Cloud Run URL in production)
    # Example: https://agent47-backend-805021975902.us-central1.run.app
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    api_v1_prefix: str = "/api/v1"
    # CORS origins – read from BACKEND_CORS_ORIGINS env when set, otherwise localhost defaults
    backend_cors_origins: List[str] = _parse_backend_cors_origins()
    
    supabase: SupabaseSettings = SupabaseSettings()
    redis: RedisSettings = RedisSettings()
    chroma: ChromaDBSettings = ChromaDBSettings()
    kafka: KafkaSettings = KafkaSettings()
    
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
    
    security: SecuritySettings = SecuritySettings()
    billing: BillingSettings = BillingSettings()
    monitoring: ProductionMonitoringSettings = ProductionMonitoringSettings()
    agents: AgentSettings = AgentSettings()
    
    phone_scraping: PhoneScrapingSettings = PhoneScrapingSettings()
    twilio: TwilioSettings = TwilioSettings()
    google_maps: GoogleMapsSettings = GoogleMapsSettings()
    geolocation: GeolocationSettings = GeolocationSettings()
    
    google_gemini_image: GoogleGeminiImageSettings = GoogleGeminiImageSettings()
    
    admin_default_email: str = os.getenv("ADMIN_DEFAULT_EMAIL", "agent47assist@gmail.com")
    admin_default_password: str = os.getenv("ADMIN_DEFAULT_PASSWORD", "G.z.t.i.p.0,1,0")
    admin_session_timeout_hours: int = int(os.getenv("ADMIN_SESSION_TIMEOUT_HOURS", "24"))
    admin_enable_2fa: bool = os.getenv("ADMIN_ENABLE_2FA", "false").lower() == "true"
    admin_ip_whitelist: list = os.getenv("ADMIN_IP_WHITELIST", "").split(",") if os.getenv("ADMIN_IP_WHITELIST") else []
    
    upload_dir: str = "./uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    log_level: str = "INFO"
    log_file: str = "./logs/agent47.log"
    
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

ensure_directories()

def get_settings() -> Settings:
    return settings

def get_config() -> Settings:
    return settings