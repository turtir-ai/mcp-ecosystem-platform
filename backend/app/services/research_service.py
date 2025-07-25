"""
Research service for web automation and data extraction using MCP servers.
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
from ..core.interfaces import MCPServerConfig

logger = logging.getLogger(__name__)


class ResearchType(str, Enum):
    """Types of research operations."""
    WEB_SEARCH = "web_search"
    DEEP_RESEARCH = "deep_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    MARKET_INTELLIGENCE = "market_intelligence"
    CONTENT_EXTRACTION = "content_extraction"
    SCREENSHOT_ANALYSIS = "screenshot_analysis"


@dataclass
class ResearchRequest:
    """Research request configuration."""
    query: str
    research_type: ResearchType
    depth: int = 3
    max_sources: int = 10
    include_screenshots: bool = False
    extract_structured_data: bool = True
    privacy_mode: bool = True
    timeout_seconds: int = 300

    # Additional parameters
    target_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    language: str = "en"
    region: Optional[str] = None


@dataclass
class ResearchResult:
    """Research operation result."""
    request_id: str
    query: str
    research_type: ResearchType
    status: str

    # Results
    sources: List[Dict[str, Any]]
    summary: Optional[str] = None
    insights: Optional[Dict[str, Any]] = None
    structured_data: Optional[Dict[str, Any]] = None
    screenshots: Optional[List[str]] = None

    # Metadata
    total_sources: int = 0
    processing_time_seconds: float = 0
    created_at: datetime = None
    completed_at: Optional[datetime] = None

    # Privacy and security
    sensitive_data_detected: bool = False
    redacted_content: Optional[List[str]] = None


class ResearchService:
    """Service for web research and browser automation."""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.error_handler = get_error_handler()
        self.active_research: Dict[str, ResearchResult] = {}

    async def conduct_research(self, request: ResearchRequest) -> ResearchResult:
        """Conduct comprehensive web research."""
        request_id = f"research_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Initialize result
        result = ResearchResult(
            request_id=request_id,
            query=request.query,
            research_type=request.research_type,
            status="running",
            sources=[],
            created_at=datetime.utcnow()
        )

        self.active_research[request_id] = result

        try:
            logger.info(f"Starting research {request_id}: {request.query}")
            start_time = datetime.utcnow()

            # Execute research based on type
            if request.research_type == ResearchType.WEB_SEARCH:
                await self._conduct_web_search(request, result)
            elif request.research_type == ResearchType.DEEP_RESEARCH:
                await self._conduct_deep_research(request, result)
            elif request.research_type == ResearchType.COMPETITIVE_ANALYSIS:
                await self._conduct_competitive_analysis(request, result)
            elif request.research_type == ResearchType.CONTENT_EXTRACTION:
                await self._conduct_content_extraction(request, result)
            else:
                raise ValueError(
                    f"Unsupported research type: {request.research_type}")

            # Post-processing
            if request.privacy_mode:
                await self._apply_privacy_filters(result)

            if request.extract_structured_data:
                await self._extract_structured_data(result)

            # Calculate processing time
            end_time = datetime.utcnow()
            result.processing_time_seconds = (
                end_time - start_time).total_seconds()
            result.completed_at = end_time
            result.status = "completed"

            logger.info(
                f"Research {request_id} completed in {result.processing_time_seconds:.2f}s")

        except Exception as e:
            result.status = "failed"
            result.completed_at = datetime.utcnow()

            # Log error
            self.error_handler.handle_workflow_error(
                error=e,
                workflow_id="research",
                execution_id=request_id,
                context={"query": request.query,
                         "type": request.research_type.value}
            )

            logger.error(f"Research {request_id} failed: {e}")
            raise

        return result

    async def _conduct_web_search(self, request: ResearchRequest, result: ResearchResult):
        """Conduct basic web search using browser automation."""
        try:
            # Use browser-automation MCP server
            search_result = await self.mcp_client.call_tool(
                server_name="browser-automation",
                tool_name="search_web",
                arguments={
                    "task": request.query,
                    "max_results": request.max_sources
                }
            )

            # Process search results
            if isinstance(search_result, dict) and "results" in search_result:
                for item in search_result["results"][:request.max_sources]:
                    source = {
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "source_type": "web_search",
                        "relevance_score": item.get("score", 0.5),
                        "extracted_at": datetime.utcnow().isoformat()
                    }
                    result.sources.append(source)

            result.total_sources = len(result.sources)

        except Exception as e:
            raise MCPError(
                message=f"Web search failed: {str(e)}",
                server_name="browser-automation",
                tool_name="search_web"
            )

    async def _conduct_deep_research(self, request: ResearchRequest, result: ResearchResult):
        """Conduct deep research using deep-research MCP server."""
        try:
            # Use deep-research MCP server
            research_result = await self.mcp_client.call_tool(
                server_name="deep-research",
                tool_name="comprehensive_web_research",
                arguments={
                    "query": request.query,
                    "depth": request.depth,
                    "sources_per_query": request.max_sources
                }
            )

            # Process deep research results
            if isinstance(research_result, dict):
                # Extract sources
                if "sources" in research_result:
                    for source in research_result["sources"]:
                        processed_source = {
                            "url": source.get("url", ""),
                            "title": source.get("title", ""),
                            "content": source.get("content", ""),
                            "summary": source.get("summary", ""),
                            "source_type": "deep_research",
                            "relevance_score": source.get("relevance", 0.5),
                            "credibility_score": source.get("credibility", 0.5),
                            "extracted_at": datetime.utcnow().isoformat()
                        }
                        result.sources.append(processed_source)

                # Extract insights
                if "insights" in research_result:
                    result.insights = research_result["insights"]

                # Extract summary
                if "summary" in research_result:
                    result.summary = research_result["summary"]

            result.total_sources = len(result.sources)

        except Exception as e:
            raise MCPError(
                message=f"Deep research failed: {str(e)}",
                server_name="deep-research",
                tool_name="comprehensive_web_research"
            )

    async def _conduct_competitive_analysis(self, request: ResearchRequest, result: ResearchResult):
        """Conduct competitive analysis research."""
        try:
            # First, get basic web search results
            await self._conduct_web_search(request, result)

            # Then enhance with competitive intelligence
            competitors = []
            for source in result.sources[:5]:  # Analyze top 5 sources
                try:
                    # Extract competitive information
                    analysis_result = await self.mcp_client.call_tool(
                        server_name="groq-llm",
                        tool_name="groq_generate",
                        arguments={
                            "prompt": f"Analyze this content for competitive intelligence about '{request.query}': {source.get('snippet', '')}",
                            "model": "llama-3.1-70b-versatile",
                            "max_tokens": 500
                        }
                    )

                    if isinstance(analysis_result, dict) and "content" in analysis_result:
                        competitors.append({
                            "source_url": source["url"],
                            "analysis": analysis_result["content"],
                            "analyzed_at": datetime.utcnow().isoformat()
                        })

                except Exception as e:
                    logger.warning(
                        f"Failed to analyze competitor source {source['url']}: {e}")

            # Store competitive insights
            result.insights = {
                "competitive_analysis": competitors,
                "total_competitors_analyzed": len(competitors)
            }

        except Exception as e:
            raise MCPError(
                message=f"Competitive analysis failed: {str(e)}",
                server_name="multiple"
            )

    async def _conduct_content_extraction(self, request: ResearchRequest, result: ResearchResult):
        """Extract content from specific URLs."""
        try:
            # Assume query contains URLs or domains to extract from
            urls = self._extract_urls_from_query(request.query)

            if not urls:
                raise ValueError(
                    "No URLs found in query for content extraction")

            # Launch browser and extract content
            browser_result = await self.mcp_client.call_tool(
                server_name="real-browser",
                tool_name="launch_real_browser",
                arguments={"headless": True}
            )

            for url in urls[:request.max_sources]:
                try:
                    # Navigate to URL
                    await self.mcp_client.call_tool(
                        server_name="real-browser",
                        tool_name="real_navigate",
                        arguments={
                            "page_id": "main",
                            "url": url
                        }
                    )

                    # Extract text content
                    content_result = await self.mcp_client.call_tool(
                        server_name="real-browser",
                        tool_name="real_extract_text",
                        arguments={
                            "page_id": "main",
                            "selector": "body"
                        }
                    )

                    # Take screenshot if requested
                    screenshot_path = None
                    if request.include_screenshots:
                        screenshot_result = await self.mcp_client.call_tool(
                            server_name="real-browser",
                            tool_name="real_screenshot",
                            arguments={
                                "page_id": "main",
                                "path": f"screenshot_{len(result.sources)}.png"
                            }
                        )
                        if isinstance(screenshot_result, dict) and "path" in screenshot_result:
                            screenshot_path = screenshot_result["path"]

                    # Create source entry
                    source = {
                        "url": url,
                        "title": url.split("/")[-1] or url,
                        "content": content_result if isinstance(content_result, str) else "",
                        "source_type": "content_extraction",
                        "screenshot": screenshot_path,
                        "extracted_at": datetime.utcnow().isoformat()
                    }
                    result.sources.append(source)

                except Exception as e:
                    logger.warning(
                        f"Failed to extract content from {url}: {e}")

            # Close browser
            await self.mcp_client.call_tool(
                server_name="real-browser",
                tool_name="close_browser",
                arguments={}
            )

            result.total_sources = len(result.sources)

        except Exception as e:
            raise MCPError(
                message=f"Content extraction failed: {str(e)}",
                server_name="real-browser"
            )

    async def _apply_privacy_filters(self, result: ResearchResult):
        """Apply privacy filters to research results."""
        try:
            sensitive_patterns = []

            for source in result.sources:
                content = source.get("content", "") + " " + \
                    source.get("snippet", "")

                if content:
                    # Use API key sniffer to detect sensitive information
                    detection_result = await self.mcp_client.call_tool(
                        server_name="api-key-sniffer",
                        tool_name="analyze_text",
                        arguments={"text": content}
                    )

                    if isinstance(detection_result, dict) and detection_result.get("keys_found"):
                        result.sensitive_data_detected = True
                        sensitive_patterns.extend(
                            detection_result.get("patterns", []))

                        # Redact sensitive content
                        redacted_content = content
                        for pattern in detection_result.get("patterns", []):
                            redacted_content = redacted_content.replace(
                                pattern, "[REDACTED]")

                        source["content"] = redacted_content
                        source["privacy_filtered"] = True

            if result.sensitive_data_detected:
                result.redacted_content = list(set(sensitive_patterns))
                logger.info(
                    f"Privacy filtering applied to research {result.request_id}")

        except Exception as e:
            logger.warning(f"Privacy filtering failed: {e}")

    async def _extract_structured_data(self, result: ResearchResult):
        """Extract structured data from research results."""
        try:
            # Combine all content for analysis
            combined_content = ""
            for source in result.sources:
                combined_content += source.get("content", "") + \
                    " " + source.get("snippet", "") + "\n"

            if not combined_content.strip():
                return

            # Use AI to extract structured data
            extraction_result = await self.mcp_client.call_tool(
                server_name="openrouter-llm",
                tool_name="openrouter_generate",
                arguments={
                    "prompt": f"Extract structured data (key facts, statistics, dates, entities) from this research content about '{result.query}': {combined_content[:2000]}",
                    "model": "qwen/qwen3-235b-a22b-07-25:free",
                    "max_tokens": 800
                }
            )

            if isinstance(extraction_result, dict) and "content" in extraction_result:
                # Try to parse as JSON, fallback to text
                try:
                    structured_data = json.loads(extraction_result["content"])
                except json.JSONDecodeError:
                    structured_data = {
                        "extracted_text": extraction_result["content"]}

                result.structured_data = structured_data

        except Exception as e:
            logger.warning(f"Structured data extraction failed: {e}")

    def _extract_urls_from_query(self, query: str) -> List[str]:
        """Extract URLs from query string."""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, query)
        return urls

    async def get_research_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a research operation."""
        result = self.active_research.get(request_id)
        if not result:
            return None

        return {
            "request_id": result.request_id,
            "query": result.query,
            "research_type": result.research_type.value,
            "status": result.status,
            "total_sources": result.total_sources,
            "processing_time_seconds": result.processing_time_seconds,
            "created_at": result.created_at,
            "completed_at": result.completed_at,
            "sensitive_data_detected": result.sensitive_data_detected
        }

    async def cancel_research(self, request_id: str) -> bool:
        """Cancel a running research operation."""
        if request_id in self.active_research:
            result = self.active_research[request_id]
            result.status = "cancelled"
            result.completed_at = datetime.utcnow()
            return True
        return False

    def cleanup_research(self, request_id: str):
        """Remove completed research from active list."""
        if request_id in self.active_research:
            del self.active_research[request_id]


# Factory function
def create_research_service() -> ResearchService:
    """Create a research service instance."""
    from ..core.interfaces import MCPServerConfig
    
    # Create a dummy config for research service
    dummy_config = MCPServerConfig(
        name="research-service",
        command="echo",
        args=["dummy"],
        env={}
    )
    
    mcp_client = MCPClient(dummy_config)
    return ResearchService(mcp_client)
