"""
Research API routes for web research and browser automation.
"""
from ..services.privacy_security_service import (
    PrivacySecurityService, SensitivityLevel, DataType,
    create_privacy_security_service
)
from ..services.ai_research_analyzer import (
    AIResearchAnalyzer, AnalysisRequest, AnalysisType, LLMProvider,
    create_ai_research_analyzer
)
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from ..services.research_service import (
    ResearchService, ResearchRequest, ResearchResult, ResearchType,
    create_research_service
)
from ..core.auth import get_current_user

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequestModel(BaseModel):
    """API model for research requests."""
    query: str = Field(..., description="Research query or topic")
    research_type: ResearchType = Field(
        default=ResearchType.WEB_SEARCH, description="Type of research")
    depth: int = Field(default=3, ge=1, le=5,
                       description="Research depth (1-5)")
    max_sources: int = Field(default=10, ge=1, le=50,
                             description="Maximum sources to analyze")
    include_screenshots: bool = Field(
        default=False, description="Include screenshots")
    extract_structured_data: bool = Field(
        default=True, description="Extract structured data")
    privacy_mode: bool = Field(
        default=True, description="Apply privacy filters")
    timeout_seconds: int = Field(
        default=300, ge=30, le=1800, description="Timeout in seconds")

    # Optional parameters
    target_domains: Optional[List[str]] = Field(
        None, description="Target domains to focus on")
    exclude_domains: Optional[List[str]] = Field(
        None, description="Domains to exclude")
    language: str = Field(default="en", description="Language preference")
    region: Optional[str] = Field(None, description="Geographic region")


class ResearchStatusModel(BaseModel):
    """API model for research status."""
    request_id: str
    query: str
    research_type: str
    status: str
    total_sources: int
    processing_time_seconds: float
    created_at: str
    completed_at: Optional[str]
    sensitive_data_detected: bool


def get_research_service() -> ResearchService:
    """Get research service instance."""
    return create_research_service()


