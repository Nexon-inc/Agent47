from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AriaCampaign, AriaSocialAccount, AriaBrandProfile
from core.ai import get_ai_service_manager, AIServiceManager


class GeoCampaignService:
    """Service for creating geo-specific campaigns targeting specific regions"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Comprehensive list of African countries and major cities
        self.african_regions = {
            "kenya": {
                "country": "Kenya",
                "cities": ["nairobi", "mombasa", "kisumu", "nakuru", "eldoret", "thika", "kakamega", "kericho"],
                "languages": ["swahili", "english"],
                "timezone": "Africa/Nairobi",
                "popular_hashtags": ["#kenya", "#nairobi", "#mombasa", "#kenyans", "#kenyantiktok", "#nairobi", "#mombasa"],
                "cultural_context": "East African culture, Swahili heritage, tech innovation hub"
            },
            "nigeria": {
                "country": "Nigeria",
                "cities": ["lagos", "abuja", "kano", "ibadan", "port harcourt", "benin city", "calabar", "enugu", "kaduna"],
                "languages": ["english", "hausa", "yoruba", "igbo"],
                "timezone": "Africa/Lagos",
                "popular_hashtags": ["#nigeria", "#lagos", "#nigerians", "#naijatiktok", "#lagosvibes", "#abuja", "#kano"],
                "cultural_context": "West African culture, diverse ethnic groups, Nollywood influence"
            },
            "south_africa": {
                "country": "South Africa",
                "cities": ["johannesburg", "cape town", "durban", "pretoria", "port elizabeth", "bloemfontein", "east london", "kimberley"],
                "languages": ["english", "afrikaans", "zulu", "xhosa"],
                "timezone": "Africa/Johannesburg",
                "popular_hashtags": ["#southafrica", "#capetown", "#joburg", "#durban", "#southafricantiktok", "#pretoria"],
                "cultural_context": "Rainbow nation, diverse cultures, modern African metropolis"
            },
            "ghana": {
                "country": "Ghana",
                "cities": ["accra", "kumasi", "tamale", "sekondi", "sunyani", "cape coast", "ho", "wa", "bolgatanga"],
                "languages": ["english", "twi", "ga", "ewe"],
                "timezone": "Africa/Accra",
                "popular_hashtags": ["#ghana", "#accra", "#ghanaians", "#ghanatiktok", "#ghanavibes", "#kumasi"],
                "cultural_context": "West African culture, Ashanti heritage, pan-African leadership"
            },
            "ethiopia": {
                "country": "Ethiopia",
                "cities": ["addis ababa", "dire dawa", "mekelle", "gondar", "bahir dar", "hawassa", "jimma", "harar"],
                "languages": ["amharic", "english", "oromo"],
                "timezone": "Africa/Addis_Ababa",
                "popular_hashtags": ["#ethiopia", "#addisababa", "#ethiopians", "#ethiopiatiktok", "#addisvibes"],
                "cultural_context": "East African culture, ancient civilization, coffee culture"
            },
            "uganda": {
                "country": "Uganda",
                "cities": ["kampala", "jinja", "mbale", "gulu", "entebbe", "masaka", "mbarara", "kasese"],
                "languages": ["english", "luganda", "swahili"],
                "timezone": "Africa/Kampala",
                "popular_hashtags": ["#uganda", "#kampala", "#ugandans", "#ugandatiktok", "#kampalavibes"],
                "cultural_context": "East African culture, Pearl of Africa, diverse ethnic groups"
            },
            "tanzania": {
                "country": "Tanzania",
                "cities": ["dar es salaam", "dodoma", "mwanza", "arusha", "mbeya", "tanga", "morogoro", "songea"],
                "languages": ["swahili", "english"],
                "timezone": "Africa/Dar_es_Salaam",
                "popular_hashtags": ["#tanzania", "#darelsalaam", "#tanzanians", "#tanzaniatiktok", "#darswahili"],
                "cultural_context": "East African culture, Swahili heartland, wildlife tourism"
            },
            "rwanda": {
                "country": "Rwanda",
                "cities": ["kigali", "butare", "ruhengeri", "gisenyi", "byumba", "cyangugu", "kibuye", "kibungo"],
                "languages": ["kinyarwanda", "french", "english"],
                "timezone": "Africa/Kigali",
                "popular_hashtags": ["#rwanda", "#kigali", "#rwandans", "#rwandatiktok", "#kigalivibes"],
                "cultural_context": "East African culture, land of a thousand hills, innovation hub"
            },
            "egypt": {
                "country": "Egypt",
                "cities": ["cairo", "alexandria", "giza", "sharm el sheikh", "luxor", "aswan", "hurghada", "dahab"],
                "languages": ["arabic", "english"],
                "timezone": "Africa/Cairo",
                "popular_hashtags": ["#egypt", "#cairo", "#egyptians", "#egypttiktok", "#cairovibes", "#alexandria"],
                "cultural_context": "Ancient civilization, Arab culture, Mediterranean influence"
            },
            "morocco": {
                "country": "Morocco",
                "cities": ["casablanca", "rabat", "marrakech", "fes", "tangier", "agadir", "oujda", "tetouan"],
                "languages": ["arabic", "french", "berber"],
                "timezone": "Africa/Casablanca",
                "popular_hashtags": ["#morocco", "#casablanca", "#marrakech", "#moroccantiktok", "#moroccovibes"],
                "cultural_context": "North African culture, Berber heritage, French colonial influence"
            },
            "senegal": {
                "country": "Senegal",
                "cities": ["dakar", "thies", "kaolack", "ziguinchor", "saint louis", "touba", "diourbel", "fatick"],
                "languages": ["french", "wolof", "serer"],
                "timezone": "Africa/Dakar",
                "popular_hashtags": ["#senegal", "#dakar", "#senegalese", "#senegaltiktok", "#dakarvibes"],
                "cultural_context": "West African culture, French influence, vibrant music scene"
            },
            "ivory_coast": {
                "country": "Ivory Coast",
                "cities": ["abidjan", "yamoussoukro", "bouake", "san pedro", "korhogo", "man", "gagnoa", "abengourou"],
                "languages": ["french", "baoule", "dioula"],
                "timezone": "Africa/Abidjan",
                "popular_hashtags": ["#ivorycoast", "#abidjan", "#ivoiriens", "#cotedivoiretiktok", "#abidjanvibes"],
                "cultural_context": "West African culture, French colonial heritage, economic hub"
            },
            "cameroon": {
                "country": "Cameroon",
                "cities": ["yaounde", "douala", "bamenda", "bafoussam", "garoua", "maroua", "kribi", "kousseri"],
                "languages": ["french", "english", "cameroonian pidgin"],
                "timezone": "Africa/Douala",
                "popular_hashtags": ["#cameroon", "#yaounde", "#douala", "#cameroonians", "#cameroontiktok"],
                "cultural_context": "Central African culture, bilingual heritage, diverse ethnic groups"
            },
            "zimbabwe": {
                "country": "Zimbabwe",
                "cities": ["harare", "bulawayo", "chitungwiza", "mutare", "epworth", "gweru", "kwekwe", "kadoma"],
                "languages": ["english", "shona", "ndebele"],
                "timezone": "Africa/Harare",
                "popular_hashtags": ["#zimbabwe", "#harare", "#zimbabweans", "#zimbabwetiktok", "#hararevibes"],
                "cultural_context": "Southern African culture, Shona heritage, agricultural traditions"
            },
            "zambia": {
                "country": "Zambia",
                "cities": ["lusaka", "kitwe", "ndola", "kabwe", "chililabombwe", "mufulira", "luanshya", "chingola"],
                "languages": ["english", "bemba", "tonga"],
                "timezone": "Africa/Lusaka",
                "popular_hashtags": ["#zambia", "#lusaka", "#zambians", "#zambiatiktok", "#lusakavibes"],
                "cultural_context": "Southern African culture, copper mining heritage, diverse ethnic groups"
            },
            "botswana": {
                "country": "Botswana",
                "cities": ["gaborone", "francistown", "maun", "selebi phikwe", "serowe", "kanye", "molepolole", "mahalapye"],
                "languages": ["english", "tswana"],
                "timezone": "Africa/Gaborone",
                "popular_hashtags": ["#botswana", "#gaborone", "#batswana", "#botswanatiktok", "#gaboronevibes"],
                "cultural_context": "Southern African culture, Tswana heritage, diamond mining economy"
            },
            "namibia": {
                "country": "Namibia",
                "cities": ["windhoek", "walvis bay", "oshakati", "rundu", "katima mulilo", "otjiwarongo", "keetmanshoop", "luderitz"],
                "languages": ["english", "afrikaans", "oshivambo"],
                "timezone": "Africa/Windhoek",
                "popular_hashtags": ["#namibia", "#windhoek", "#namibians", "#namibiatiktok", "#windhoekvibes"],
                "cultural_context": "Southern African culture, German colonial influence, desert landscapes"
            },
            "mozambique": {
                "country": "Mozambique",
                "cities": ["maputo", "beira", "nampula", "chimoio", "nacala", "quelimane", "tete", "xai-xai"],
                "languages": ["portuguese", "makhuwa", "sena"],
                "timezone": "Africa/Maputo",
                "popular_hashtags": ["#mozambique", "#maputo", "#mozambicans", "#mozambiquetiktok", "#maputovibes"],
                "cultural_context": "Southern African culture, Portuguese colonial heritage, coastal traditions"
            },
            "angola": {
                "country": "Angola",
                "cities": ["luanda", "huambo", "lobito", "benguela", "lubango", "malanje", "namibe", "soyo"],
                "languages": ["portuguese", "umbundu", "kimbundu"],
                "timezone": "Africa/Luanda",
                "popular_hashtags": ["#angola", "#luanda", "#angolans", "#angolatiktok", "#luandavibes"],
                "cultural_context": "Southern African culture, Portuguese colonial heritage, oil economy"
            },
            "madagascar": {
                "country": "Madagascar",
                "cities": ["antananarivo", "toamasina", "antsirabe", "fianarantsoa", "mahajanga", "toliara", "antsohihy", "ambovombe"],
                "languages": ["malagasy", "french"],
                "timezone": "Indian/Antananarivo",
                "popular_hashtags": ["#madagascar", "#antananarivo", "#malagasy", "#madagascartiktok", "#tana"],
                "cultural_context": "Island culture, unique biodiversity, Malagasy heritage"
            },
            "mauritius": {
                "country": "Mauritius",
                "cities": ["port louis", "beau bassin", "curepipe", "quatre bornes", "vacoas", "phoenix", "rose hill", "triolet"],
                "languages": ["english", "french", "creole"],
                "timezone": "Indian/Mauritius",
                "popular_hashtags": ["#mauritius", "#portlouis", "#mauritians", "#mauritiustiktok", "#mauritiusvibes"],
                "cultural_context": "Island culture, multicultural heritage, tourism economy"
            },
            "seychelles": {
                "country": "Seychelles",
                "cities": ["victoria", "anse boileau", "anse royale", "beau vallon", "cascade", "takamaka", "grand anse", "port glaud"],
                "languages": ["english", "french", "creole"],
                "timezone": "Indian/Mahe",
                "popular_hashtags": ["#seychelles", "#victoria", "#seychellois", "#seychellestiktok", "#seychellesvibes"],
                "cultural_context": "Island paradise, Creole culture, luxury tourism"
            }
        }
        
        # Global regions for broader targeting
        self.global_regions = {
            "north_america": {
                "countries": ["united states", "canada", "mexico"],
                "cities": ["new york", "los angeles", "toronto", "mexico city", "chicago", "vancouver", "montreal", "houston"],
                "timezone": "America/New_York",
                "popular_hashtags": ["#usa", "#canada", "#mexico", "#northamerica", "#nyc", "#la", "#toronto"],
                "cultural_context": "Western culture, diverse populations, tech innovation"
            },
            "europe": {
                "countries": ["united kingdom", "germany", "france", "italy", "spain", "netherlands", "sweden", "norway"],
                "cities": ["london", "berlin", "paris", "rome", "madrid", "amsterdam", "stockholm", "oslo"],
                "timezone": "Europe/London",
                "popular_hashtags": ["#europe", "#uk", "#germany", "#france", "#italy", "#spain", "#netherlands"],
                "cultural_context": "European culture, diverse languages, rich history"
            },
            "asia": {
                "countries": ["china", "japan", "south korea", "india", "singapore", "thailand", "vietnam", "malaysia"],
                "cities": ["beijing", "tokyo", "seoul", "mumbai", "singapore", "bangkok", "ho chi minh city", "kuala lumpur"],
                "timezone": "Asia/Tokyo",
                "popular_hashtags": ["#asia", "#china", "#japan", "#korea", "#india", "#singapore", "#thailand"],
                "cultural_context": "Asian cultures, diverse traditions, tech innovation"
            },
            "south_america": {
                "countries": ["brazil", "argentina", "colombia", "peru", "chile", "ecuador", "uruguay", "paraguay"],
                "cities": ["sao paulo", "buenos aires", "bogota", "lima", "santiago", "quito", "montevideo", "asuncion"],
                "timezone": "America/Sao_Paulo",
                "popular_hashtags": ["#southamerica", "#brazil", "#argentina", "#colombia", "#peru", "#chile"],
                "cultural_context": "Latin American culture, diverse landscapes, rich traditions"
            },
            "oceania": {
                "countries": ["australia", "new zealand", "fiji", "papua new guinea", "samoa", "tonga", "vanuatu", "solomon islands"],
                "cities": ["sydney", "melbourne", "auckland", "suva", "port moresby", "apia", "nuku'alofa", "port vila"],
                "timezone": "Australia/Sydney",
                "popular_hashtags": ["#oceania", "#australia", "#newzealand", "#fiji", "#pacific", "#downunder"],
                "cultural_context": "Pacific culture, indigenous heritage, island traditions"
            },
            "middle_east": {
                "countries": ["saudi arabia", "uae", "israel", "turkey", "iran", "egypt", "jordan", "lebanon"],
                "cities": ["riyadh", "dubai", "tel aviv", "istanbul", "tehran", "cairo", "amman", "beirut"],
                "timezone": "Asia/Riyadh",
                "popular_hashtags": ["#middleeast", "#saudiarabia", "#uae", "#israel", "#turkey", "#iran"],
                "cultural_context": "Middle Eastern culture, Islamic heritage, modern development"
            }
        }
    
    async def _get_ai_service_manager(self):
        """Get AI service manager"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager
    
    async def create_geo_campaign(
        self,
        brand_id: int,
        target_regions: List[str],
        campaign_type: str,
        content_theme: str,
        budget: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a geo-specific campaign targeting specific regions"""
        try:
            nlp = await self._get_nlp()
            
            # Validate and expand target regions
            expanded_regions = self._expand_target_regions(target_regions)
            
            # Generate campaign strategy
            campaign_strategy = await self._generate_campaign_strategy(
                expanded_regions, campaign_type, content_theme
            )
            
            # Create campaign content variations
            content_variations = await self._create_content_variations(
                expanded_regions, campaign_strategy, content_theme
            )
            
            # Generate hashtag strategies
            hashtag_strategies = self._generate_hashtag_strategies(expanded_regions)
            
            # Create posting schedule
            posting_schedule = self._create_posting_schedule(expanded_regions)
            
            # Create campaign object
            campaign_data = {
                "brand_id": brand_id,
                "name": f"Geo-AriaCampaign: {content_theme} - {', '.join(target_regions)}",
                "description": campaign_strategy["overview"],
                "campaign_type": campaign_type,
                "target_regions": expanded_regions,
                "strategy": campaign_strategy,
                "content_variations": content_variations,
                "hashtag_strategies": hashtag_strategies,
                "posting_schedule": posting_schedule,
                "budget": budget,
                "start_date": start_date or datetime.now(),
                "end_date": end_date or (datetime.now() + timedelta(days=30)),
                "status": "draft"
            }
            
            return {
                "success": True,
                "campaign": campaign_data,
                "message": f"Geo-campaign created successfully for {len(expanded_regions)} regions"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create geo-campaign: {str(e)}"
            }
    
    def _expand_target_regions(self, target_regions: List[str]) -> List[Dict[str, Any]]:
        """Expand target regions to include detailed information"""
        expanded = []
        
        for region in target_regions:
            region_lower = region.lower()
            
            # Check African regions first
            if region_lower in self.african_regions:
                region_info = self.african_regions[region_lower].copy()
                region_info["region_type"] = "african_country"
                expanded.append(region_info)
            
            # Check global regions
            elif region_lower in self.global_regions:
                region_info = self.global_regions[region_lower].copy()
                region_info["region_type"] = "global_region"
                expanded.append(region_info)
            
            # Check if it's a specific city
            else:
                # Search for city in African regions
                for region_data in self.african_regions.values():
                    if region_lower in [city.lower() for city in region_data["cities"]]:
                        city_info = {
                            "city": region_lower.title(),
                            "country": region_data["country"],
                            "region_type": "african_city",
                            "languages": region_data["languages"],
                            "timezone": region_data["timezone"],
                            "popular_hashtags": region_data["popular_hashtags"],
                            "cultural_context": region_data["cultural_context"]
                        }
                        expanded.append(city_info)
                        break
                
                # Search for city in global regions
                for region_data in self.global_regions.values():
                    if region_lower in [city.lower() for city in region_data["cities"]]:
                        city_info = {
                            "city": region_lower.title(),
                            "region_type": "global_city",
                            "timezone": region_data["timezone"],
                            "popular_hashtags": region_data["popular_hashtags"],
                            "cultural_context": region_data["cultural_context"]
                        }
                        expanded.append(city_info)
                        break
                
                # If not found, create generic region
                if not any(exp.get("city") == region_lower.title() for exp in expanded):
                    generic_info = {
                        "region": region_lower.title(),
                        "region_type": "generic",
                        "timezone": "UTC",
                        "popular_hashtags": [f"#{region_lower}"],
                        "cultural_context": "General targeting"
                    }
                    expanded.append(generic_info)
        
        return expanded
    
    async def _generate_campaign_strategy(
        self,
        expanded_regions: List[Dict[str, Any]],
        campaign_type: str,
        content_theme: str
    ) -> Dict[str, Any]:
        """Generate campaign strategy based on target regions"""
        nlp = await self._get_nlp()
        
        # Analyze regional characteristics
        regional_insights = []
        for region in expanded_regions:
            if region["region_type"] == "african_country":
                insights = {
                    "region": region["country"],
                    "cultural_approach": f"Embrace {region['cultural_context']}",
                    "language_strategy": f"Primary: {region['languages'][0]}, Secondary: {', '.join(region['languages'][1:]) if len(region['languages']) > 1 else 'None'}",
                    "timing_strategy": f"Optimize for {region['timezone']} timezone",
                    "content_adaptation": f"Adapt content for {region['cultural_context']}",
                    "engagement_tactics": f"Use local hashtags: {', '.join(region['popular_hashtags'][:3])}"
                }
            elif region["region_type"] == "african_city":
                insights = {
                    "region": f"{region['city']}, {region['country']}",
                    "cultural_approach": f"Focus on {region['city']} urban culture",
                    "language_strategy": f"Primary: {region['languages'][0]}, Secondary: {', '.join(region['languages'][1:]) if len(region['languages']) > 1 else 'None'}",
                    "timing_strategy": f"Optimize for {region['timezone']} timezone",
                    "content_adaptation": f"Urban-focused content for {region['city']}",
                    "engagement_tactics": f"Use city-specific hashtags: {', '.join(region['popular_hashtags'][:3])}"
                }
            else:
                insights = {
                    "region": region.get("region", "Unknown"),
                    "cultural_approach": "General cultural approach",
                    "language_strategy": "English primary",
                    "timing_strategy": "UTC optimization",
                    "content_adaptation": "Standard content adaptation",
                    "engagement_tactics": f"Use general hashtags: {', '.join(region['popular_hashtags'])}"
                }
            
            regional_insights.append(insights)
        
        # Generate AI-powered strategy
        strategy_prompt = f"""
        Create a comprehensive social media campaign strategy for {campaign_type} campaign with theme: {content_theme}
        
        Target regions: {[r.get('country', r.get('city', r.get('region', 'Unknown'))) for r in expanded_regions]}
        
        Regional insights: {regional_insights}
        
        Provide:
        1. AriaCampaign overview
        2. Regional adaptation strategies
        3. Content pillars
        4. Engagement tactics
        5. Success metrics
        6. Cultural considerations
        """
        
        try:
            response = await nlp.generate_text(strategy_prompt)
            strategy_text = response.get("text", "")
        except:
            strategy_text = f"AriaCampaign strategy for {content_theme} targeting {len(expanded_regions)} regions"
        
        return {
            "overview": strategy_text,
            "regional_insights": regional_insights,
            "content_pillars": [
                "Cultural Relevance",
                "Local Language",
                "Regional Trends",
                "Community Engagement",
                "Authentic Storytelling"
            ],
            "engagement_tactics": [
                "Local hashtag usage",
                "Cultural celebration posts",
                "Community spotlights",
                "Regional trend integration",
                "Local influencer collaboration"
            ],
            "success_metrics": [
                "Regional engagement rates",
                "Local hashtag performance",
                "Cultural resonance scores",
                "Community growth",
                "Cross-regional reach"
            ]
        }
    
    async def _create_content_variations(
        self,
        expanded_regions: List[Dict[str, Any]],
        campaign_strategy: Dict[str, Any],
        content_theme: str
    ) -> List[Dict[str, Any]]:
        """Create content variations for different regions"""
        nlp = await self._get_nlp()
        variations = []
        
        for region in expanded_regions:
            if region["region_type"] in ["african_country", "african_city"]:
                # Generate region-specific content
                content_prompt = f"""
                Create social media content for {content_theme} campaign targeting {region.get('country', region.get('city', 'Unknown'))}
                
                Cultural context: {region.get('cultural_context', 'African culture')}
                Languages: {', '.join(region.get('languages', ['English']))}
                Popular hashtags: {', '.join(region.get('popular_hashtags', []))}
                
                Generate:
                1. Caption (primary language)
                2. Caption (secondary language if applicable)
                3. Hashtag strategy
                4. Content adaptation notes
                """
                
                try:
                    response = await nlp.generate_text(content_prompt)
                    content_text = response.get("text", "")
                except:
                    content_text = f"Content for {content_theme} in {region.get('country', region.get('city', 'Unknown'))}"
                
                variation = {
                    "region": region.get("country", region.get("city", "Unknown")),
                    "region_type": region["region_type"],
                    "primary_caption": content_text,
                    "secondary_caption": content_text if len(region.get("languages", [])) > 1 else None,
                    "hashtags": region.get("popular_hashtags", [])[:5],
                    "adaptation_notes": f"Adapt for {region.get('cultural_context', 'local culture')}",
                    "language": region.get("languages", ["English"])[0],
                    "timezone": region.get("timezone", "UTC")
                }
            else:
                # Generic content variation
                variation = {
                    "region": region.get("region", "Global"),
                    "region_type": "generic",
                    "primary_caption": f"Content for {content_theme} campaign",
                    "secondary_caption": None,
                    "hashtags": region.get("popular_hashtags", []),
                    "adaptation_notes": "Standard content adaptation",
                    "language": "English",
                    "timezone": "UTC"
                }
            
            variations.append(variation)
        
        return variations
    
    def _generate_hashtag_strategies(self, expanded_regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate hashtag strategies for different regions"""
        strategies = {}
        
        for region in expanded_regions:
            region_name = region.get("country", region.get("city", region.get("region", "Unknown")))
            
            if region["region_type"] in ["african_country", "african_city"]:
                # Regional hashtag strategy
                strategies[region_name] = {
                    "primary_hashtags": region.get("popular_hashtags", [])[:3],
                    "secondary_hashtags": region.get("popular_hashtags", [])[3:6] if len(region.get("popular_hashtags", [])) > 3 else [],
                    "trending_hashtags": [],
                    "branded_hashtags": [f"#{region_name.lower().replace(' ', '')}"],
                    "language_specific": region.get("languages", ["English"]),
                    "cultural_hashtags": [f"#{region.get('cultural_context', '').lower().replace(' ', '')}"],
                    "engagement_hashtags": ["#follow", "#like", "#comment", "#share"]
                }
            else:
                # Generic hashtag strategy
                strategies[region_name] = {
                    "primary_hashtags": region.get("popular_hashtags", []),
                    "secondary_hashtags": [],
                    "trending_hashtags": [],
                    "branded_hashtags": [],
                    "language_specific": ["English"],
                    "cultural_hashtags": [],
                    "engagement_hashtags": ["#follow", "#like", "#comment", "#share"]
                }
        
        return strategies
    
    def _create_posting_schedule(self, expanded_regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create posting schedule optimized for different regions"""
        schedule = {}
        
        for region in expanded_regions:
            region_name = region.get("country", region.get("city", region.get("region", "Unknown")))
            timezone = region.get("timezone", "UTC")
            
            # Optimal posting times for different regions
            if "Africa" in timezone:
                # African timezone optimization
                schedule[region_name] = {
                    "timezone": timezone,
                    "optimal_times": [
                        "08:00-10:00",  # Morning commute
                        "12:00-14:00",  # Lunch break
                        "17:00-19:00",  # Evening commute
                        "20:00-22:00"   # Evening relaxation
                    ],
                    "best_days": ["Monday", "Wednesday", "Friday", "Saturday"],
                    "frequency": "3-4 posts per week",
                    "content_mix": [
                        "Monday: Motivational/Start of week",
                        "Wednesday: Mid-week engagement",
                        "Friday: Weekend anticipation",
                        "Saturday: Community/entertainment"
                    ]
                }
            else:
                # Global timezone optimization
                schedule[region_name] = {
                    "timezone": timezone,
                    "optimal_times": [
                        "09:00-11:00",  # Morning
                        "13:00-15:00",  # Afternoon
                        "18:00-20:00",  # Evening
                        "21:00-23:00"   # Night
                    ],
                    "best_days": ["Tuesday", "Wednesday", "Thursday", "Saturday"],
                    "frequency": "4-5 posts per week",
                    "content_mix": [
                        "Tuesday: Educational/How-to",
                        "Wednesday: Hump day content",
                        "Thursday: Throwback/Inspiration",
                        "Saturday: Entertainment/Weekend"
                    ]
                }
        
        return schedule
    
    async def get_region_insights(self, region_name: str) -> Dict[str, Any]:
        """Get detailed insights for a specific region"""
        region_lower = region_name.lower()
        
        # Check African regions
        if region_lower in self.african_regions:
            region_data = self.african_regions[region_lower]
            return {
                "success": True,
                "region": region_data,
                "insights": {
                    "cultural_highlights": region_data["cultural_context"],
                    "language_opportunities": f"Primary: {region_data['languages'][0]}, Secondary: {', '.join(region_data['languages'][1:]) if len(region_data['languages']) > 1 else 'None'}",
                    "timing_optimization": f"Timezone: {region_data['timezone']}",
                    "hashtag_strategy": f"Top hashtags: {', '.join(region_data['popular_hashtags'][:5])}",
                    "content_adaptation": f"Focus on {region_data['cultural_context']}",
                    "engagement_tips": [
                        "Use local language when possible",
                        "Celebrate local culture and traditions",
                        "Engage with local hashtags",
                        "Consider local time zones",
                        "Respect cultural sensitivities"
                    ]
                }
            }
        
        # Check if it's a specific city
        else:
            # Search in African regions
            for region_data in self.african_regions.values():
                if region_lower in [city.lower() for city in region_data["cities"]]:
                    return {
                        "success": True,
                        "region": {
                            "city": region_name.title(),
                            "country": region_data["country"],
                            "languages": region_data["languages"],
                            "timezone": region_data["timezone"],
                            "popular_hashtags": region_data["popular_hashtags"],
                            "cultural_context": region_data["cultural_context"]
                        },
                        "insights": {
                            "cultural_highlights": f"Urban culture in {region_name.title()}, {region_data['country']}",
                            "language_opportunities": f"Primary: {region_data['languages'][0]}, Secondary: {', '.join(region_data['languages'][1:]) if len(region_data['languages']) > 1 else 'None'}",
                            "timing_optimization": f"Timezone: {region_data['timezone']}",
                            "hashtag_strategy": f"City hashtags: {', '.join(region_data['popular_hashtags'][:3])}",
                            "content_adaptation": f"Focus on {region_name.title()} urban culture",
                            "engagement_tips": [
                                "Highlight city-specific landmarks",
                                "Use local language when possible",
                                "Engage with city hashtags",
                                "Consider local time zones",
                                "Show urban lifestyle and culture"
                            ]
                        }
                    }
            
            # Search in global regions
            for region_data in self.global_regions.values():
                if region_lower in [city.lower() for city in region_data["cities"]]:
                    return {
                        "success": True,
                        "region": {
                            "city": region_name.title(),
                            "timezone": region_data["timezone"],
                            "popular_hashtags": region_data["popular_hashtags"],
                            "cultural_context": region_data["cultural_context"]
                        },
                        "insights": {
                            "cultural_highlights": f"Urban culture in {region_name.title()}",
                            "language_opportunities": "Primary: English, Secondary: Local languages",
                            "timing_optimization": f"Timezone: {region_data['timezone']}",
                            "hashtag_strategy": f"City hashtags: {', '.join(region_data['popular_hashtags'][:3])}",
                            "content_adaptation": f"Focus on {region_name.title()} urban culture",
                            "engagement_tips": [
                                "Highlight city-specific landmarks",
                                "Use English as primary language",
                                "Engage with city hashtags",
                                "Consider local time zones",
                                "Show urban lifestyle and culture"
                            ]
                        }
                    }
        
        return {
            "success": False,
            "error": f"Region '{region_name}' not found in our database"
        }
    
    async def get_all_regions(self) -> Dict[str, Any]:
        """Get all available regions for campaign targeting"""
        return {
            "success": True,
            "african_regions": list(self.african_regions.keys()),
            "global_regions": list(self.global_regions.keys()),
            "african_cities": [city for region in self.african_regions.values() for city in region["cities"]],
            "global_cities": [city for region in self.global_regions.values() for city in region["cities"]],
            "total_regions": len(self.african_regions) + len(self.global_regions),
            "total_cities": sum(len(region["cities"]) for region in self.african_regions.values()) + sum(len(region["cities"]) for region in self.global_regions.values())
        }
    
    async def create_campaign_from_template(
        self,
        brand_id: int,
        template_name: str,
        target_regions: List[str],
        customizations: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a campaign from a predefined template"""
        templates = {
            "african_cultural_celebration": {
                "campaign_type": "cultural",
                "content_theme": "Celebrating African Heritage and Culture",
                "default_regions": ["kenya", "nigeria", "south_africa", "ghana"],
                "content_pillars": [
                    "Traditional celebrations",
                    "Modern African innovation",
                    "Cultural heritage",
                    "Community unity",
                    "African excellence"
                ]
            },
            "african_business_spotlight": {
                "campaign_type": "business",
                "content_theme": "Showcasing African Business Innovation",
                "default_regions": ["kenya", "nigeria", "south_africa", "ghana"],
                "content_pillars": [
                    "Startup success stories",
                    "Traditional business wisdom",
                    "Innovation hubs",
                    "Economic growth",
                    "Business opportunities"
                ]
            },
            "african_tourism": {
                "campaign_type": "tourism",
                "content_theme": "Discovering African Destinations",
                "default_regions": ["kenya", "south_africa", "morocco", "egypt"],
                "content_pillars": [
                    "Natural wonders",
                    "Cultural experiences",
                    "Adventure activities",
                    "Local cuisine",
                    "Historical sites"
                ]
            },
            "african_tech_innovation": {
                "campaign_type": "technology",
                "content_theme": "African Tech Innovation and Digital Transformation",
                "default_regions": ["kenya", "nigeria", "south_africa", "rwanda"],
                "content_pillars": [
                    "Fintech solutions",
                    "Digital inclusion",
                    "Tech startups",
                    "Innovation hubs",
                    "Digital skills"
                ]
            }
        }
        
        if template_name not in templates:
            return {
                "success": False,
                "error": f"Template '{template_name}' not found"
            }
        
        template = templates[template_name]
        regions = target_regions or template["default_regions"]
        
        # Create campaign using template
        campaign_result = await self.create_geo_campaign(
            brand_id=brand_id,
            target_regions=regions,
            campaign_type=template["campaign_type"],
            content_theme=template["content_theme"]
        )
        
        if campaign_result["success"]:
            # Apply template customizations
            if customizations:
                campaign_result["campaign"]["template_customizations"] = customizations
                campaign_result["campaign"]["template_name"] = template_name
        
        return campaign_result
