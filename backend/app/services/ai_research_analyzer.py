"""
AI-powered research analysis service using multiple LLM providers.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from .mcp_client import MCPClient
from ..core.error_handling import get_error_handler, MCPError

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of AI analysis."""
    SUMMARY = "summary"
    INSIGHTS = "insights"
    SENTIMENT = "sentiment"
    TRENDS = "trends"
    COMPETITIVE = "competitive"
    MARKET_INTELLIGENCE = "market_intelligence"
    FACT_CHECK = "fact_check"
    ENTITY_EXTRACTION = "entity_extraction"


class LLMProvider(str, Enum):
    """Available LLM providers."""
    GROQ = "groq-llm"
    OPENROUTER = "openrouter-llm"
    DEEP_RESEARCH = "deep-research"


@dataclass
class AnalysisRequest:
    """AI analysis request configuration."""
    content: str
    analysis_type: AnalysisType
    context: Optional[str] = None
    preferred_provider: Optional[LLMProvider] = None
    max_tokens: int = 1000
    temperature: float = 0.7

    # Analysis-specific parameters
    extract_entities: bool = False
    include_confidence: bool = True
    language: str = "en"
    domain_expertise: Optional[str] = None


@dataclass
class AnalysisResult:
    """AI analysis result."""
    request_id: str
    analysis_type: AnalysisType
    provider_used: LLMProvider

    # Results
    analysis: str
    confidence_score: Optional[float] = None
    entities: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

    # Processing info
    processing_time_seconds: float = 0
    tokens_used: Optional[int] = None
    created_at: datetime = None


