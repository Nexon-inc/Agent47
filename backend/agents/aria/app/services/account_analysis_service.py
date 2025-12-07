from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import (
    SocialAccount, AccountGroup, BrandProfile, Campaign, 
    ScheduledPost, PublishedPost, EngagementEvent, AnalyticsSnapshot,
    PlatformEnum, PostStatus, ApprovalStatus
)
from ..database import get_db
from backend.core.ai import get_ai_service_manager, AIServiceManager


class AccountAnalysisService:
    """Service for analyzing connected social media accounts and providing management recommendations"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Account health indicators
        self.health_indicators = {
            "excellent": {"score": 90, "color": "green", "status": "Excellent"},
            "good": {"score": 75, "color": "blue", "status": "Good"},
            "fair": {"score": 60, "color": "yellow", "status": "Fair"},
            "poor": {"score": 40, "color": "orange", "status": "Poor"},
            "critical": {"score": 0, "color": "red", "status": "Critical"}
        }
    
    async def _get_ai_service_manager(self):
        """Get AI service manager"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager
    
    async def analyze_accounts(
        self,
        user_id: int,
        brand_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Comprehensive analysis of all connected social media accounts"""
        try:
            if not db:
                db = await get_db().__anext__()
            
            # Get all accounts for the user/brand
            accounts_query = select(SocialAccount).where(SocialAccount.user_id == user_id)
            if brand_id:
                accounts_query = accounts_query.where(SocialAccount.brand_id == brand_id)
            
            accounts_result = await db.execute(accounts_query)
            accounts = accounts_result.scalars().all()
            
            if not accounts:
                return {
                    "success": False,
                    "error": "No social media accounts found for this user/brand"
                }
            
            # Analyze each account
            account_analyses = []
            total_engagement = 0
            total_posts = 0
            total_followers = 0
            
            for account in accounts:
                account_analysis = await self._analyze_single_account(account, db)
                account_analyses.append(account_analysis)
                
                total_engagement += account_analysis.get("total_engagement", 0)
                total_posts += account_analysis.get("total_posts", 0)
                total_followers += account_analysis.get("follower_count", 0)
            
            # Generate overall brand analysis
            brand_analysis = await self._analyze_brand_performance(
                accounts, account_analyses, total_engagement, total_posts, total_followers, db
            )
            
            # Generate AI-powered recommendations
            recommendations = await self._generate_ai_recommendations(
                account_analyses, brand_analysis
            )
            
            # Create action plan
            action_plan = await self._create_action_plan(account_analyses, recommendations)
            
            return {
                "success": True,
                "analysis_summary": {
                    "total_accounts": len(accounts),
                    "total_engagement": total_engagement,
                    "total_posts": total_posts,
                    "total_followers": total_followers,
                    "overall_health_score": brand_analysis["overall_health_score"],
                    "analysis_date": datetime.now().isoformat()
                },
                "account_analyses": account_analyses,
                "brand_analysis": brand_analysis,
                "recommendations": recommendations,
                "action_plan": action_plan,
                "next_steps": self._generate_next_steps(account_analyses, recommendations)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze accounts: {str(e)}"
            }
    
    async def _analyze_single_account(
        self,
        account: SocialAccount,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze a single social media account"""
        try:
            # Get account statistics
            stats = await self._get_account_statistics(account.id, db)
            
            # Analyze content performance
            content_analysis = await self._analyze_content_performance(account.id, db)
            
            # Analyze engagement patterns
            engagement_analysis = await self._analyze_engagement_patterns(account.id, db)
            
            # Calculate health score
            health_score = self._calculate_account_health(
                stats, content_analysis, engagement_analysis
            )
            
            # Identify strengths and weaknesses
            strengths, weaknesses = self._identify_account_characteristics(
                stats, content_analysis, engagement_analysis
            )
            
            # Generate platform-specific insights
            platform_insights = await self._generate_platform_insights(account)
            
            return {
                "account_id": account.id,
                "platform": account.platform.value,
                "username": account.username,
                "display_name": account.display_name,
                "follower_count": account.follower_count or 0,
                "following_count": account.following_count or 0,
                "account_age_days": (datetime.now() - account.created_at).days if account.created_at else 0,
                "last_post_date": stats.get("last_post_date"),
                "total_posts": stats.get("total_posts", 0),
                "total_engagement": stats.get("total_engagement", 0),
                "engagement_rate": stats.get("engagement_rate", 0),
                "health_score": health_score,
                "health_status": self._get_health_status(health_score),
                "strengths": strengths,
                "weaknesses": weaknesses,
                "content_analysis": content_analysis,
                "engagement_analysis": engagement_analysis,
                "platform_insights": platform_insights,
                "recommendations": self._generate_account_recommendations(
                    health_score, strengths, weaknesses, platform_insights
                )
            }
            
        except Exception as e:
            return {
                "account_id": account.id,
                "platform": account.platform.value,
                "username": account.username,
                "error": f"Failed to analyze account: {str(e)}"
            }
    
    async def _get_account_statistics(
        self,
        account_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get comprehensive statistics for an account"""
        try:
            # Get post statistics
            posts_query = select(
                func.count().label("total_posts"),
                func.max(PublishedPost.published_at).label("last_post_date"),
                func.avg(PublishedPost.engagement_rate).label("avg_engagement_rate")
            ).where(PublishedPost.account_id == account_id)
            
            posts_result = await db.execute(posts_query)
            posts_stats = posts_result.fetchone()
            
            # Get engagement statistics
            engagement_query = select(
                func.sum(EngagementEvent.engagement_value).label("total_engagement"),
                func.count().label("total_events")
            ).where(EngagementEvent.account_id == account_id)
            
            engagement_result = await db.execute(engagement_query)
            engagement_stats = engagement_result.fetchone()
            
            # Get scheduled posts
            scheduled_query = select(func.count()).where(
                and_(
                    ScheduledPost.account_id == account_id,
                    ScheduledPost.status == PostStatus.PENDING
                )
            )
            scheduled_result = await db.execute(scheduled_query)
            scheduled_count = scheduled_result.scalar()
            
            # Calculate engagement rate
            total_engagement = engagement_stats.total_engagement or 0
            total_posts = posts_stats.total_posts or 0
            engagement_rate = (total_engagement / total_posts * 100) if total_posts > 0 else 0
            
            return {
                "total_posts": total_posts,
                "last_post_date": posts_stats.last_post_date,
                "avg_engagement_rate": float(posts_stats.avg_engagement_rate or 0),
                "total_engagement": total_engagement,
                "total_engagement_events": engagement_stats.total_events or 0,
                "scheduled_posts": scheduled_count,
                "engagement_rate": round(engagement_rate, 2)
            }
            
        except Exception as e:
            return {
                "total_posts": 0,
                "last_post_date": None,
                "avg_engagement_rate": 0,
                "total_engagement": 0,
                "total_engagement_events": 0,
                "scheduled_posts": 0,
                "engagement_rate": 0
            }
    
    async def _analyze_content_performance(
        self,
        account_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze content performance for an account"""
        try:
            # Get recent posts for analysis
            posts_query = select(PublishedPost).where(
                PublishedPost.account_id == account_id
            ).order_by(PublishedPost.published_at.desc()).limit(50)
            
            posts_result = await db.execute(posts_query)
            posts = posts_result.scalars().all()
            
            if not posts:
                return {
                    "content_types": {},
                    "best_performing_content": [],
                    "content_consistency": "No posts available",
                    "content_quality_score": 0
                }
            
            # Analyze content types
            content_types = {}
            best_posts = []
            
            for post in posts:
                content_type = self._categorize_content(post.caption or "")
                if content_type not in content_types:
                    content_types[content_type] = {
                        "count": 0,
                        "total_engagement": 0,
                        "avg_engagement": 0
                    }
                
                content_types[content_type]["count"] += 1
                content_types[content_type]["total_engagement"] += post.engagement_rate or 0
                
                # Track best performing posts
                if post.engagement_rate and post.engagement_rate > 5:  # 5% engagement threshold
                    best_posts.append({
                        "post_id": post.id,
                        "caption": post.caption[:100] + "..." if len(post.caption or "") > 100 else post.caption,
                        "engagement_rate": post.engagement_rate,
                        "published_at": post.published_at.isoformat() if post.published_at else None
                    })
            
            # Calculate averages
            for content_type in content_types:
                count = content_types[content_type]["count"]
                total_engagement = content_types[content_type]["total_engagement"]
                content_types[content_type]["avg_engagement"] = round(total_engagement / count, 2)
            
            # Sort best posts by engagement
            best_posts.sort(key=lambda x: x["engagement_rate"], reverse=True)
            
            # Calculate content consistency
            posting_frequency = len(posts) / 30 if len(posts) > 0 else 0  # posts per month
            if posting_frequency >= 1:
                consistency = "Excellent - Regular posting"
            elif posting_frequency >= 0.5:
                consistency = "Good - Moderate posting"
            elif posting_frequency >= 0.2:
                consistency = "Fair - Irregular posting"
            else:
                consistency = "Poor - Infrequent posting"
            
            # Calculate content quality score
            quality_score = min(100, len(posts) * 2 + (sum(1 for p in posts if p.engagement_rate and p.engagement_rate > 3) * 10))
            
            return {
                "content_types": content_types,
                "best_performing_content": best_posts[:5],
                "content_consistency": consistency,
                "posting_frequency": round(posting_frequency, 2),
                "content_quality_score": min(100, quality_score),
                "total_posts_analyzed": len(posts)
            }
            
        except Exception as e:
            return {
                "content_types": {},
                "best_performing_content": [],
                "content_consistency": "Analysis failed",
                "content_quality_score": 0,
                "error": str(e)
            }
    
    async def _analyze_engagement_patterns(
        self,
        account_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze engagement patterns for an account"""
        try:
            # Get engagement events
            events_query = select(EngagementEvent).where(
                EngagementEvent.account_id == account_id
            ).order_by(EngagementEvent.timestamp.desc()).limit(100)
            
            events_result = await db.execute(events_query)
            events = events_result.scalars().all()
            
            if not events:
                return {
                    "engagement_trends": "No engagement data available",
                    "peak_engagement_times": [],
                    "engagement_types": {},
                    "audience_behavior": "No data available"
                }
            
            # Analyze engagement types
            engagement_types = {}
            for event in events:
                event_type = event.event_type
                if event_type not in engagement_types:
                    engagement_types[event_type] = 0
                engagement_types[event_type] += 1
            
            # Analyze peak engagement times
            time_analysis = {}
            for event in events:
                if event.timestamp:
                    hour = event.timestamp.hour
                    if hour not in time_analysis:
                        time_analysis[hour] = 0
                    time_analysis[hour] += 1
            
            # Find peak hours
            peak_hours = sorted(time_analysis.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_times = [f"{hour:02d}:00" for hour, _ in peak_hours]
            
            # Determine engagement trends
            if len(events) >= 10:
                recent_events = events[:10]
                older_events = events[-10:] if len(events) >= 20 else events[10:]
                
                recent_engagement = sum(e.engagement_value or 0 for e in recent_events)
                older_engagement = sum(e.engagement_value or 0 for e in older_events)
                
                if recent_engagement > older_engagement * 1.2:
                    trend = "Increasing - Engagement is growing"
                elif recent_engagement < older_engagement * 0.8:
                    trend = "Decreasing - Engagement is declining"
                else:
                    trend = "Stable - Engagement is consistent"
            else:
                trend = "Insufficient data for trend analysis"
            
            # Analyze audience behavior
            total_engagement = sum(e.engagement_value or 0 for e in events)
            if total_engagement > 1000:
                behavior = "Highly engaged audience"
            elif total_engagement > 500:
                behavior = "Moderately engaged audience"
            elif total_engagement > 100:
                behavior = "Low engagement audience"
            else:
                behavior = "Minimal engagement audience"
            
            return {
                "engagement_trends": trend,
                "peak_engagement_times": peak_times,
                "engagement_types": engagement_types,
                "audience_behavior": behavior,
                "total_engagement_events": len(events),
                "engagement_distribution": time_analysis
            }
            
        except Exception as e:
            return {
                "engagement_trends": "Analysis failed",
                "peak_engagement_times": [],
                "engagement_types": {},
                "audience_behavior": "Analysis failed",
                "error": str(e)
            }
    
    def _calculate_account_health(
        self,
        stats: Dict[str, Any],
        content_analysis: Dict[str, Any],
        engagement_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall health score for an account"""
        try:
            score = 0
            
            # Posting consistency (25 points)
            if stats.get("total_posts", 0) >= 30:
                score += 25
            elif stats.get("total_posts", 0) >= 20:
                score += 20
            elif stats.get("total_posts", 0) >= 10:
                score += 15
            elif stats.get("total_posts", 0) >= 5:
                score += 10
            else:
                score += 5
            
            # Engagement rate (30 points)
            engagement_rate = stats.get("engagement_rate", 0)
            if engagement_rate >= 5:
                score += 30
            elif engagement_rate >= 3:
                score += 25
            elif engagement_rate >= 2:
                score += 20
            elif engagement_rate >= 1:
                score += 15
            else:
                score += 10
            
            # Content quality (25 points)
            content_score = content_analysis.get("content_quality_score", 0)
            score += (content_score / 100) * 25
            
            # Recent activity (20 points)
            last_post = stats.get("last_post_date")
            if last_post:
                days_since_last_post = (datetime.now() - last_post).days
                if days_since_last_post <= 7:
                    score += 20
                elif days_since_last_post <= 14:
                    score += 15
                elif days_since_last_post <= 30:
                    score += 10
                else:
                    score += 5
            else:
                score += 0
            
            return min(100, round(score, 1))
            
        except Exception as e:
            return 50.0  # Default score if calculation fails
    
    def _get_health_status(self, health_score: float) -> Dict[str, Any]:
        """Get health status based on score"""
        for status, data in self.health_indicators.items():
            if health_score >= data["score"]:
                return {
                    "status": data["status"],
                    "color": data["color"],
                    "score": health_score
                }
        return {
            "status": "Critical",
            "color": "red",
            "score": health_score
        }
    
    def _identify_account_characteristics(
        self,
        stats: Dict[str, Any],
        content_analysis: Dict[str, Any],
        engagement_analysis: Dict[str, Any]
    ) -> tuple[List[str], List[str]]:
        """Identify account strengths and weaknesses"""
        strengths = []
        weaknesses = []
        
        # Analyze strengths
        if stats.get("total_posts", 0) >= 20:
            strengths.append("Consistent posting history")
        if stats.get("engagement_rate", 0) >= 3:
            strengths.append("Good engagement rates")
        if content_analysis.get("content_quality_score", 0) >= 70:
            strengths.append("High-quality content")
        if stats.get("scheduled_posts", 0) > 0:
            strengths.append("Content planning and scheduling")
        
        # Analyze weaknesses
        if stats.get("total_posts", 0) < 10:
            weaknesses.append("Limited content history")
        if stats.get("engagement_rate", 0) < 2:
            weaknesses.append("Low engagement rates")
        if content_analysis.get("content_quality_score", 0) < 50:
            weaknesses.append("Content quality needs improvement")
        
        last_post = stats.get("last_post_date")
        if last_post and (datetime.now() - last_post).days > 30:
            weaknesses.append("Inactive posting")
        
        return strengths, weaknesses
    
    async def _generate_platform_insights(self, account: SocialAccount) -> Dict[str, Any]:
        """Generate platform-specific insights and recommendations"""
        platform = account.platform.value
        
        platform_insights = {
            "instagram": {
                "best_posting_times": ["08:00-10:00", "12:00-14:00", "17:00-19:00", "20:00-22:00"],
                "content_strategies": [
                    "Use high-quality images and videos",
                    "Leverage Instagram Stories and Reels",
                    "Engage with hashtags and location tags",
                    "Collaborate with influencers and brands"
                ],
                "growth_tips": [
                    "Post consistently (1-2 times daily)",
                    "Use relevant hashtags (15-30 per post)",
                    "Engage with your audience through comments",
                    "Cross-promote on other platforms"
                ]
            },
            "linkedin": {
                "best_posting_times": ["09:00-11:00", "13:00-15:00", "17:00-19:00"],
                "content_strategies": [
                    "Share professional insights and industry news",
                    "Post thought leadership content",
                    "Engage with industry discussions",
                    "Network with professionals in your field"
                ],
                "growth_tips": [
                    "Post 2-3 times per week",
                    "Focus on professional development content",
                    "Engage with industry leaders",
                    "Join and participate in relevant groups"
                ]
            },
            "twitter": {
                "best_posting_times": ["08:00-10:00", "12:00-14:00", "16:00-18:00", "20:00-22:00"],
                "content_strategies": [
                    "Share timely updates and news",
                    "Engage in trending conversations",
                    "Use relevant hashtags",
                    "Retweet and engage with others"
                ],
                "growth_tips": [
                    "Tweet 3-5 times daily",
                    "Participate in Twitter chats",
                    "Engage with trending topics",
                    "Build relationships with followers"
                ]
            },
            "facebook": {
                "best_posting_times": ["09:00-11:00", "13:00-15:00", "19:00-21:00"],
                "content_strategies": [
                    "Share community-focused content",
                    "Use Facebook Live for engagement",
                    "Create Facebook Groups for community building",
                    "Share behind-the-scenes content"
                ],
                "growth_tips": [
                    "Post 1-2 times daily",
                    "Engage with comments and messages",
                    "Use Facebook Insights for optimization",
                    "Create engaging video content"
                ]
            },
            "tiktok": {
                "best_posting_times": ["12:00-14:00", "16:00-18:00", "19:00-21:00", "21:00-23:00"],
                "content_strategies": [
                    "Create trending and viral content",
                    "Use popular sounds and effects",
                    "Participate in challenges and trends",
                    "Engage with the TikTok community"
                ],
                "growth_tips": [
                    "Post 1-3 times daily",
                    "Follow trending hashtags and sounds",
                    "Engage with comments and duets",
                    "Create authentic, entertaining content"
                ]
            }
        }
        
        return platform_insights.get(platform, {
            "best_posting_times": ["09:00-11:00", "13:00-15:00", "17:00-19:00"],
            "content_strategies": ["Focus on platform-specific best practices"],
            "growth_tips": ["Maintain consistent posting schedule"]
        })
    
    def _generate_account_recommendations(
        self,
        health_score: float,
        strengths: List[str],
        weaknesses: List[str],
        platform_insights: Dict[str, Any]
    ) -> List[str]:
        """Generate specific recommendations for an account"""
        recommendations = []
        
        # Health-based recommendations
        if health_score < 50:
            recommendations.append("Focus on improving content quality and engagement")
            recommendations.append("Increase posting frequency to build consistency")
        elif health_score < 75:
            recommendations.append("Optimize content strategy for better engagement")
            recommendations.append("Implement content planning and scheduling")
        else:
            recommendations.append("Maintain current performance and explore growth opportunities")
            recommendations.append("Experiment with new content formats and strategies")
        
        # Weakness-based recommendations
        for weakness in weaknesses:
            if "Limited content history" in weakness:
                recommendations.append("Create and publish more content to build your presence")
            elif "Low engagement rates" in weakness:
                recommendations.append("Analyze top-performing content and replicate successful strategies")
            elif "Content quality needs improvement" in weakness:
                recommendations.append("Invest in better visuals and compelling copywriting")
            elif "Inactive posting" in weakness:
                recommendations.append("Resume regular posting schedule to maintain audience engagement")
        
        # Platform-specific recommendations
        if platform_insights.get("content_strategies"):
            recommendations.extend(platform_insights["content_strategies"][:2])
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def _analyze_brand_performance(
        self,
        accounts: List[SocialAccount],
        account_analyses: List[Dict[str, Any]],
        total_engagement: int,
        total_posts: int,
        total_followers: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze overall brand performance across all accounts"""
        try:
            # Calculate overall metrics
            avg_health_score = sum(analysis.get("health_score", 0) for analysis in account_analyses) / len(account_analyses)
            
            # Platform distribution
            platform_distribution = {}
            for account in accounts:
                platform = account.platform.value
                if platform not in platform_distribution:
                    platform_distribution[platform] = 0
                platform_distribution[platform] += 1
            
            # Content performance across platforms
            content_performance = {}
            for analysis in account_analyses:
                platform = analysis.get("platform", "unknown")
                if platform not in content_performance:
                    content_performance[platform] = {
                        "total_posts": 0,
                        "total_engagement": 0,
                        "avg_engagement_rate": 0
                    }
                
                content_performance[platform]["total_posts"] += analysis.get("total_posts", 0)
                content_performance[platform]["total_engagement"] += analysis.get("total_engagement", 0)
            
            # Calculate averages
            for platform in content_performance:
                posts = content_performance[platform]["total_posts"]
                engagement = content_performance[platform]["total_engagement"]
                if posts > 0:
                    content_performance[platform]["avg_engagement_rate"] = round(engagement / posts, 2)
            
            # Determine overall health status
            overall_health_score = round(avg_health_score, 1)
            overall_health_status = self._get_health_status(overall_health_score)
            
            # Identify top performing platform
            top_platform = max(content_performance.keys(), 
                             key=lambda p: content_performance[p]["avg_engagement_rate"]) if content_performance else None
            
            return {
                "overall_health_score": overall_health_score,
                "overall_health_status": overall_health_status,
                "total_accounts": len(accounts),
                "platform_distribution": platform_distribution,
                "content_performance": content_performance,
                "top_performing_platform": top_platform,
                "cross_platform_consistency": self._assess_cross_platform_consistency(account_analyses),
                "brand_growth_potential": self._assess_growth_potential(accounts, total_followers, total_engagement)
            }
            
        except Exception as e:
            return {
                "overall_health_score": 0,
                "overall_health_status": {"status": "Unknown", "color": "gray", "score": 0},
                "error": f"Failed to analyze brand performance: {str(e)}"
            }
    
    def _assess_cross_platform_consistency(self, account_analyses: List[Dict[str, Any]]) -> str:
        """Assess consistency across different platforms"""
        if len(account_analyses) < 2:
            return "Single platform - No cross-platform analysis possible"
        
        health_scores = [analysis.get("health_score", 0) for analysis in account_analyses]
        score_variance = max(health_scores) - min(health_scores)
        
        if score_variance <= 20:
            return "Excellent - Consistent performance across platforms"
        elif score_variance <= 40:
            return "Good - Moderate consistency across platforms"
        elif score_variance <= 60:
            return "Fair - Inconsistent performance across platforms"
        else:
            return "Poor - Significant performance gaps between platforms"
    
    def _assess_growth_potential(
        self,
        accounts: List[SocialAccount],
        total_followers: int,
        total_engagement: int
    ) -> str:
        """Assess brand growth potential"""
        if total_followers == 0:
            return "New brand - High growth potential"
        
        engagement_rate = (total_engagement / total_followers * 100) if total_followers > 0 else 0
        
        if engagement_rate >= 5:
            return "High growth potential - Strong audience engagement"
        elif engagement_rate >= 3:
            return "Moderate growth potential - Good audience engagement"
        elif engagement_rate >= 1:
            return "Limited growth potential - Low audience engagement"
        else:
            return "Low growth potential - Poor audience engagement"
    
    async def _generate_ai_recommendations(
        self,
        account_analyses: List[Dict[str, Any]],
        brand_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered recommendations using NLP"""
        try:
            nlp = await self._get_nlp()
            
            # Create context for AI analysis
            context = {
                "total_accounts": len(account_analyses),
                "overall_health_score": brand_analysis.get("overall_health_score", 0),
                "platform_distribution": brand_analysis.get("platform_distribution", {}),
                "account_summaries": [
                    {
                        "platform": analysis.get("platform"),
                        "health_score": analysis.get("health_score"),
                        "strengths": analysis.get("strengths", []),
                        "weaknesses": analysis.get("weaknesses", [])
                    }
                    for analysis in account_analyses
                ]
            }
            
            # Generate AI recommendations
            prompt = f"""
            Analyze this social media brand and provide strategic recommendations:
            
            Brand Overview:
            - Total accounts: {context['total_accounts']}
            - Overall health score: {context['overall_health_score']}/100
            - Platforms: {', '.join(context['platform_distribution'].keys())}
            
            Account Details:
            {str(context['account_summaries'])}
            
            Provide:
            1. Top 3 strategic priorities
            2. Content strategy recommendations
            3. Platform optimization suggestions
            4. Growth opportunities
            5. Risk mitigation strategies
            
            Be specific, actionable, and professional.
            """
            
            messages = [
                {"role": "system", "content": "Social media brand analysis and strategic recommendations"},
                {"role": "user", "content": prompt}
            ]
            
            response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            if response.success:
                return {
                    "ai_generated": True,
                    "strategic_priorities": self._extract_ai_recommendations(response.text_content),
                    "full_recommendations": response.text_content
                }
            else:
                return {
                    "ai_generated": False,
                    "strategic_priorities": self._generate_fallback_recommendations(context),
                    "full_recommendations": "AI recommendations unavailable"
                }
                
        except Exception as e:
            return {
                "ai_generated": False,
                "strategic_priorities": self._generate_fallback_recommendations({}),
                "full_recommendations": f"Failed to generate AI recommendations: {str(e)}"
            }
    
    def _extract_ai_recommendations(self, ai_response: str) -> List[str]:
        """Extract key recommendations from AI response"""
        # Simple extraction - in production, this would use more sophisticated parsing
        lines = ai_response.split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                clean_line = line.lstrip('-•1234567890. ')
                if clean_line and len(clean_line) > 10:
                    recommendations.append(clean_line)
        
        return recommendations[:5] if recommendations else self._generate_fallback_recommendations({})
    
    def _generate_fallback_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate fallback recommendations when AI is unavailable"""
        return [
            "Focus on improving content quality and consistency across all platforms",
            "Implement a regular posting schedule to maintain audience engagement",
            "Analyze top-performing content and replicate successful strategies",
            "Engage with your audience through comments, likes, and shares",
            "Consider cross-platform content adaptation for better reach"
        ]
    
    async def _create_action_plan(
        self,
        account_analyses: List[Dict[str, Any]],
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create actionable plan based on analysis"""
        try:
            # Prioritize actions based on account health scores
            critical_accounts = [a for a in account_analyses if a.get("health_score", 0) < 50]
            improvement_accounts = [a for a in account_analyses if 50 <= a.get("health_score", 0) < 75]
            optimization_accounts = [a for a in account_analyses if a.get("health_score", 0) >= 75]
            
            action_plan = {
                "immediate_actions": [],
                "short_term_goals": [],
                "long_term_strategies": [],
                "priority_levels": {
                    "critical": len(critical_accounts),
                    "improvement": len(improvement_accounts),
                    "optimization": len(optimization_accounts)
                }
            }
            
            # Immediate actions for critical accounts
            for account in critical_accounts:
                action_plan["immediate_actions"].extend([
                    f"Resume posting on {account.get('platform', 'Unknown')} account",
                    f"Review and improve content quality for {account.get('platform', 'Unknown')}",
                    f"Engage with audience on {account.get('platform', 'Unknown')}"
                ])
            
            # Short-term goals
            action_plan["short_term_goals"] = [
                "Improve overall health score to 75+ across all accounts",
                "Implement consistent posting schedule",
                "Optimize content for each platform's best practices",
                "Increase engagement rates through audience interaction"
            ]
            
            # Long-term strategies
            action_plan["long_term_strategies"] = [
                "Develop comprehensive content strategy",
                "Build cross-platform brand consistency",
                "Implement advanced analytics and optimization",
                "Explore new platform opportunities",
                "Build influencer and partnership networks"
            ]
            
            return action_plan
            
        except Exception as e:
            return {
                "immediate_actions": ["Review account performance and identify improvement areas"],
                "short_term_goals": ["Improve overall account health"],
                "long_term_strategies": ["Develop comprehensive social media strategy"],
                "error": f"Failed to create action plan: {str(e)}"
            }
    
    def _generate_next_steps(
        self,
        account_analyses: List[Dict[str, Any]],
        recommendations: Dict[str, Any]
    ) -> List[str]:
        """Generate next steps for users"""
        next_steps = [
            "Review the detailed analysis for each account",
            "Prioritize actions based on account health scores",
            "Implement the recommended content strategies",
            "Set up regular posting schedules",
            "Monitor performance improvements over time"
        ]
        
        # Add platform-specific next steps
        platforms = set(analysis.get("platform") for analysis in account_analyses)
        for platform in platforms:
            if platform:
                next_steps.append(f"Optimize {platform} strategy based on platform insights")
        
        return next_steps
    
    def _categorize_content(self, caption: str) -> str:
        """Categorize content based on caption text"""
        if not caption:
            return "No caption"
        
        caption_lower = caption.lower()
        
        if any(word in caption_lower for word in ["sale", "discount", "offer", "deal", "promotion"]):
            return "Promotional"
        elif any(word in caption_lower for word in ["tip", "advice", "how to", "guide", "tutorial"]):
            return "Educational"
        elif any(word in caption_lower for word in ["behind the scenes", "bts", "work", "process"]):
            return "Behind the Scenes"
        elif any(word in caption_lower for word in ["announcement", "news", "update", "launch"]):
            return "Announcement"
        elif any(word in caption_lower for word in ["question", "poll", "survey", "feedback"]):
            return "Interactive"
        elif any(word in caption_lower for word in ["inspiration", "motivation", "quote", "positive"]):
            return "Inspirational"
        else:
            return "General"
