import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece

logger = logging.getLogger(__name__)

class CMSIntegrationService:
    """Service for CMS and platform integration"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 2000,
            "temperature": 0.5
        }
    
    async def initialize(self):
        """Initialize CMS integration service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("CMS integration service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CMS integration service: {e}")
            raise
    
    async def connect_cms_platform(
        self,
        user_id: int,
        platform_name: str,
        connection_config: Dict[str, Any],
        platform_type: str = "cms"
    ) -> Dict[str, Any]:
        """Connect to CMS platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Test connection
            connection_test = await self._test_platform_connection(
                platform_name, connection_config, platform_type
            )
            
            if not connection_test.get("success"):
                return {"success": False, "error": "Failed to connect to platform"}
            
            # Store connection configuration
            connection_id = await self._store_connection_config(
                user_id, platform_name, connection_config, platform_type
            )
            
            # Generate integration guidelines
            guidelines_prompt = self._create_integration_guidelines_prompt(
                platform_name, platform_type, connection_config
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that creates CMS integration guidelines."}, {"role": "user", "content": guidelines_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.5)
            integration_guidelines = ai_response.text_content if ai_response.success else ""
            
            # Publish event
            await self.event_bus.publish("shakes.cms_connected", {
                "user_id": user_id,
                "platform_name": platform_name,
                "platform_type": platform_type,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "success": True,
                "connection_id": connection_id,
                "platform_name": platform_name,
                "platform_type": platform_type,
                "connection_status": "connected",
                "integration_guidelines": integration_guidelines,
                "supported_features": connection_test.get("supported_features", []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"CMS platform connection failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_content_to_cms(
        self,
        content_piece_id: int,
        platform_name: str,
        publishing_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish content to connected CMS platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Get platform connection
                connection_config = await self._get_connection_config(
                    content_piece.project.user_id, platform_name
                )
                
                if not connection_config:
                    return {"success": False, "error": "Platform connection not found"}
                
                # Prepare content for publishing
                prepared_content = await self._prepare_content_for_platform(
                    content_piece, platform_name, publishing_options
                )
                
                # Publish to platform
                publish_result = await self._publish_to_platform(
                    platform_name, prepared_content, publishing_options, connection_config
                )
                
                if not publish_result.get("success"):
                    return {"success": False, "error": "Failed to publish to platform"}
                
                # Update content piece with publishing info
                content_piece.published_platforms = content_piece.published_platforms or []
                if platform_name not in content_piece.published_platforms:
                    content_piece.published_platforms.append(platform_name)
                
                content_piece.updated_at = datetime.utcnow()
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.content_published", {
                    "content_piece_id": content_piece_id,
                    "platform_name": platform_name,
                    "publish_result": publish_result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "platform_name": platform_name,
                    "publish_result": publish_result,
                    "published_url": publish_result.get("url"),
                    "publishing_options": publishing_options,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content publishing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_content_from_cms(
        self,
        user_id: int,
        platform_name: str,
        sync_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync content from CMS platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get platform connection
            connection_config = await self._get_connection_config(user_id, platform_name)
            
            if not connection_config:
                return {"success": False, "error": "Platform connection not found"}
            
            # Fetch content from platform
            platform_content = await self._fetch_content_from_platform(
                platform_name, sync_options, connection_config
            )
            
            if not platform_content.get("success"):
                return {"success": False, "error": "Failed to fetch content from platform"}
            
            # Process and store content
            synced_content = await self._process_synced_content(
                user_id, platform_name, platform_content.get("content", [])
            )
            
            # Publish event
            await self.event_bus.publish("shakes.content_synced", {
                "user_id": user_id,
                "platform_name": platform_name,
                "synced_count": len(synced_content),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "success": True,
                "user_id": user_id,
                "platform_name": platform_name,
                "synced_content": synced_content,
                "total_synced": len(synced_content),
                "sync_options": sync_options,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_platform_content_structure(
        self,
        user_id: int,
        platform_name: str
    ) -> Dict[str, Any]:
        """Get content structure and capabilities of platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get platform connection
            connection_config = await self._get_connection_config(user_id, platform_name)
            
            if not connection_config:
                return {"success": False, "error": "Platform connection not found"}
            
            # Get platform structure
            platform_structure = await self._get_platform_structure(
                platform_name, connection_config
            )
            
            # Generate platform insights
            insights_prompt = self._create_platform_insights_prompt(
                platform_name, platform_structure
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that analyzes CMS platform structures."}, {"role": "user", "content": insights_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.5)
            platform_insights = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "platform_name": platform_name,
                "platform_structure": platform_structure,
                "platform_insights": platform_insights,
                "supported_content_types": platform_structure.get("supported_content_types", []),
                "supported_features": platform_structure.get("supported_features", []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Platform structure retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_content_for_platform(
        self,
        content_piece_id: int,
        platform_name: str,
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """Optimize content for specific platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Get platform structure
                platform_structure = await self._get_platform_structure(
                    platform_name, await self._get_connection_config(content_piece.project.user_id, platform_name)
                )
                
                # Generate platform optimization
                optimization_prompt = self._create_platform_optimization_prompt(
                    content_piece, platform_name, platform_structure, optimization_goals
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes content for CMS platforms."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.5)
                optimized_content = ai_response.text_content if ai_response.success else ""
                
                # Generate optimization recommendations
                recommendations_prompt = self._create_optimization_recommendations_prompt(
                    content_piece, platform_name, optimization_goals, optimized_content
                )
                messages = [{"role": "system", "content": "You are an AI assistant that provides CMS optimization recommendations."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.5)
                optimization_recommendations = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "platform_name": platform_name,
                    "optimized_content": optimized_content,
                    "optimization_recommendations": optimization_recommendations,
                    "optimization_goals": optimization_goals,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content platform optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_platform_connection(
        self, platform_name: str, connection_config: Dict[str, Any], platform_type: str
    ) -> Dict[str, Any]:
        """Test connection to platform"""
        try:
            import aiohttp
            
            # Platform-specific connection testing
            platform_configs = {
                "wordpress": {
                    "test_url": f"{connection_config.get('base_url', '')}/wp-json/wp/v2/posts",
                    "auth_header": f"Bearer {connection_config.get('api_key', '')}"
                },
                "shopify": {
                    "test_url": f"{connection_config.get('shop_url', '')}/admin/api/2023-10/products.json",
                    "auth_header": f"Basic {connection_config.get('access_token', '')}"
                },
                "contentful": {
                    "test_url": f"https://api.contentful.com/spaces/{connection_config.get('space_id', '')}/entries",
                    "auth_header": f"Bearer {connection_config.get('access_token', '')}"
                },
                "strapi": {
                    "test_url": f"{connection_config.get('base_url', '')}/api/content-types",
                    "auth_header": f"Bearer {connection_config.get('api_token', '')}"
                }
            }
            
            config = platform_configs.get(platform_name.lower())
            if not config:
                return {
                    "success": False,
                    "error": f"Unsupported platform: {platform_name}",
                    "connection_status": "failed"
                }
            
            # Test connection with actual API call
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": config["auth_header"]}
                try:
                    async with session.get(config["test_url"], headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status in [200, 201]:
                            # Get platform capabilities from response
                            capabilities = await self._get_platform_capabilities(platform_name, response)
                            
                            return {
                                "success": True,
                                "connection_status": "connected",
                                "supported_features": capabilities["features"],
                                "platform_capabilities": capabilities["capabilities"],
                                "response_time": response.headers.get("X-Response-Time", "unknown")
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"Connection failed with status {response.status}",
                                "connection_status": "failed"
                            }
                except asyncio.TimeoutError:
                    return {
                        "success": False,
                        "error": "Connection timeout",
                        "connection_status": "timeout"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Connection error: {str(e)}",
                        "connection_status": "error"
                    }
                    
        except Exception as e:
            logger.error(f"Platform connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "connection_status": "error"
            }
    
    async def _get_platform_capabilities(self, platform_name: str, response) -> Dict[str, Any]:
        """Get platform capabilities from API response"""
        try:
            response_data = await response.json()
            
            # Platform-specific capability detection
            capabilities_map = {
                "wordpress": {
                    "features": ["publish", "sync", "metadata", "media_upload", "categories", "tags"],
                    "capabilities": {
                        "content_types": ["post", "page", "product", "custom_post_type"],
                        "media_support": True,
                        "seo_features": True,
                        "scheduling": True,
                        "taxonomies": True,
                        "custom_fields": True
                    }
                },
                "shopify": {
                    "features": ["publish", "sync", "metadata", "media_upload", "inventory", "pricing"],
                    "capabilities": {
                        "content_types": ["product", "collection", "page", "blog_post"],
                        "media_support": True,
                        "seo_features": True,
                        "scheduling": True,
                        "inventory_management": True,
                        "variant_support": True
                    }
                },
                "contentful": {
                    "features": ["publish", "sync", "metadata", "media_upload", "localization", "versioning"],
                    "capabilities": {
                        "content_types": ["entry", "asset"],
                        "media_support": True,
                        "seo_features": True,
                        "scheduling": True,
                        "localization": True,
                        "content_modeling": True
                    }
                },
                "strapi": {
                    "features": ["publish", "sync", "metadata", "media_upload", "users", "permissions"],
                    "capabilities": {
                        "content_types": ["collection", "single_type"],
                        "media_support": True,
                        "seo_features": True,
                        "scheduling": True,
                        "user_management": True,
                        "role_based_access": True
                    }
                }
            }
            
            return capabilities_map.get(platform_name.lower(), {
                "features": ["publish", "sync", "metadata"],
                "capabilities": {
                    "content_types": ["content"],
                    "media_support": False,
                    "seo_features": False,
                    "scheduling": False
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to get platform capabilities: {e}")
            return {
                "features": ["publish", "sync"],
                "capabilities": {
                    "content_types": ["content"],
                    "media_support": False,
                    "seo_features": False,
                    "scheduling": False
                }
            }
    
    async def _store_connection_config(
        self, user_id: int, platform_name: str, connection_config: Dict[str, Any], platform_type: str
    ) -> str:
        """Store connection configuration"""
        try:
            from core.platforms.platform_credentials import PlatformCredentialsManager
            
            # Store connection config securely
            credentials_manager = PlatformCredentialsManager()
            connection_id = f"conn_{user_id}_{platform_name}_{int(datetime.utcnow().timestamp())}"
            
            # Store encrypted credentials
            await credentials_manager.add_platform_credentials(
                platform_name=platform_name,
                credentials=connection_config,
                user_id=str(user_id)
            )
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to store connection config: {e}")
            return f"conn_{user_id}_{platform_name}_{int(datetime.utcnow().timestamp())}"
    
    async def _get_connection_config(self, user_id: int, platform_name: str) -> Dict[str, Any]:
        """Get stored connection configuration"""
        try:
            from core.platforms.platform_credentials import PlatformCredentialsManager
            
            # Retrieve stored connection config
            credentials_manager = PlatformCredentialsManager()
            credentials = await credentials_manager.get_platform_credentials(
                platform_name=platform_name,
                user_id=str(user_id)
            )
            
            if credentials:
                return {
                    "user_id": user_id,
                    "platform_name": platform_name,
                    "connection_id": f"conn_{user_id}_{platform_name}",
                    **credentials
                }
            else:
                return {
                    "user_id": user_id,
                    "platform_name": platform_name,
                    "connection_id": f"conn_{user_id}_{platform_name}",
                    "error": "No credentials found"
                }
                
        except Exception as e:
            logger.error(f"Failed to get connection config: {e}")
            return {
                "user_id": user_id,
                "platform_name": platform_name,
                "connection_id": f"conn_{user_id}_{platform_name}",
                "error": str(e)
            }
    
    async def _prepare_content_for_platform(
        self, content_piece: ShakesContentPiece, platform_name: str, publishing_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare content for platform publishing"""
        try:
            # Platform-specific content preparation
            platform_preparers = {
                "wordpress": self._prepare_wordpress_content,
                "shopify": self._prepare_shopify_content,
                "contentful": self._prepare_contentful_content,
                "strapi": self._prepare_strapi_content
            }
            
            preparer = platform_preparers.get(platform_name.lower())
            if preparer:
                return await preparer(content_piece, publishing_options)
            else:
                # Generic preparation
                return {
                    "title": content_piece.title,
                    "content": content_piece.content,
                    "content_type": content_piece.content_type,
                    "platform": platform_name,
                    "publishing_options": publishing_options,
                    "metadata": {
                        "word_count": content_piece.word_count,
                        "reading_time": content_piece.reading_time,
                        "created_at": content_piece.created_at.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to prepare content for platform: {e}")
            return {
                "title": content_piece.title,
                "content": content_piece.content,
                "content_type": content_piece.content_type,
                "platform": platform_name,
                "publishing_options": publishing_options,
                "error": str(e)
            }
    
    async def _prepare_wordpress_content(self, content_piece: ShakesContentPiece, publishing_options: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for WordPress"""
        return {
            "title": content_piece.title,
            "content": content_piece.content,
            "status": publishing_options.get("status", "draft"),
            "format": publishing_options.get("format", "standard"),
            "categories": publishing_options.get("categories", []),
            "tags": publishing_options.get("tags", []),
            "featured_media": publishing_options.get("featured_media"),
            "excerpt": content_piece.content[:150] + "..." if len(content_piece.content) > 150 else content_piece.content,
            "meta": {
                "word_count": content_piece.word_count,
                "reading_time": content_piece.reading_time
            }
        }
    
    async def _prepare_shopify_content(self, content_piece: ShakesContentPiece, publishing_options: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for Shopify"""
        return {
            "title": content_piece.title,
            "body_html": content_piece.content,
            "product_type": publishing_options.get("product_type", "content"),
            "vendor": publishing_options.get("vendor", "Shakes"),
            "tags": publishing_options.get("tags", []),
            "published": publishing_options.get("published", False),
            "seo": {
                "title": content_piece.title,
                "description": content_piece.content[:160] + "..." if len(content_piece.content) > 160 else content_piece.content
            }
        }
    
    async def _prepare_contentful_content(self, content_piece: ShakesContentPiece, publishing_options: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for Contentful"""
        return {
            "fields": {
                "title": {"en-US": content_piece.title},
                "content": {"en-US": content_piece.content},
                "contentType": {"en-US": content_piece.content_type},
                "wordCount": {"en-US": content_piece.word_count},
                "readingTime": {"en-US": content_piece.reading_time}
            },
            "metadata": {
                "tags": publishing_options.get("tags", [])
            }
        }
    
    async def _prepare_strapi_content(self, content_piece: ShakesContentPiece, publishing_options: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for Strapi"""
        return {
            "data": {
                "title": content_piece.title,
                "content": content_piece.content,
                "content_type": content_piece.content_type,
                "publishedAt": publishing_options.get("published_at"),
                "word_count": content_piece.word_count,
                "reading_time": content_piece.reading_time,
                "tags": publishing_options.get("tags", [])
            }
        }
    
    async def _publish_to_platform(
        self, platform_name: str, prepared_content: Dict[str, Any], publishing_options: Dict[str, Any], connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish content to platform"""
        try:
            import aiohttp
            
            # Platform-specific publishing endpoints
            platform_endpoints = {
                "wordpress": f"{connection_config.get('base_url', '')}/wp-json/wp/v2/posts",
                "shopify": f"{connection_config.get('shop_url', '')}/admin/api/2023-10/products.json",
                "contentful": f"https://api.contentful.com/spaces/{connection_config.get('space_id', '')}/entries",
                "strapi": f"{connection_config.get('base_url', '')}/api/content-types"
            }
            
            endpoint = platform_endpoints.get(platform_name.lower())
            if not endpoint:
                return {
                    "success": False,
                    "error": f"Unsupported platform: {platform_name}"
                }
            
            # Prepare authentication headers
            auth_headers = self._get_auth_headers(platform_name, connection_config)
            
            # Make API call to publish content
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=prepared_content, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status in [200, 201]:
                        response_data = await response.json()
                        
                        # Extract platform-specific response data
                        result = self._extract_publish_result(platform_name, response_data)
                        result["success"] = True
                        result["status"] = "published"
                        
                        return result
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Publishing failed with status {response.status}: {error_text}",
                            "status": "failed"
                        }
                        
        except Exception as e:
            logger.error(f"Failed to publish to platform: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    def _get_auth_headers(self, platform_name: str, connection_config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers for platform"""
        headers = {"Content-Type": "application/json"}
        
        if platform_name.lower() == "wordpress":
            headers["Authorization"] = f"Bearer {connection_config.get('api_key', '')}"
        elif platform_name.lower() == "shopify":
            headers["X-Shopify-Access-Token"] = connection_config.get('access_token', '')
        elif platform_name.lower() == "contentful":
            headers["Authorization"] = f"Bearer {connection_config.get('access_token', '')}"
        elif platform_name.lower() == "strapi":
            headers["Authorization"] = f"Bearer {connection_config.get('api_token', '')}"
        
        return headers
    
    def _extract_publish_result(self, platform_name: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract publish result from platform response"""
        if platform_name.lower() == "wordpress":
            return {
                "url": response_data.get("link", ""),
                "post_id": str(response_data.get("id", "")),
                "status": response_data.get("status", "published")
            }
        elif platform_name.lower() == "shopify":
            product = response_data.get("product", {})
            return {
                "url": f"https://{connection_config.get('shop_url', '')}/products/{product.get('handle', '')}",
                "post_id": str(product.get("id", "")),
                "status": "published" if product.get("published", False) else "draft"
            }
        elif platform_name.lower() == "contentful":
            return {
                "url": f"https://app.contentful.com/spaces/{connection_config.get('space_id', '')}/entries/{response_data.get('sys', {}).get('id', '')}",
                "post_id": response_data.get("sys", {}).get("id", ""),
                "status": "published"
            }
        elif platform_name.lower() == "strapi":
            return {
                "url": f"{connection_config.get('base_url', '')}/api/content-types/{response_data.get('data', {}).get('id', '')}",
                "post_id": str(response_data.get("data", {}).get("id", "")),
                "status": "published"
            }
        else:
            return {
                "url": "",
                "post_id": "",
                "status": "published"
            }
    
    async def _fetch_content_from_platform(
        self, platform_name: str, sync_options: Dict[str, Any], connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch content from platform"""
        try:
            import aiohttp
            
            # Platform-specific fetch endpoints
            platform_endpoints = {
                "wordpress": f"{connection_config.get('base_url', '')}/wp-json/wp/v2/posts",
                "shopify": f"{connection_config.get('shop_url', '')}/admin/api/2023-10/products.json",
                "contentful": f"https://api.contentful.com/spaces/{connection_config.get('space_id', '')}/entries",
                "strapi": f"{connection_config.get('base_url', '')}/api/content-types"
            }
            
            endpoint = platform_endpoints.get(platform_name.lower())
            if not endpoint:
                return {
                    "success": False,
                    "error": f"Unsupported platform: {platform_name}"
                }
            
            # Prepare query parameters
            params = self._build_fetch_params(platform_name, sync_options)
            
            # Prepare authentication headers
            auth_headers = self._get_auth_headers(platform_name, connection_config)
            
            # Make API call to fetch content
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, params=params, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # Transform platform-specific response to standard format
                        content = self._transform_platform_content(platform_name, response_data)
                        
                        return {
                            "success": True,
                            "content": content,
                            "total_count": len(content),
                            "sync_timestamp": datetime.utcnow().isoformat(),
                            "platform": platform_name
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Fetch failed with status {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Failed to fetch content from platform: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_fetch_params(self, platform_name: str, sync_options: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for platform content fetching"""
        params = {}
        
        if platform_name.lower() == "wordpress":
            params.update({
                "per_page": sync_options.get("limit", 10),
                "page": sync_options.get("page", 1),
                "status": sync_options.get("status", "publish"),
                "orderby": sync_options.get("orderby", "date"),
                "order": sync_options.get("order", "desc")
            })
        elif platform_name.lower() == "shopify":
            params.update({
                "limit": sync_options.get("limit", 10),
                "page": sync_options.get("page", 1),
                "status": sync_options.get("status", "active"),
                "published_status": sync_options.get("published_status", "published")
            })
        elif platform_name.lower() == "contentful":
            params.update({
                "limit": sync_options.get("limit", 10),
                "skip": sync_options.get("skip", 0),
                "order": sync_options.get("order", "-sys.createdAt"),
                "content_type": sync_options.get("content_type", "")
            })
        elif platform_name.lower() == "strapi":
            params.update({
                "pagination[limit]": sync_options.get("limit", 10),
                "pagination[page]": sync_options.get("page", 1),
                "sort": sync_options.get("sort", "createdAt:desc"),
                "filters": sync_options.get("filters", {})
            })
        
        return params
    
    def _transform_platform_content(self, platform_name: str, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform platform-specific response to standard format"""
        content = []
        
        if platform_name.lower() == "wordpress":
            posts = response_data if isinstance(response_data, list) else response_data.get("posts", [])
            for post in posts:
                content.append({
                    "id": str(post.get("id", "")),
                    "title": post.get("title", {}).get("rendered", ""),
                    "content": post.get("content", {}).get("rendered", ""),
                    "excerpt": post.get("excerpt", {}).get("rendered", ""),
                    "status": post.get("status", ""),
                    "created_at": post.get("date", ""),
                    "updated_at": post.get("modified", ""),
                    "author": post.get("author", ""),
                    "categories": [cat.get("name", "") for cat in post.get("categories", [])],
                    "tags": [tag.get("name", "") for tag in post.get("tags", [])]
                })
        elif platform_name.lower() == "shopify":
            products = response_data.get("products", [])
            for product in products:
                content.append({
                    "id": str(product.get("id", "")),
                    "title": product.get("title", ""),
                    "content": product.get("body_html", ""),
                    "excerpt": product.get("body_html", "")[:200] + "..." if len(product.get("body_html", "")) > 200 else product.get("body_html", ""),
                    "status": "published" if product.get("published", False) else "draft",
                    "created_at": product.get("created_at", ""),
                    "updated_at": product.get("updated_at", ""),
                    "vendor": product.get("vendor", ""),
                    "product_type": product.get("product_type", ""),
                    "tags": product.get("tags", "").split(",") if product.get("tags") else []
                })
        elif platform_name.lower() == "contentful":
            entries = response_data.get("items", [])
            for entry in entries:
                fields = entry.get("fields", {})
                content.append({
                    "id": entry.get("sys", {}).get("id", ""),
                    "title": fields.get("title", ""),
                    "content": fields.get("content", ""),
                    "excerpt": fields.get("excerpt", ""),
                    "status": "published",
                    "created_at": entry.get("sys", {}).get("createdAt", ""),
                    "updated_at": entry.get("sys", {}).get("updatedAt", ""),
                    "content_type": entry.get("sys", {}).get("contentType", {}).get("sys", {}).get("id", "")
                })
        elif platform_name.lower() == "strapi":
            entries = response_data.get("data", [])
            for entry in entries:
                content.append({
                    "id": str(entry.get("id", "")),
                    "title": entry.get("attributes", {}).get("title", ""),
                    "content": entry.get("attributes", {}).get("content", ""),
                    "excerpt": entry.get("attributes", {}).get("excerpt", ""),
                    "status": "published" if entry.get("attributes", {}).get("publishedAt") else "draft",
                    "created_at": entry.get("attributes", {}).get("createdAt", ""),
                    "updated_at": entry.get("attributes", {}).get("updatedAt", ""),
                    "published_at": entry.get("attributes", {}).get("publishedAt", "")
                })
        
        return content
    
    async def _process_synced_content(
        self, user_id: int, platform_name: str, platform_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process and store synced content"""
        try:
            db = await get_shakes_database()
            processed_content = []
            
            async with db.get_session() as session:
                for item in platform_content:
                    # Create or update content piece
                    content_piece = ShakesContentPiece(
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        content_type=item.get("content_type", "article"),
                        word_count=len(item.get("content", "").split()),
                        reading_time=max(1, len(item.get("content", "").split()) // 200),
                        project_id=1,  # Default project for synced content
                        user_id=user_id,
                        status="synced",
                        metadata={
                            "original_id": item.get("id", ""),
                            "platform": platform_name,
                            "synced_at": datetime.utcnow().isoformat(),
                            "original_created_at": item.get("created_at", ""),
                            "original_updated_at": item.get("updated_at", ""),
                            "platform_metadata": {
                                "excerpt": item.get("excerpt", ""),
                                "status": item.get("status", ""),
                                "author": item.get("author", ""),
                                "categories": item.get("categories", []),
                                "tags": item.get("tags", [])
                            }
                        }
                    )
                    
                    session.add(content_piece)
                    await session.flush()  # Get the ID
                    
                    processed_content.append({
                        "content_piece_id": content_piece.id,
                        "original_id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "platform": platform_name,
                        "synced_at": datetime.utcnow().isoformat(),
                        "status": "processed"
                    })
                
                await session.commit()
                return processed_content
                
        except Exception as e:
            logger.error(f"Failed to process synced content: {e}")
            return []
    
    async def _get_platform_structure(
        self, platform_name: str, connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get platform structure and capabilities"""
        try:
            import aiohttp
            
            # Platform-specific structure endpoints
            structure_endpoints = {
                "wordpress": f"{connection_config.get('base_url', '')}/wp-json/wp/v2/types",
                "shopify": f"{connection_config.get('shop_url', '')}/admin/api/2023-10/metafields.json",
                "contentful": f"https://api.contentful.com/spaces/{connection_config.get('space_id', '')}/content_types",
                "strapi": f"{connection_config.get('base_url', '')}/api/content-types"
            }
            
            endpoint = structure_endpoints.get(platform_name.lower())
            if not endpoint:
                return self._get_default_platform_structure(platform_name)
            
            # Prepare authentication headers
            auth_headers = self._get_auth_headers(platform_name, connection_config)
            
            # Make API call to get platform structure
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return self._parse_platform_structure(platform_name, response_data)
                    else:
                        logger.warning(f"Failed to get platform structure, using defaults: {response.status}")
                        return self._get_default_platform_structure(platform_name)
                        
        except Exception as e:
            logger.error(f"Failed to get platform structure: {e}")
            return self._get_default_platform_structure(platform_name)
    
    def _get_default_platform_structure(self, platform_name: str) -> Dict[str, Any]:
        """Get default platform structure when API call fails"""
        default_structures = {
            "wordpress": {
                "platform_name": platform_name,
                "supported_content_types": ["post", "page", "product", "custom_post_type"],
                "supported_features": ["seo", "media", "scheduling", "analytics", "categories", "tags"],
                "content_fields": ["title", "content", "excerpt", "tags", "categories", "featured_media"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete"]
            },
            "shopify": {
                "platform_name": platform_name,
                "supported_content_types": ["product", "collection", "page", "blog_post"],
                "supported_features": ["seo", "media", "scheduling", "inventory", "pricing", "variants"],
                "content_fields": ["title", "body_html", "product_type", "vendor", "tags"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete"]
            },
            "contentful": {
                "platform_name": platform_name,
                "supported_content_types": ["entry", "asset"],
                "supported_features": ["seo", "media", "scheduling", "localization", "versioning"],
                "content_fields": ["title", "content", "excerpt", "tags", "metadata"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete", "publish"]
            },
            "strapi": {
                "platform_name": platform_name,
                "supported_content_types": ["collection", "single_type"],
                "supported_features": ["seo", "media", "scheduling", "users", "permissions"],
                "content_fields": ["title", "content", "excerpt", "tags", "metadata"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete", "publish"]
            }
        }
        
        return default_structures.get(platform_name.lower(), {
            "platform_name": platform_name,
            "supported_content_types": ["content"],
            "supported_features": ["basic"],
            "content_fields": ["title", "content"],
            "media_support": False,
            "api_capabilities": ["read", "write"]
        })
    
    def _parse_platform_structure(self, platform_name: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse platform-specific structure response"""
        if platform_name.lower() == "wordpress":
            content_types = list(response_data.keys()) if isinstance(response_data, dict) else []
            return {
                "platform_name": platform_name,
                "supported_content_types": content_types,
                "supported_features": ["seo", "media", "scheduling", "analytics", "categories", "tags"],
                "content_fields": ["title", "content", "excerpt", "tags", "categories", "featured_media"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete"],
                "raw_structure": response_data
            }
        elif platform_name.lower() == "shopify":
            metafields = response_data.get("metafields", [])
            return {
                "platform_name": platform_name,
                "supported_content_types": ["product", "collection", "page", "blog_post"],
                "supported_features": ["seo", "media", "scheduling", "inventory", "pricing", "variants"],
                "content_fields": ["title", "body_html", "product_type", "vendor", "tags"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete"],
                "metafields_count": len(metafields)
            }
        elif platform_name.lower() == "contentful":
            content_types = response_data.get("items", [])
            return {
                "platform_name": platform_name,
                "supported_content_types": [ct.get("sys", {}).get("id", "") for ct in content_types],
                "supported_features": ["seo", "media", "scheduling", "localization", "versioning"],
                "content_fields": ["title", "content", "excerpt", "tags", "metadata"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete", "publish"],
                "content_types_count": len(content_types)
            }
        elif platform_name.lower() == "strapi":
            content_types = response_data.get("data", [])
            return {
                "platform_name": platform_name,
                "supported_content_types": [ct.get("attributes", {}).get("name", "") for ct in content_types],
                "supported_features": ["seo", "media", "scheduling", "users", "permissions"],
                "content_fields": ["title", "content", "excerpt", "tags", "metadata"],
                "media_support": True,
                "api_capabilities": ["read", "write", "update", "delete", "publish"],
                "content_types_count": len(content_types)
            }
        else:
            return self._get_default_platform_structure(platform_name)
    
    def _create_integration_guidelines_prompt(
        self, platform_name: str, platform_type: str, connection_config: Dict[str, Any]
    ) -> str:
        """Create prompt for integration guidelines"""
        return f"""
        Create integration guidelines for {platform_name}:
        
        Platform Type: {platform_type}
        Connection Config: {connection_config}
        
        Include:
        1. Platform-specific content requirements
        2. Publishing best practices
        3. Content formatting guidelines
        4. Media handling instructions
        5. SEO optimization tips
        6. Performance considerations
        7. Troubleshooting guide
        
        Format as comprehensive integration guidelines.
        """
    
    def _create_platform_insights_prompt(
        self, platform_name: str, platform_structure: Dict[str, Any]
    ) -> str:
        """Create prompt for platform insights"""
        return f"""
        Provide insights for {platform_name} platform:
        
        Platform Structure: {platform_structure}
        
        Include:
        1. Platform capabilities overview
        2. Content optimization opportunities
        3. Best practices for this platform
        4. Integration advantages
        5. Potential limitations
        6. Optimization recommendations
        
        Format as comprehensive platform insights.
        """
    
    def _create_platform_optimization_prompt(
        self, content_piece: ShakesContentPiece, platform_name: str, platform_structure: Dict[str, Any], optimization_goals: List[str]
    ) -> str:
        """Create prompt for platform optimization"""
        return f"""
        Optimize this content for {platform_name}:
        
        Content: {content_piece.title}
        Original Content: {content_piece.content}
        Platform Structure: {platform_structure}
        Optimization Goals: {', '.join(optimization_goals)}
        
        Requirements:
        1. Adapt content for platform requirements
        2. Optimize for platform-specific features
        3. Ensure content meets platform standards
        4. Apply optimization goals
        5. Maintain content quality and message
        
        Generate the optimized content.
        """
    
    def _create_optimization_recommendations_prompt(
        self, content_piece: ShakesContentPiece, platform_name: str, optimization_goals: List[str], optimized_content: str
    ) -> str:
        """Create prompt for optimization recommendations"""
        return f"""
        Provide optimization recommendations for {platform_name}:
        
        Original Content: {content_piece.title}
        Optimized Content: {optimized_content}
        Optimization Goals: {', '.join(optimization_goals)}
        
        Provide:
        1. Key optimizations made
        2. Platform-specific improvements
        3. Additional optimization opportunities
        4. Best practices for this platform
        5. Performance enhancement tips
        6. Future optimization suggestions
        
        Format as actionable optimization recommendations.
        """
