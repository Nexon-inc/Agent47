import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text
import re
import hashlib

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class ArticleStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REVIEW = "review"

class ArticleCategory(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    TROUBLESHOOTING = "troubleshooting"
    FAQ = "faq"
    TUTORIAL = "tutorial"
    ANNOUNCEMENT = "announcement"

class ArticleType(Enum):
    ARTICLE = "article"
    FAQ = "faq"
    TUTORIAL = "tutorial"
    TROUBLESHOOTING = "troubleshooting"
    VIDEO = "video"
    DOCUMENT = "document"

class SearchResult(Enum):
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"
    RELATED = "related"
    SUGGESTED = "suggested"

@dataclass
class KnowledgeArticle:
    article_id: str
    title: str
    content: str
    summary: str
    category: ArticleCategory
    article_type: ArticleType
    status: ArticleStatus
    author_id: str
    author_name: str
    tags: List[str]
    keywords: List[str]
    view_count: int
    helpful_count: int
    not_helpful_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    version: int
    metadata: Dict[str, Any]

@dataclass
class ArticleVersion:
    version_id: str
    article_id: str
    version_number: int
    title: str
    content: str
    summary: str
    changes: str
    created_at: datetime
    created_by: str

@dataclass
class ArticleFeedback:
    feedback_id: str
    article_id: str
    user_id: str
    user_email: str
    rating: int
    comment: str
    helpful: bool
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class SearchQuery:
    query_id: str
    query_text: str
    user_id: Optional[str]
    results_count: int
    search_time_ms: int
    created_at: datetime
    metadata: Dict[str, Any]

class KnowledgeBase(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.article_cache: Dict[str, KnowledgeArticle] = {}
        self.search_index: Dict[str, List[str]] = {}
        self.popular_articles: List[str] = []
        self.recent_searches: List[str] = []
        self.search_analytics: Dict[str, int] = {}
        self.max_cache_size = 1000
        self.search_result_limit = 50

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing KnowledgeBase...")
            self.database = get_database()
            await self._setup_knowledge_tables()
            await self._load_articles()
            await self._build_search_index()
            await self._load_popular_articles()
            self.logger.info("KnowledgeBase initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize KnowledgeBase: {str(e)}")
            return False

    async def _setup_knowledge_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_articles (
                    id SERIAL PRIMARY KEY,
                    article_id VARCHAR(255) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    category VARCHAR(30) NOT NULL,
                    article_type VARCHAR(30) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    author_id VARCHAR(255) NOT NULL,
                    author_name VARCHAR(255) NOT NULL,
                    tags JSONB DEFAULT '[]'::jsonb,
                    keywords JSONB DEFAULT '[]'::jsonb,
                    view_count INTEGER DEFAULT 0,
                    helpful_count INTEGER DEFAULT 0,
                    not_helpful_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published_at TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS article_versions (
                    id SERIAL PRIMARY KEY,
                    version_id VARCHAR(255) UNIQUE NOT NULL,
                    article_id VARCHAR(255) NOT NULL,
                    version_number INTEGER NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    changes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255) NOT NULL,
                    FOREIGN KEY (article_id) REFERENCES knowledge_articles(article_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS article_feedback (
                    id SERIAL PRIMARY KEY,
                    feedback_id VARCHAR(255) UNIQUE NOT NULL,
                    article_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    user_email VARCHAR(255),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    helpful BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (article_id) REFERENCES knowledge_articles(article_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS search_queries (
                    id SERIAL PRIMARY KEY,
                    query_id VARCHAR(255) UNIQUE NOT NULL,
                    query_text TEXT NOT NULL,
                    user_id VARCHAR(255),
                    results_count INTEGER DEFAULT 0,
                    search_time_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS article_views (
                    id SERIAL PRIMARY KEY,
                    view_id VARCHAR(255) UNIQUE NOT NULL,
                    article_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    ip_address INET,
                    user_agent TEXT,
                    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (article_id) REFERENCES knowledge_articles(article_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_articles_status 
                ON knowledge_articles(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_articles_category 
                ON knowledge_articles(category);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_articles_article_type 
                ON knowledge_articles(article_type);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_articles_view_count 
                ON knowledge_articles(view_count);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_articles_published_at 
                ON knowledge_articles(published_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_article_versions_article_id 
                ON article_versions(article_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_article_feedback_article_id 
                ON article_feedback(article_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_queries_created_at 
                ON search_queries(created_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_article_views_article_id 
                ON article_views(article_id);
            """)
            
            await session.commit()

    async def _load_articles(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT article_id, title, content, summary, category, article_type, status,
                       author_id, author_name, tags, keywords, view_count, helpful_count,
                       not_helpful_count, created_at, updated_at, published_at, version, metadata
                FROM knowledge_articles
                WHERE status = 'published'
            """)
            
            for row in result:
                article = KnowledgeArticle(
                    article_id=row.article_id,
                    title=row.title,
                    content=row.content,
                    summary=row.summary or "",
                    category=ArticleCategory(row.category),
                    article_type=ArticleType(row.article_type),
                    status=ArticleStatus(row.status),
                    author_id=row.author_id,
                    author_name=row.author_name,
                    tags=row.tags or [],
                    keywords=row.keywords or [],
                    view_count=row.view_count,
                    helpful_count=row.helpful_count,
                    not_helpful_count=row.not_helpful_count,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    published_at=row.published_at,
                    version=row.version,
                    metadata=row.metadata or {}
                )
                self.article_cache[article.article_id] = article

    async def _build_search_index(self):
        try:
            self.search_index = {}
            
            for article_id, article in self.article_cache.items():
                searchable_text = f"{article.title} {article.content} {article.summary} {' '.join(article.tags)} {' '.join(article.keywords)}"
                words = re.findall(r'\b\w+\b', searchable_text.lower())
                
                for word in words:
                    if len(word) > 2:
                        if word not in self.search_index:
                            self.search_index[word] = []
                        if article_id not in self.search_index[word]:
                            self.search_index[word].append(article_id)
            
            self.logger.info(f"Search index built with {len(self.search_index)} terms")
            
        except Exception as e:
            self.logger.error(f"Failed to build search index: {str(e)}")

    async def _load_popular_articles(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT article_id, view_count, helpful_count
                FROM knowledge_articles
                WHERE status = 'published'
                ORDER BY (view_count + helpful_count * 2) DESC
                LIMIT 20
            """)
            
            self.popular_articles = [row.article_id for row in result]

    async def create_article(
        self,
        title: str,
        content: str,
        summary: str,
        category: ArticleCategory,
        article_type: ArticleType,
        author_id: str,
        author_name: str,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        status: ArticleStatus = ArticleStatus.DRAFT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            article_id = f"KB_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(title) % 10000}"
            
            article = KnowledgeArticle(
                article_id=article_id,
                title=title,
                content=content,
                summary=summary,
                category=category,
                article_type=article_type,
                status=status,
                author_id=author_id,
                author_name=author_name,
                tags=tags or [],
                keywords=keywords or [],
                view_count=0,
                helpful_count=0,
                not_helpful_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                published_at=datetime.utcnow() if status == ArticleStatus.PUBLISHED else None,
                version=1,
                metadata=metadata or {}
            )
            
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO knowledge_articles (
                        article_id, title, content, summary, category, article_type, status,
                        author_id, author_name, tags, keywords, published_at, metadata
                    ) VALUES (
                        :article_id, :title, :content, :summary, :category, :article_type, :status,
                        :author_id, :author_name, :tags, :keywords, :published_at, :metadata
                    )
                """, {
                    "article_id": article.article_id,
                    "title": article.title,
                    "content": article.content,
                    "summary": article.summary,
                    "category": article.category.value,
                    "article_type": article.article_type.value,
                    "status": article.status.value,
                    "author_id": article.author_id,
                    "author_name": article.author_name,
                    "tags": article.tags,
                    "keywords": article.keywords,
                    "published_at": article.published_at,
                    "metadata": article.metadata
                })
                await session.commit()
            
            if status == ArticleStatus.PUBLISHED:
                self.article_cache[article_id] = article
                await self._update_search_index(article)
            
            self.logger.info(f"Knowledge article created: {article_id}")
            return article_id
            
        except Exception as e:
            self.logger.error(f"Failed to create article: {str(e)}")
            return None

    async def update_article(
        self,
        article_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        category: Optional[ArticleCategory] = None,
        article_type: Optional[ArticleType] = None,
        status: Optional[ArticleStatus] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        updated_by: str = "system"
    ) -> bool:
        try:
            if article_id not in self.article_cache:
                article = await self.get_article(article_id)
                if not article:
                    return False
            else:
                article = self.article_cache[article_id]
            
            if not self.database:
                return False
            
            old_content = article.content
            old_title = article.title
            
            update_fields = ["updated_at = :updated_at", "version = version + 1"]
            params = {"article_id": article_id, "updated_at": datetime.utcnow()}
            
            if title is not None:
                update_fields.append("title = :title")
                params["title"] = title
                article.title = title
            
            if content is not None:
                update_fields.append("content = :content")
                params["content"] = content
                article.content = content
            
            if summary is not None:
                update_fields.append("summary = :summary")
                params["summary"] = summary
                article.summary = summary
            
            if category is not None:
                update_fields.append("category = :category")
                params["category"] = category.value
                article.category = category
            
            if article_type is not None:
                update_fields.append("article_type = :article_type")
                params["article_type"] = article_type.value
                article.article_type = article_type
            
            if status is not None:
                update_fields.append("status = :status")
                params["status"] = status.value
                article.status = status
                
                if status == ArticleStatus.PUBLISHED and article.published_at is None:
                    update_fields.append("published_at = :published_at")
                    params["published_at"] = datetime.utcnow()
                    article.published_at = datetime.utcnow()
            
            if tags is not None:
                update_fields.append("tags = :tags")
                params["tags"] = tags
                article.tags = tags
            
            if keywords is not None:
                update_fields.append("keywords = :keywords")
                params["keywords"] = keywords
                article.keywords = keywords
            
            if metadata is not None:
                update_fields.append("metadata = :metadata")
                params["metadata"] = metadata
                article.metadata = metadata
            
            async with self.database.get_session() as session:
                await session.execute(f"""
                    UPDATE knowledge_articles 
                    SET {', '.join(update_fields)}
                    WHERE article_id = :article_id
                """, params)
                
                await self._save_article_version(
                    article_id, old_title, old_content, article.summary, 
                    f"Updated by {updated_by}", updated_by
                )
                
                await session.commit()
            
            article.version += 1
            article.updated_at = datetime.utcnow()
            
            if article.status == ArticleStatus.PUBLISHED:
                self.article_cache[article_id] = article
                await self._update_search_index(article)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update article: {str(e)}")
            return False

    async def _save_article_version(
        self,
        article_id: str,
        title: str,
        content: str,
        summary: str,
        changes: str,
        created_by: str
    ):
        try:
            if not self.database:
                return
            
            version_id = f"VERSION_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(article_id) % 10000}"
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT version FROM knowledge_articles WHERE article_id = :article_id
                """, {"article_id": article_id})
                
                row = result.fetchone()
                version_number = row.version if row else 1
                
                await session.execute("""
                    INSERT INTO article_versions (
                        version_id, article_id, version_number, title, content, summary, changes, created_by
                    ) VALUES (
                        :version_id, :article_id, :version_number, :title, :content, :summary, :changes, :created_by
                    )
                """, {
                    "version_id": version_id,
                    "article_id": article_id,
                    "version_number": version_number,
                    "title": title,
                    "content": content,
                    "summary": summary,
                    "changes": changes,
                    "created_by": created_by
                })
                
        except Exception as e:
            self.logger.error(f"Failed to save article version: {str(e)}")

    async def _update_search_index(self, article: KnowledgeArticle):
        try:
            searchable_text = f"{article.title} {article.content} {article.summary} {' '.join(article.tags)} {' '.join(article.keywords)}"
            words = re.findall(r'\b\w+\b', searchable_text.lower())
            
            for word in words:
                if len(word) > 2:
                    if word not in self.search_index:
                        self.search_index[word] = []
                    if article.article_id not in self.search_index[word]:
                        self.search_index[word].append(article.article_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update search index: {str(e)}")

    async def get_article(self, article_id: str) -> Optional[KnowledgeArticle]:
        try:
            if article_id in self.article_cache:
                return self.article_cache[article_id]
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT article_id, title, content, summary, category, article_type, status,
                           author_id, author_name, tags, keywords, view_count, helpful_count,
                           not_helpful_count, created_at, updated_at, published_at, version, metadata
                    FROM knowledge_articles
                    WHERE article_id = :article_id
                """, {"article_id": article_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                article = KnowledgeArticle(
                    article_id=row.article_id,
                    title=row.title,
                    content=row.content,
                    summary=row.summary or "",
                    category=ArticleCategory(row.category),
                    article_type=ArticleType(row.article_type),
                    status=ArticleStatus(row.status),
                    author_id=row.author_id,
                    author_name=row.author_name,
                    tags=row.tags or [],
                    keywords=row.keywords or [],
                    view_count=row.view_count,
                    helpful_count=row.helpful_count,
                    not_helpful_count=row.not_helpful_count,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    published_at=row.published_at,
                    version=row.version,
                    metadata=row.metadata or {}
                )
                
                if article.status == ArticleStatus.PUBLISHED:
                    self.article_cache[article_id] = article
                
                return article
                
        except Exception as e:
            self.logger.error(f"Failed to get article: {str(e)}")
            return None

    async def search_articles(
        self,
        query: str,
        category: Optional[ArticleCategory] = None,
        article_type: Optional[ArticleType] = None,
        limit: int = 20,
        user_id: Optional[str] = None
    ) -> List[Tuple[KnowledgeArticle, float, SearchResult]]:
        try:
            start_time = datetime.utcnow()
            
            query_words = re.findall(r'\b\w+\b', query.lower())
            article_scores = {}
            
            for word in query_words:
                if word in self.search_index:
                    for article_id in self.search_index[word]:
                        if article_id not in article_scores:
                            article_scores[article_id] = 0
                        article_scores[article_id] += 1
            
            results = []
            for article_id, score in sorted(article_scores.items(), key=lambda x: x[1], reverse=True):
                if len(results) >= limit:
                    break
                
                article = await self.get_article(article_id)
                if not article or article.status != ArticleStatus.PUBLISHED:
                    continue
                
                if category and article.category != category:
                    continue
                
                if article_type and article.article_type != article_type:
                    continue
                
                result_type = SearchResult.EXACT_MATCH if score == len(query_words) else SearchResult.PARTIAL_MATCH
                results.append((article, score, result_type))
            
            search_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._log_search_query(query, user_id, len(results), search_time_ms)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search articles: {str(e)}")
            return []

    async def _log_search_query(
        self,
        query: str,
        user_id: Optional[str],
        results_count: int,
        search_time_ms: int
    ):
        try:
            if not self.database:
                return
            
            query_id = f"QUERY_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000}"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO search_queries (
                        query_id, query_text, user_id, results_count, search_time_ms
                    ) VALUES (
                        :query_id, :query_text, :user_id, :results_count, :search_time_ms
                    )
                """, {
                    "query_id": query_id,
                    "query_text": query,
                    "user_id": user_id,
                    "results_count": results_count,
                    "search_time_ms": search_time_ms
                })
                await session.commit()
            
            self.recent_searches.append(query)
            if len(self.recent_searches) > 100:
                self.recent_searches = self.recent_searches[-100:]
            
            if query in self.search_analytics:
                self.search_analytics[query] += 1
            else:
                self.search_analytics[query] = 1
                
        except Exception as e:
            self.logger.error(f"Failed to log search query: {str(e)}")

    async def record_article_view(
        self,
        article_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        try:
            if not self.database:
                return False
            
            view_id = f"VIEW_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(article_id) % 10000}"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO article_views (
                        view_id, article_id, user_id, ip_address, user_agent
                    ) VALUES (
                        :view_id, :article_id, :user_id, :ip_address, :user_agent
                    )
                """, {
                    "view_id": view_id,
                    "article_id": article_id,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })
                
                await session.execute("""
                    UPDATE knowledge_articles 
                    SET view_count = view_count + 1
                    WHERE article_id = :article_id
                """, {"article_id": article_id})
                
                await session.commit()
            
            if article_id in self.article_cache:
                self.article_cache[article_id].view_count += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record article view: {str(e)}")
            return False

    async def add_article_feedback(
        self,
        article_id: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        helpful: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            feedback_id = f"FEEDBACK_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(article_id) % 10000}"
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO article_feedback (
                        feedback_id, article_id, user_id, user_email, rating, comment, helpful, metadata
                    ) VALUES (
                        :feedback_id, :article_id, :user_id, :user_email, :rating, :comment, :helpful, :metadata
                    )
                """, {
                    "feedback_id": feedback_id,
                    "article_id": article_id,
                    "user_id": user_id,
                    "user_email": user_email,
                    "rating": rating,
                    "comment": comment,
                    "helpful": helpful,
                    "metadata": metadata or {}
                })
                
                if helpful is not None:
                    if helpful:
                        await session.execute("""
                            UPDATE knowledge_articles 
                            SET helpful_count = helpful_count + 1
                            WHERE article_id = :article_id
                        """, {"article_id": article_id})
                    else:
                        await session.execute("""
                            UPDATE knowledge_articles 
                            SET not_helpful_count = not_helpful_count + 1
                            WHERE article_id = :article_id
                        """, {"article_id": article_id})
                
                await session.commit()
            
            if article_id in self.article_cache:
                if helpful:
                    self.article_cache[article_id].helpful_count += 1
                else:
                    self.article_cache[article_id].not_helpful_count += 1
            
            return feedback_id
            
        except Exception as e:
            self.logger.error(f"Failed to add article feedback: {str(e)}")
            return None

    async def get_articles(
        self,
        category: Optional[ArticleCategory] = None,
        article_type: Optional[ArticleType] = None,
        status: Optional[ArticleStatus] = None,
        author_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeArticle]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if category:
            conditions.append("category = :category")
            params["category"] = category.value
        
        if article_type:
            conditions.append("article_type = :article_type")
            params["article_type"] = article_type.value
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if author_id:
            conditions.append("author_id = :author_id")
            params["author_id"] = author_id
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT article_id, title, content, summary, category, article_type, status,
                       author_id, author_name, tags, keywords, view_count, helpful_count,
                       not_helpful_count, created_at, updated_at, published_at, version, metadata
                FROM knowledge_articles
                {where_clause}
                ORDER BY updated_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            articles = []
            for row in result:
                article = KnowledgeArticle(
                    article_id=row.article_id,
                    title=row.title,
                    content=row.content,
                    summary=row.summary or "",
                    category=ArticleCategory(row.category),
                    article_type=ArticleType(row.article_type),
                    status=ArticleStatus(row.status),
                    author_id=row.author_id,
                    author_name=row.author_name,
                    tags=row.tags or [],
                    keywords=row.keywords or [],
                    view_count=row.view_count,
                    helpful_count=row.helpful_count,
                    not_helpful_count=row.not_helpful_count,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    published_at=row.published_at,
                    version=row.version,
                    metadata=row.metadata or {}
                )
                articles.append(article)
            
            return articles

    async def get_popular_articles(self, limit: int = 10) -> List[KnowledgeArticle]:
        try:
            articles = []
            for article_id in self.popular_articles[:limit]:
                article = await self.get_article(article_id)
                if article:
                    articles.append(article)
            return articles
        except Exception as e:
            self.logger.error(f"Failed to get popular articles: {str(e)}")
            return []

    async def get_recent_searches(self, limit: int = 10) -> List[str]:
        return self.recent_searches[-limit:] if self.recent_searches else []

    async def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        try:
            suggestions = []
            query_lower = query.lower()
            
            for search_term in self.search_analytics.keys():
                if query_lower in search_term.lower() and search_term != query_lower:
                    suggestions.append(search_term)
            
            suggestions.sort(key=lambda x: self.search_analytics[x], reverse=True)
            return suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get search suggestions: {str(e)}")
            return []

    async def get_knowledge_base_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN status = 'published' THEN 1 END) as published_articles,
                    COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_articles,
                    COUNT(CASE WHEN category = 'technical' THEN 1 END) as technical_articles,
                    COUNT(CASE WHEN category = 'faq' THEN 1 END) as faq_articles,
                    COUNT(CASE WHEN category = 'tutorial' THEN 1 END) as tutorial_articles,
                    SUM(view_count) as total_views,
                    SUM(helpful_count) as total_helpful,
                    AVG(rating) as avg_rating
                FROM knowledge_articles
                LEFT JOIN article_feedback ON knowledge_articles.article_id = article_feedback.article_id
                WHERE knowledge_articles.created_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_articles": row.total_articles,
                "published_articles": row.published_articles,
                "draft_articles": row.draft_articles,
                "technical_articles": row.technical_articles,
                "faq_articles": row.faq_articles,
                "tutorial_articles": row.tutorial_articles,
                "total_views": row.total_views or 0,
                "total_helpful": row.total_helpful or 0,
                "avg_rating": float(row.avg_rating) if row.avg_rating else 0.0
            }

_knowledge_base: Optional[KnowledgeBase] = None

async def get_knowledge_base() -> KnowledgeBase:
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
        await _knowledge_base.initialize()
    return _knowledge_base

async def init_knowledge_base() -> KnowledgeBase:
    return await get_knowledge_base()