class AIResearchAnalyzer:
    """AI-powered research analysis service."""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.error_handler = get_error_handler()

        # Provider capabilities and preferences
        self.provider_capabilities = {
            LLMProvider.GROQ: {
                "strengths": ["fast_processing", "code_analysis", "technical_content"],
                "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                "max_tokens": 4096
            },
            LLMProvider.OPENROUTER: {
                "strengths": ["general_analysis", "creative_content", "multilingual"],
                "models": ["qwen/qwen3-235b-a22b-07-25:free", "microsoft/phi-3-mini-128k-instruct:free"],
                "max_tokens": 2048
            },
            LLMProvider.DEEP_RESEARCH: {
                "strengths": ["research_synthesis", "fact_checking", "comprehensive_analysis"],
                "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
                "max_tokens": 8192
            }
        }

    async def analyze_content(self, request: AnalysisRequest) -> AnalysisResult:
        """Perform AI analysis on content."""
        request_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()

        try:
            logger.info(
                f"Starting AI analysis {request_id}: {request.analysis_type.value}")

            # Select optimal provider
            provider = self._select_provider(request)

            # Perform analysis based on type
            if request.analysis_type == AnalysisType.SUMMARY:
                analysis_result = await self._generate_summary(request, provider)
            elif request.analysis_type == AnalysisType.INSIGHTS:
                analysis_result = await self._extract_insights(request, provider)
            elif request.analysis_type == AnalysisType.SENTIMENT:
                analysis_result = await self._analyze_sentiment(request, provider)
            elif request.analysis_type == AnalysisType.TRENDS:
                analysis_result = await self._analyze_trends(request, provider)
            elif request.analysis_type == AnalysisType.COMPETITIVE:
                analysis_result = await self._competitive_analysis(request, provider)
            elif request.analysis_type == AnalysisType.MARKET_INTELLIGENCE:
                analysis_result = await self._market_intelligence(request, provider)
            elif request.analysis_type == AnalysisType.FACT_CHECK:
                analysis_result = await self._fact_check(request, provider)
            elif request.analysis_type == AnalysisType.ENTITY_EXTRACTION:
                analysis_result = await self._extract_entities(request, provider)
            else:
                raise ValueError(
                    f"Unsupported analysis type: {request.analysis_type}")

            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            # Create result
            result = AnalysisResult(
                request_id=request_id,
                analysis_type=request.analysis_type,
                provider_used=provider,
                analysis=analysis_result.get("analysis", ""),
                confidence_score=analysis_result.get("confidence_score"),
                entities=analysis_result.get("entities"),
                metadata=analysis_result.get("metadata", {}),
                processing_time_seconds=processing_time,
                tokens_used=analysis_result.get("tokens_used"),
                created_at=start_time
            )

            logger.info(
                f"AI analysis {request_id} completed in {processing_time:.2f}s")
            return result

        except Exception as e:
            self.error_handler.handle_workflow_error(
                error=e,
                workflow_id="ai_analysis",
                execution_id=request_id,
                context={"analysis_type": request.analysis_type.value}
            )
            raise

    def _select_provider(self, request: AnalysisRequest) -> LLMProvider:
        """Select optimal LLM provider based on analysis type and requirements."""
        if request.preferred_provider:
            return request.preferred_provider

        # Provider selection logic based on analysis type
        provider_preferences = {
            AnalysisType.SUMMARY: LLMProvider.GROQ,
            AnalysisType.INSIGHTS: LLMProvider.DEEP_RESEARCH,
            AnalysisType.SENTIMENT: LLMProvider.OPENROUTER,
            AnalysisType.TRENDS: LLMProvider.DEEP_RESEARCH,
            AnalysisType.COMPETITIVE: LLMProvider.GROQ,
            AnalysisType.MARKET_INTELLIGENCE: LLMProvider.DEEP_RESEARCH,
            AnalysisType.FACT_CHECK: LLMProvider.DEEP_RESEARCH,
            AnalysisType.ENTITY_EXTRACTION: LLMProvider.GROQ
        }

        return provider_preferences.get(request.analysis_type, LLMProvider.GROQ)

    async def _generate_summary(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Generate content summary."""
        prompt = f"""
        Please provide a comprehensive summary of the following content:
        
        Context: {request.context or 'General content analysis'}
        
        Content:
        {request.content[:3000]}  # Limit content length
        
        Requirements:
        - Create a concise but comprehensive summary
        - Highlight key points and main themes
        - Include important statistics or data points
        - Maintain objectivity and accuracy
        - Format as clear, readable text
        """

        result = await self._call_llm(provider, prompt, request.max_tokens, request.temperature)

        return {
            "analysis": result.get("content", ""),
            "metadata": {
                "content_length": len(request.content),
                "summary_ratio": len(result.get("content", "")) / max(len(request.content), 1)
            }
        }

    async def _extract_insights(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Extract insights and patterns from content."""
        prompt = f"""
        Analyze the following content and extract key insights, patterns, and actionable intelligence:
        
        Context: {request.context or 'Business/research analysis'}
        Domain: {request.domain_expertise or 'General'}
        
        Content:
        {request.content[:3000]}
        
        Please provide:
        1. Key insights and findings
        2. Emerging patterns or trends
        3. Actionable recommendations
        4. Potential opportunities or risks
        5. Data-driven conclusions
        
        Format as structured analysis with clear sections.
        """

        result = await self._call_llm(provider, prompt, request.max_tokens, request.temperature)

        # Try to extract structured insights
        insights_text = result.get("content", "")
        structured_insights = self._parse_structured_insights(insights_text)

        return {
            "analysis": insights_text,
            "metadata": {
                "structured_insights": structured_insights,
                "insight_categories": len(structured_insights)
            }
        }

    async def _analyze_sentiment(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Analyze sentiment and emotional tone."""
        prompt = f"""
        Perform detailed sentiment analysis on the following content:
        
        Content:
        {request.content[:2000]}
        
        Please analyze:
        1. Overall sentiment (positive/negative/neutral)
        2. Emotional tone and intensity
        3. Key sentiment drivers
        4. Confidence level in assessment
        5. Sentiment distribution across different topics
        
        Provide sentiment score from -1 (very negative) to +1 (very positive).
        Include confidence score from 0 to 1.
        """

        # Lower temperature for consistency
        result = await self._call_llm(provider, prompt, request.max_tokens, 0.3)

        # Extract sentiment score and confidence
        sentiment_text = result.get("content", "")
        sentiment_score, confidence = self._parse_sentiment_scores(
            sentiment_text)

        return {
            "analysis": sentiment_text,
            "confidence_score": confidence,
            "metadata": {
                "sentiment_score": sentiment_score,
                "sentiment_category": self._categorize_sentiment(sentiment_score)
            }
        }

    async def _analyze_trends(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Analyze trends and patterns over time."""
        prompt = f"""
        Analyze the following content for trends, patterns, and temporal changes:
        
        Context: {request.context or 'Trend analysis'}
        
        Content:
        {request.content[:3000]}
        
        Please identify:
        1. Emerging trends and patterns
        2. Growth or decline indicators
        3. Cyclical patterns
        4. Anomalies or disruptions
        5. Future projections based on current trends
        6. Confidence level in trend identification
        
        Focus on data-driven observations and quantifiable trends where possible.
        """

        result = await self._call_llm(provider, prompt, request.max_tokens, request.temperature)

        return {
            "analysis": result.get("content", ""),
            "metadata": {
                "analysis_focus": "trend_identification",
                "temporal_scope": "historical_and_predictive"
            }
        }

    async def _competitive_analysis(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Perform competitive analysis."""
        prompt = f"""
        Conduct competitive analysis based on the following information:
        
        Context: {request.context or 'Competitive landscape analysis'}
        
        Content:
        {request.content[:3000]}
        
        Please analyze:
        1. Key competitors and market players
        2. Competitive advantages and disadvantages
        3. Market positioning and differentiation
        4. Pricing strategies and value propositions
        5. Strengths, weaknesses, opportunities, threats (SWOT)
        6. Competitive gaps and opportunities
        
        Provide actionable competitive intelligence.
        """

        result = await self._call_llm(provider, prompt, request.max_tokens, request.temperature)

        return {
            "analysis": result.get("content", ""),
            "metadata": {
                "analysis_type": "competitive_intelligence",
                "framework": "SWOT_and_positioning"
            }
        }

    async def _market_intelligence(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Generate market intelligence insights."""
        prompt = f"""
        Generate comprehensive market intelligence from the following data:
        
        Market/Industry: {request.context or 'General market'}
        
        Content:
        {request.content[:3000]}
        
        Please provide:
        1. Market size and growth potential
        2. Key market drivers and barriers
        3. Customer segments and behavior
        4. Industry dynamics and forces
        5. Regulatory and economic factors
        6. Investment and opportunity assessment
        7. Risk factors and mitigation strategies
        
        Focus on actionable business intelligence.
        """

        result = await self._call_llm(provider, prompt, request.max_tokens, request.temperature)

        return {
            "analysis": result.get("content", ""),
            "metadata": {
                "intelligence_type": "market_analysis",
                "scope": "comprehensive_market_assessment"
            }
        }

    async def _fact_check(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Perform fact-checking analysis."""
        if provider != LLMProvider.DEEP_RESEARCH:
            # Use deep-research for fact-checking
            try:
                fact_check_result = await self.mcp_client.call_tool(
                    server_name="deep-research",
                    tool_name="fact_check_research",
                    arguments={
                        "claim": request.content[:1000],
                        "sources_required": 3
                    }
                )

                if isinstance(fact_check_result, dict):
                    return {
                        "analysis": fact_check_result.get("analysis", ""),
                        "confidence_score": fact_check_result.get("confidence", 0.5),
                        "metadata": {
                            "sources_checked": fact_check_result.get("sources_count", 0),
                            "verification_status": fact_check_result.get("status", "unknown")
                        }
                    }
            except Exception as e:
                logger.warning(
                    f"Deep research fact-check failed, falling back to LLM: {e}")

        # Fallback to LLM-based fact checking
        prompt = f"""
        Perform fact-checking analysis on the following claims:
        
        Content to verify:
        {request.content[:2000]}
        
        Please:
        1. Identify specific factual claims
        2. Assess verifiability of each claim
        3. Note any potential inaccuracies or inconsistencies
        4. Provide confidence level for assessments
        5. Suggest additional verification needed
        
        Be objective and indicate uncertainty where appropriate.
        """

        # Low temperature for accuracy
        result = await self._call_llm(provider, prompt, request.max_tokens, 0.2)

        return {
            "analysis": result.get("content", ""),
            "metadata": {
                "verification_method": "llm_analysis",
                "requires_external_verification": True
            }
        }

    async def _extract_entities(self, request: AnalysisRequest, provider: LLMProvider) -> Dict[str, Any]:
        """Extract named entities and key information."""
        prompt = f"""
        Extract and categorize named entities from the following content:
        
        Content:
        {request.content[:2000]}
        
        Please identify and categorize:
        1. People (names, titles, roles)
        2. Organizations (companies, institutions)
        3. Locations (cities, countries, regions)
        4. Dates and times
        5. Products and services
        6. Technologies and concepts
        7. Financial figures and metrics
        
        Format as structured list with entity type and confidence level.
        """

        # Very low temperature for consistency
        result = await self._call_llm(provider, prompt, request.max_tokens, 0.1)

        # Parse entities from response
        entities_text = result.get("content", "")
        entities = self._parse_entities(entities_text)

        return {
            "analysis": entities_text,
            "entities": entities,
            "metadata": {
                "total_entities": len(entities),
                "entity_types": list(set(e.get("type", "") for e in entities))
            }
        }

    async def _call_llm(self, provider: LLMProvider, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Call the specified LLM provider."""
        try:
            if provider == LLMProvider.GROQ:
                return await self.mcp_client.call_tool(
                    server_name="groq-llm",
                    tool_name="groq_generate",
                    arguments={
                        "prompt": prompt,
                        "model": "llama-3.1-70b-versatile",
                        "max_tokens": min(max_tokens, 4096),
                        "temperature": temperature
                    }
                )
            elif provider == LLMProvider.OPENROUTER:
                return await self.mcp_client.call_tool(
                    server_name="openrouter-llm",
                    tool_name="openrouter_generate",
                    arguments={
                        "prompt": prompt,
                        "model": "qwen/qwen3-235b-a22b-07-25:free",
                        "max_tokens": min(max_tokens, 2048),
                        "temperature": temperature
                    }
                )
            elif provider == LLMProvider.DEEP_RESEARCH:
                return await self.mcp_client.call_tool(
                    server_name="deep-research",
                    tool_name="analyze_research_content",
                    arguments={
                        "content": prompt,
                        "research_question": "AI Analysis Request",
                        "analysis_type": "detailed"
                    }
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            raise MCPError(
                message=f"LLM call failed: {str(e)}",
                server_name=provider.value,
                is_retryable=True
            )

    def _parse_structured_insights(self, text: str) -> List[Dict[str, Any]]:
        """Parse structured insights from analysis text."""
        insights = []
        lines = text.split('\n')

        current_insight = {}
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_insight:
                    insights.append(current_insight)
                current_insight = {"text": line, "category": "insight"}
            elif line and current_insight:
                current_insight["text"] += " " + line

        if current_insight:
            insights.append(current_insight)

        return insights

    def _parse_sentiment_scores(self, text: str) -> tuple[float, float]:
        """Parse sentiment score and confidence from analysis text."""
        import re

        # Look for sentiment score patterns
        sentiment_patterns = [
            r'sentiment score[:\s]+(-?\d+\.?\d*)',
            r'score[:\s]+(-?\d+\.?\d*)',
            r'(-?\d+\.?\d*)\s*(?:out of|/)\s*[-+]?1'
        ]

        confidence_patterns = [
            r'confidence[:\s]+(\d+\.?\d*)',
            r'confidence level[:\s]+(\d+\.?\d*)'
        ]

        sentiment_score = 0.0
        confidence = 0.5

        for pattern in sentiment_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    sentiment_score = float(match.group(1))
                    break
                except ValueError:
                    continue

        for pattern in confidence_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    confidence = float(match.group(1))
                    if confidence > 1:
                        confidence = confidence / 100  # Convert percentage
                    break
                except ValueError:
                    continue

        return sentiment_score, confidence

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment score."""
        if score > 0.3:
            return "positive"
        elif score < -0.3:
            return "negative"
        else:
            return "neutral"

    def _parse_entities(self, text: str) -> List[Dict[str, Any]]:
        """Parse entities from analysis text."""
        entities = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if ':' in line and any(entity_type in line.lower() for entity_type in
                                   ['person', 'organization', 'location', 'date', 'product', 'technology']):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    entity_type = parts[0].strip()
                    entity_value = parts[1].strip()

                    entities.append({
                        "type": entity_type.lower(),
                        "value": entity_value,
                        "confidence": 0.8  # Default confidence
                    })

        return entities


# Factory function
def create_ai_research_analyzer() -> AIResearchAnalyzer:
    """Create an AI research analyzer instance."""
    from ..core.interfaces import MCPServerConfig
    
    # Create a dummy config for AI research analyzer
    dummy_config = MCPServerConfig(
        name="ai-research-analyzer",
        command="echo",
        args=["dummy"],
        env={}
    )
    
    mcp_client = MCPClient(dummy_config)
    return AIResearchAnalyzer(mcp_client)