@router.post("/", response_model=dict)
async def start_research(
    request: ResearchRequestModel,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Start a new research operation."""
    try:
        # Convert API model to service model
        research_request = ResearchRequest(
            query=request.query,
            research_type=request.research_type,
            depth=request.depth,
            max_sources=request.max_sources,
            include_screenshots=request.include_screenshots,
            extract_structured_data=request.extract_structured_data,
            privacy_mode=request.privacy_mode,
            timeout_seconds=request.timeout_seconds,
            target_domains=request.target_domains,
            exclude_domains=request.exclude_domains,
            language=request.language,
            region=request.region
        )

        # Start research in background
        result = await research_service.conduct_research(research_request)

        return {
            "request_id": result.request_id,
            "status": result.status,
            "message": "Research started successfully",
            "estimated_completion": f"{request.timeout_seconds} seconds"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start research: {str(e)}"
        )


@router.get("/{request_id}/status", response_model=ResearchStatusModel)
async def get_research_status(
    request_id: str,
    research_service: ResearchService = Depends(get_research_service)
):
    """Get status of a research operation."""
    status_info = await research_service.get_research_status(request_id)

    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research request not found"
        )

    return ResearchStatusModel(**status_info)


@router.get("/{request_id}/results", response_model=dict)
async def get_research_results(
    request_id: str,
    include_content: bool = False,
    research_service: ResearchService = Depends(get_research_service)
):
    """Get results of a completed research operation."""
    result = research_service.active_research.get(request_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research request not found"
        )

    if result.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research is still {result.status}. Use /status endpoint to check progress."
        )

    # Prepare response
    response = {
        "request_id": result.request_id,
        "query": result.query,
        "research_type": result.research_type.value,
        "status": result.status,
        "total_sources": result.total_sources,
        "processing_time_seconds": result.processing_time_seconds,
        "created_at": result.created_at.isoformat() if result.created_at else None,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        "sensitive_data_detected": result.sensitive_data_detected
    }

    # Add summary and insights
    if result.summary:
        response["summary"] = result.summary

    if result.insights:
        response["insights"] = result.insights

    if result.structured_data:
        response["structured_data"] = result.structured_data

    # Add sources (with optional content)
    sources = []
    for source in result.sources:
        source_data = {
            "url": source.get("url", ""),
            "title": source.get("title", ""),
            "source_type": source.get("source_type", ""),
            "relevance_score": source.get("relevance_score", 0),
            "extracted_at": source.get("extracted_at", "")
        }

        # Include snippet/summary by default
        if "snippet" in source:
            source_data["snippet"] = source["snippet"]
        if "summary" in source:
            source_data["summary"] = source["summary"]

        # Include full content only if requested
        if include_content and "content" in source:
            source_data["content"] = source["content"]

        # Include additional metadata
        for key in ["credibility_score", "screenshot", "privacy_filtered"]:
            if key in source:
                source_data[key] = source[key]

        sources.append(source_data)

    response["sources"] = sources

    # Add privacy information
    if result.redacted_content:
        response["privacy_info"] = {
            "sensitive_patterns_found": len(result.redacted_content),
            "redaction_applied": True
        }

    return response


@router.post("/{request_id}/cancel", response_model=dict)
async def cancel_research(
    request_id: str,
    research_service: ResearchService = Depends(get_research_service)
):
    """Cancel a running research operation."""
    success = await research_service.cancel_research(request_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research request not found or already completed"
        )

    return {"message": "Research cancelled successfully"}


@router.get("/types", response_model=List[dict])
async def get_research_types():
    """Get available research types."""
    return [
        {
            "type": ResearchType.WEB_SEARCH.value,
            "name": "Web Search",
            "description": "Basic web search using browser automation",
            "estimated_time": "30-60 seconds",
            "max_sources": 50
        },
        {
            "type": ResearchType.DEEP_RESEARCH.value,
            "name": "Deep Research",
            "description": "Comprehensive research with AI analysis",
            "estimated_time": "2-5 minutes",
            "max_sources": 20
        },
        {
            "type": ResearchType.COMPETITIVE_ANALYSIS.value,
            "name": "Competitive Analysis",
            "description": "Analyze competitors and market positioning",
            "estimated_time": "3-8 minutes",
            "max_sources": 15
        },
        {
            "type": ResearchType.CONTENT_EXTRACTION.value,
            "name": "Content Extraction",
            "description": "Extract content from specific URLs",
            "estimated_time": "1-3 minutes",
            "max_sources": 10
        }
    ]


@router.post("/quick-search", response_model=dict)
async def quick_search(
    query: str,
    max_results: int = 5,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service)
):
    """Perform a quick web search (synchronous)."""
    try:
        # Create a simple research request
        request = ResearchRequest(
            query=query,
            research_type=ResearchType.WEB_SEARCH,
            max_sources=max_results,
            extract_structured_data=False,
            timeout_seconds=60
        )

        # Execute research
        result = await research_service.conduct_research(request)

        # Return simplified results
        return {
            "query": query,
            "total_results": len(result.sources),
            "processing_time": result.processing_time_seconds,
            "results": [
                {
                    "title": source.get("title", ""),
                    "url": source.get("url", ""),
                    "snippet": source.get("snippet", ""),
                    "relevance_score": source.get("relevance_score", 0)
                }
                for source in result.sources[:max_results]
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quick search failed: {str(e)}"
        )


class AIAnalysisRequestModel(BaseModel):
    """API model for AI analysis requests."""
    content: str = Field(..., description="Content to analyze")
    analysis_type: AnalysisType = Field(...,
                                        description="Type of analysis to perform")
    context: Optional[str] = Field(
        None, description="Additional context for analysis")
    preferred_provider: Optional[LLMProvider] = Field(
        None, description="Preferred LLM provider")
    max_tokens: int = Field(default=1000, ge=100, le=4000,
                            description="Maximum tokens for response")
    temperature: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Temperature for generation")

    # Analysis-specific parameters
    extract_entities: bool = Field(
        default=False, description="Extract named entities")
    include_confidence: bool = Field(
        default=True, description="Include confidence scores")
    language: str = Field(default="en", description="Content language")
    domain_expertise: Optional[str] = Field(
        None, description="Domain expertise context")


def get_ai_analyzer() -> AIResearchAnalyzer:
    """Get AI research analyzer instance."""
    return create_ai_research_analyzer()


@router.post("/analyze", response_model=dict)
async def analyze_content(
    request: AIAnalysisRequestModel,
    current_user: dict = Depends(get_current_user),
    ai_analyzer: AIResearchAnalyzer = Depends(get_ai_analyzer)
):
    """Perform AI analysis on content."""
    try:
        # Convert API model to service model
        analysis_request = AnalysisRequest(
            content=request.content,
            analysis_type=request.analysis_type,
            context=request.context,
            preferred_provider=request.preferred_provider,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            extract_entities=request.extract_entities,
            include_confidence=request.include_confidence,
            language=request.language,
            domain_expertise=request.domain_expertise
        )

        # Perform analysis
        result = await ai_analyzer.analyze_content(analysis_request)

        # Prepare response
        response = {
            "request_id": result.request_id,
            "analysis_type": result.analysis_type.value,
            "provider_used": result.provider_used.value,
            "analysis": result.analysis,
            "processing_time_seconds": result.processing_time_seconds,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }

        # Add optional fields
        if result.confidence_score is not None:
            response["confidence_score"] = result.confidence_score

        if result.entities:
            response["entities"] = result.entities

        if result.metadata:
            response["metadata"] = result.metadata

        if result.tokens_used:
            response["tokens_used"] = result.tokens_used

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.get("/analysis-types", response_model=List[dict])
async def get_analysis_types():
    """Get available AI analysis types."""
    return [
        {
            "type": AnalysisType.SUMMARY.value,
            "name": "Content Summary",
            "description": "Generate comprehensive summary of content",
            "use_cases": ["Document summarization", "Article condensation", "Report overview"],
            "estimated_time": "10-30 seconds"
        },
        {
            "type": AnalysisType.INSIGHTS.value,
            "name": "Insights Extraction",
            "description": "Extract key insights and actionable intelligence",
            "use_cases": ["Business intelligence", "Research analysis", "Strategic planning"],
            "estimated_time": "20-60 seconds"
        },
        {
            "type": AnalysisType.SENTIMENT.value,
            "name": "Sentiment Analysis",
            "description": "Analyze emotional tone and sentiment",
            "use_cases": ["Social media monitoring", "Customer feedback", "Brand perception"],
            "estimated_time": "10-20 seconds"
        },
        {
            "type": AnalysisType.TRENDS.value,
            "name": "Trend Analysis",
            "description": "Identify patterns and trends over time",
            "use_cases": ["Market analysis", "Performance tracking", "Forecasting"],
            "estimated_time": "30-90 seconds"
        },
        {
            "type": AnalysisType.COMPETITIVE.value,
            "name": "Competitive Analysis",
            "description": "Analyze competitive landscape and positioning",
            "use_cases": ["Market research", "Competitor intelligence", "SWOT analysis"],
            "estimated_time": "45-120 seconds"
        },
        {
            "type": AnalysisType.MARKET_INTELLIGENCE.value,
            "name": "Market Intelligence",
            "description": "Generate comprehensive market insights",
            "use_cases": ["Investment research", "Market entry", "Business development"],
            "estimated_time": "60-180 seconds"
        },
        {
            "type": AnalysisType.FACT_CHECK.value,
            "name": "Fact Checking",
            "description": "Verify factual claims and accuracy",
            "use_cases": ["Content verification", "Research validation", "Due diligence"],
            "estimated_time": "30-90 seconds"
        },
        {
            "type": AnalysisType.ENTITY_EXTRACTION.value,
            "name": "Entity Extraction",
            "description": "Extract named entities and key information",
            "use_cases": ["Data mining", "Information extraction", "Knowledge graphs"],
            "estimated_time": "15-45 seconds"
        }
    ]


@router.get("/providers", response_model=List[dict])
async def get_llm_providers():
    """Get available LLM providers and their capabilities."""
    return [
        {
            "provider": LLMProvider.GROQ.value,
            "name": "Groq",
            "description": "Ultra-fast LLM processing with high-quality models",
            "strengths": ["Fast processing", "Code analysis", "Technical content"],
            "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            "max_tokens": 4096,
            "best_for": ["Quick analysis", "Technical content", "Code review"]
        },
        {
            "provider": LLMProvider.OPENROUTER.value,
            "name": "OpenRouter",
            "description": "Access to multiple free and premium models",
            "strengths": ["General analysis", "Creative content", "Multilingual"],
            "models": ["qwen/qwen3-235b-a22b-07-25:free", "microsoft/phi-3-mini-128k-instruct:free"],
            "max_tokens": 2048,
            "best_for": ["General analysis", "Creative tasks", "Multilingual content"]
        },
        {
            "provider": LLMProvider.DEEP_RESEARCH.value,
            "name": "Deep Research",
            "description": "Specialized research and analysis capabilities",
            "strengths": ["Research synthesis", "Fact checking", "Comprehensive analysis"],
            "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
            "max_tokens": 8192,
            "best_for": ["Research analysis", "Fact checking", "Comprehensive insights"]
        }
    ]


@router.post("/batch-analyze", response_model=List[dict])
async def batch_analyze_content(
    requests: List[AIAnalysisRequestModel],
    current_user: dict = Depends(get_current_user),
    ai_analyzer: AIResearchAnalyzer = Depends(get_ai_analyzer)
):
    """Perform batch AI analysis on multiple content pieces."""
    if len(requests) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 requests allowed in batch"
        )

    try:
        results = []

        # Process requests concurrently
        tasks = []
        for req in requests:
            analysis_request = AnalysisRequest(
                content=req.content,
                analysis_type=req.analysis_type,
                context=req.context,
                preferred_provider=req.preferred_provider,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                extract_entities=req.extract_entities,
                include_confidence=req.include_confidence,
                language=req.language,
                domain_expertise=req.domain_expertise
            )
            tasks.append(ai_analyzer.analyze_content(analysis_request))

        # Execute all analyses
        analysis_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(analysis_results):
            if isinstance(result, Exception):
                results.append({
                    "index": i,
                    "status": "failed",
                    "error": str(result)
                })
            else:
                results.append({
                    "index": i,
                    "status": "completed",
                    "request_id": result.request_id,
                    "analysis_type": result.analysis_type.value,
                    "provider_used": result.provider_used.value,
                    "analysis": result.analysis,
                    "confidence_score": result.confidence_score,
                    "processing_time_seconds": result.processing_time_seconds
                })

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


class PrivacyAnalysisRequestModel(BaseModel):
    """API model for privacy analysis requests."""
    content: str = Field(...,
                         description="Content to analyze for privacy issues")
    content_id: Optional[str] = Field(
        None, description="Optional content identifier")
    include_redacted: bool = Field(
        default=True, description="Include redacted content in response")
    include_recommendations: bool = Field(
        default=True, description="Include privacy recommendations")


def get_privacy_service() -> PrivacySecurityService:
    """Get privacy security service instance."""
    return create_privacy_security_service()


@router.post("/privacy/analyze", response_model=dict)
async def analyze_privacy(
    request: PrivacyAnalysisRequestModel,
    current_user: dict = Depends(get_current_user),
    privacy_service: PrivacySecurityService = Depends(get_privacy_service)
):
    """Analyze content for privacy and security issues."""
    try:
        # Perform privacy analysis
        report = await privacy_service.analyze_privacy(
            content=request.content,
            content_id=request.content_id
        )

        # Prepare response
        response = {
            "content_id": report.content_id,
            "total_matches": report.total_matches,
            "sensitivity_level": report.sensitivity_level.value,
            "processing_time_seconds": report.processing_time_seconds,
            "created_at": report.created_at.isoformat()
        }

        # Add matches information
        matches_info = []
        for match in report.matches:
            match_info = {
                "data_type": match.data_type.value,
                "confidence": match.confidence,
                "severity": match.severity.value,
                "context": match.context[:100] + "..." if len(match.context) > 100 else match.context
            }
            # Don't include actual sensitive values in API response
            matches_info.append(match_info)

        response["matches"] = matches_info

        # Add redacted content if requested
        if request.include_redacted:
            response["redacted_content"] = report.redacted_content

        # Add recommendations if requested
        if request.include_recommendations:
            response["recommendations"] = report.recommendations

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Privacy analysis failed: {str(e)}"
        )


@router.post("/privacy/score", response_model=dict)
async def get_privacy_score(
    content: str,
    current_user: dict = Depends(get_current_user),
    privacy_service: PrivacySecurityService = Depends(get_privacy_service)
):
    """Get privacy score for content."""
    try:
        score_info = await privacy_service.get_privacy_score(content)
        return score_info

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Privacy scoring failed: {str(e)}"
        )


@router.get("/privacy/data-types", response_model=List[dict])
async def get_data_types():
    """Get supported sensitive data types."""
    return [
        {
            "type": DataType.API_KEY.value,
            "name": "API Keys",
            "description": "API keys, access tokens, and authentication credentials"
        }
    ]
