#!/usr/bin/env python3
"""
Comprehensive Ollama LLM Testing Suite
Tests heavy, long inputs and multiple concurrent requests
"""

import asyncio
import aiohttp
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaLLMTester:
    """Comprehensive tester for Ollama LLM with Llama 3 8B"""
    
    def __init__(self, base_url: str = "http://localhost:8008"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama service is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data}")
                    return {"healthy": True, "data": data}
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return {"healthy": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def test_simple_chat(self) -> Dict[str, Any]:
        """Test simple chat functionality"""
        logger.info("🧪 Testing simple chat...")
        
        test_message = "Hello! Can you tell me about artificial intelligence and its applications in business?"
        
        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/chat",
                json={
                    "message": test_message,
                    "max_tokens": 18000,
                    "temperature": 3.5
                },
                timeout=aiohttp.ClientTimeout(total=600)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Simple chat successful ({(response_time):.2f}s)")
                    return {
                        "success": True,
                        "response_time": response_time,
                        "response_length": len(data.get("response", "")),
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "response_preview": data.get("response", "")[:800] + "..."
                    }
                else:
                    logger.error(f"❌ Simple chat failed: {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"❌ Simple chat error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_heavy_long_input(self) -> Dict[str, Any]:
        """Test with heavy, long input"""
        logger.info("🧪 Testing heavy long input...")
        
        # Create a very long, complex business scenario
        long_input = """
        I'm the CEO of a rapidly growing fintech startup called "PayFlow Africa" that specializes in cross-border payments and digital banking solutions across 15 African countries. We currently have 2.3 million active users and process over $50 million in transactions monthly. Our team consists of 150 employees across engineering, product, marketing, sales, compliance, and customer support departments.
        
        We're facing several critical challenges that require strategic AI implementation:
        
        1. CUSTOMER SUPPORT SCALING: Our customer support team is overwhelmed with 15,000+ tickets per week. We need an AI system that can handle complex queries about international money transfers, regulatory compliance across different African jurisdictions, currency conversion issues, and technical troubleshooting for our mobile app and web platform.
        
        2. FRAUD DETECTION: We're experiencing increasing sophisticated fraud attempts including account takeovers, synthetic identity fraud, and money laundering schemes. We need advanced AI models to detect patterns in transaction behavior, user authentication patterns, and identify suspicious activities in real-time.
        
        3. REGULATORY COMPLIANCE: Each African country has different financial regulations, KYC requirements, and anti-money laundering laws. We need AI to help us stay compliant with local regulations, generate required reports, and ensure our operations meet the standards of central banks in Nigeria, Kenya, Ghana, South Africa, Uganda, Tanzania, Rwanda, and 8 other countries.
        
        4. MARKET ANALYSIS: We need to analyze market trends, competitor activities, and customer behavior patterns across different African markets to make informed decisions about product development, pricing strategies, and market expansion.
        
        5. RISK ASSESSMENT: We need AI to assess credit risk for our lending products, evaluate merchant risk for our payment processing services, and predict market volatility for our currency exchange services.
        
        6. PRODUCT DEVELOPMENT: We're planning to launch new products including cryptocurrency trading, insurance products, investment advisory services, and B2B payment solutions. We need AI to help with product design, market research, and user experience optimization.
        
        Our technical infrastructure includes:
        - Microservices architecture with 50+ services
        - Real-time data processing with Apache Kafka
        - Machine learning pipeline with TensorFlow and PyTorch
        - Cloud infrastructure on AWS with multi-region deployment
        - Mobile apps for iOS and Android with 4.8+ star ratings
        - Web platform with React frontend and Node.js backend
        - Database systems including PostgreSQL, MongoDB, and Redis
        - Integration with 200+ banks and financial institutions across Africa
        
        We have a budget of $2 million for AI implementation over the next 18 months and need to prioritize which AI solutions to implement first. Our board expects to see ROI within 12 months and wants to increase our user base to 5 million users while reducing operational costs by 30%.
        
        Please provide a comprehensive AI strategy that addresses our most critical needs, includes implementation timelines, resource requirements, expected ROI, and risk mitigation strategies. Consider the unique challenges of operating in African markets including infrastructure limitations, regulatory complexity, and diverse customer needs across different countries.
        """
        
        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/chat",
                json={
                    "message": long_input,
                    "max_tokens": 20000,
                    "temperature": 3.5,
                    "top_p": 1.9
                },
                timeout=aiohttp.ClientTimeout(total=900)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    logger.info(f"✅ Heavy input successful ({(response_time):.2f}s, {len(response_text)} chars)")
                    return {
                        "success": True,
                        "response_time": response_time,
                        "input_length": len(long_input),
                        "response_length": len(response_text),
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "response_preview": response_text[:700] + "...",
                        "quality_indicators": {
                            "mentions_ai_strategy": "AI strategy" in response_text,
                            "mentions_implementation": "implementation" in response_text.lower(),
                            "mentions_roi": "ROI" in response_text or "return on investment" in response_text.lower(),
                            "mentions_africa": "Africa" in response_text,
                            "mentions_fintech": "fintech" in response_text.lower()
                        }
                    }
                else:
                    logger.error(f"❌ Heavy input failed: {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"❌ Heavy input error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_concurrent_requests(self, num_requests: int = 10) -> Dict[str, Any]:
        """Test multiple concurrent requests"""
        logger.info(f"🧪 Testing {num_requests} concurrent requests...")
        
        async def single_request(request_id: int) -> Dict[str, Any]:
            test_message = f"Request #{request_id}: Explain the benefits of AI in business automation and provide specific examples for a {['retail', 'healthcare', 'finance', 'education', 'manufacturing'][request_id % 5]} company."
            
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{self.base_url}/chat",
                    json={
                        "message": test_message,
                        "max_tokens": 15000,
                        "temperature": 3.0
                    },
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "request_id": request_id,
                            "success": True,
                            "response_time": response_time,
                            "response_length": len(data.get("response", "")),
                            "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                        }
                    else:
                        return {
                            "request_id": request_id,
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "response_time": response_time
                        }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "response_time": 0
                }
        
        # Run concurrent requests
        start_time = time.time()
        tasks = [single_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            total_tokens = sum(r["tokens_used"] for r in successful_requests)
        else:
            avg_response_time = min_response_time = max_response_time = total_tokens = 0
        
        logger.info(f"✅ Concurrent test completed: {len(successful_requests)}/{num_requests} successful")
        
        return {
            "success": len(successful_requests) > 0,
            "total_requests": num_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "total_tokens_generated": total_tokens,
            "requests_per_second": num_requests / total_time if total_time > 0 else 0,
            "failed_details": failed_requests
        }
    
    async def test_domain_expertise(self) -> Dict[str, Any]:
        """Test domain expertise across different business areas"""
        logger.info("🧪 Testing domain expertise...")
        
        domains = [
            {
                "name": "Sales & Marketing",
                "question": "Create a comprehensive sales strategy for a B2B SaaS company targeting enterprise clients in the healthcare industry. Include lead generation, qualification, proposal development, and closing techniques."
            },
            {
                "name": "Content Creation",
                "question": "Develop a content marketing strategy for a fintech startup launching a new mobile payment app. Include content types, distribution channels, SEO optimization, and engagement tactics."
            },
            {
                "name": "Research & Analysis",
                "question": "Analyze the competitive landscape for AI-powered customer service solutions in the e-commerce sector. Include market size, key players, pricing models, and differentiation strategies."
            },
            {
                "name": "Business Development",
                "question": "Create a partnership strategy for a logistics company looking to expand into emerging markets. Include partnership types, selection criteria, negotiation tactics, and success metrics."
            },
            {
                "name": "Financial Planning",
                "question": "Develop a financial model for a subscription-based software company with 10,000 customers, $2M ARR, and plans to scale to $10M ARR in 3 years. Include revenue projections, cost structure, and funding requirements."
            }
        ]
        
        results = []
        for domain in domains:
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{self.base_url}/chat",
                    json={
                        "message": domain["question"],
                        "max_tokens": 20000,
                        "temperature": 3.5
                    },
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get("response", "")
                        results.append({
                            "domain": domain["name"],
                            "success": True,
                            "response_time": response_time,
                            "response_length": len(response_text),
                            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                            "quality_score": self._assess_response_quality(response_text, domain["name"])
                        })
                        logger.info(f"✅ {domain['name']} expertise test passed")
                    else:
                        results.append({
                            "domain": domain["name"],
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "response_time": response_time
                        })
                        logger.error(f"❌ {domain['name']} expertise test failed")
            except Exception as e:
                results.append({
                    "domain": domain["name"],
                    "success": False,
                    "error": str(e),
                    "response_time": 0
                })
                logger.error(f"❌ {domain['name']} expertise test error: {e}")
        
        successful_domains = [r for r in results if r["success"]]
        avg_quality_score = statistics.mean([r["quality_score"] for r in successful_domains]) if successful_domains else 0
        
        return {
            "success": len(successful_domains) > 0,
            "domains_tested": len(domains),
            "successful_domains": len(successful_domains),
            "avg_quality_score": avg_quality_score,
            "domain_results": results
        }
    
    def _assess_response_quality(self, response_text: str, domain: str) -> float:
        """Assess the quality of a response (0-10 scale)"""
        score = 5.0  # Base score
        
        # Length and detail
        if len(response_text) > 500:
            score += 1.0
        if len(response_text) > 1000:
            score += 1.0
        
        # Domain-specific keywords
        domain_keywords = {
            "Sales & Marketing": ["strategy", "leads", "conversion", "ROI", "campaign"],
            "Content Creation": ["content", "SEO", "engagement", "distribution", "audience"],
            "Research & Analysis": ["analysis", "market", "competitors", "data", "trends"],
            "Business Development": ["partnership", "collaboration", "expansion", "growth", "alliance"],
            "Financial Planning": ["revenue", "costs", "projections", "budget", "financial"]
        }
        
        keywords = domain_keywords.get(domain, [])
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in response_text.lower())
        score += min(keyword_matches * 0.5, 2.0)
        
        # Structure and organization
        if any(indicator in response_text for indicator in ["1.", "2.", "3.", "•", "-"]):
            score += 1.0
        
        return min(score, 10.0)
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        logger.info("🚀 Starting comprehensive Ollama LLM testing...")
        
        start_time = time.time()
        
        # Run all tests
        health_result = await self.health_check()
        simple_chat_result = await self.test_simple_chat()
        heavy_input_result = await self.test_heavy_long_input()
        concurrent_result = await self.test_concurrent_requests(15)
        domain_expertise_result = await self.test_domain_expertise()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        report = {
            "test_summary": {
                "total_test_time": total_time,
                "timestamp": datetime.now().isoformat(),
                "ollama_service_healthy": health_result["healthy"]
            },
            "test_results": {
                "health_check": health_result,
                "simple_chat": simple_chat_result,
                "heavy_input": heavy_input_result,
                "concurrent_requests": concurrent_result,
                "domain_expertise": domain_expertise_result
            },
            "performance_metrics": {
                "avg_response_time": statistics.mean([
                    simple_chat_result.get("response_time", 0),
                    heavy_input_result.get("response_time", 0),
                    concurrent_result.get("avg_response_time", 0)
                ]) if any([
                    simple_chat_result.get("response_time", 0),
                    heavy_input_result.get("response_time", 0),
                    concurrent_result.get("avg_response_time", 0)
                ]) else 0,
                "total_tokens_generated": sum([
                    simple_chat_result.get("tokens_used", 0),
                    heavy_input_result.get("tokens_used", 0),
                    concurrent_result.get("total_tokens_generated", 0)
                ]),
                "success_rate": len([r for r in [
                    simple_chat_result,
                    heavy_input_result,
                    concurrent_result,
                    domain_expertise_result
                ] if r.get("success", False)]) / 4 * 100
            },
            "recommendations": self._generate_recommendations({
                "health_check": health_result,
                "simple_chat": simple_chat_result,
                "heavy_input": heavy_input_result,
                "concurrent_requests": concurrent_result,
                "domain_expertise": domain_expertise_result
            })
        }
        
        return report
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not results["health_check"]["healthy"]:
            recommendations.append("🔧 Fix Ollama service health issues before proceeding")
        
        if results["simple_chat"].get("response_time", 0) > 10:
            recommendations.append("⚡ Simple chat response time is slow - consider optimization")
        
        if results["heavy_input"].get("response_time", 0) > 30:
            recommendations.append("⚡ Heavy input processing is slow - may need more resources")
        
        if results["concurrent_requests"].get("success_rate", 0) < 80:
            recommendations.append("🔄 Concurrent request handling needs improvement")
        
        if results["domain_expertise"].get("avg_quality_score", 0) < 7:
            recommendations.append("📚 Consider fine-tuning for better domain expertise")
        
        if not recommendations:
            recommendations.append("✅ All tests passed! Ollama LLM is ready for production use")
        
        return recommendations

async def main():
    """Main test execution"""
    print("🧪 Ollama LLM Comprehensive Testing Suite")
    print("=" * 50)
    
    async with OllamaLLMTester() as tester:
        report = await tester.run_comprehensive_test()
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print(f"Total test time: {report['test_summary']['total_test_time']:.2f} seconds")
        print(f"Ollama service healthy: {report['test_summary']['ollama_service_healthy']}")
        print(f"Overall success rate: {report['performance_metrics']['success_rate']:.1f}%")
        print(f"Average response time: {report['performance_metrics']['avg_response_time']:.2f} seconds")
        print(f"Total tokens generated: {report['performance_metrics']['total_tokens_generated']}")
        
        print(f"\n💡 RECOMMENDATIONS")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        # Save detailed report
        with open("tests/e2e/ollama_llm_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: tests/e2e/ollama_llm_test_report.json")
        
        return report

if __name__ == "__main__":
    asyncio.run(main())
