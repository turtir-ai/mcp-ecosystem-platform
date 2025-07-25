"""
Privacy and security service for data protection and sensitive information handling.
"""
import re
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from .mcp_client import MCPClient
from ..core.error_handling import get_error_handler

logger = logging.getLogger(__name__)


class SensitivityLevel(str, Enum):
    """Data sensitivity levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DataType(str, Enum):
    """Types of sensitive data."""
    API_KEY = "api_key"
    PASSWORD = "password"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    PERSONAL_NAME = "personal_name"
    ADDRESS = "address"
    FINANCIAL = "financial"
    MEDICAL = "medical"
    BIOMETRIC = "biometric"


@dataclass
class SensitiveDataMatch:
    """Represents a match of sensitive data."""
    data_type: DataType
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str
    severity: SensitivityLevel


@dataclass
class PrivacyReport:
    """Privacy analysis report."""
    content_id: str
    total_matches: int
    sensitivity_level: SensitivityLevel
    matches: List[SensitiveDataMatch]
    redacted_content: str
    recommendations: List[str]
    processing_time_seconds: float
    created_at: datetime


class PrivacySecurityService:
    """Service for data privacy and security measures."""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.error_handler = get_error_handler()

        # Sensitive data patterns
        self.patterns = {
            DataType.API_KEY: [
                r'(?i)(?:api[_-]?key|apikey|access[_-]?token|secret[_-]?key)["\s]*[:=]["\s]*([a-zA-Z0-9_\-]{20,})',
                r'(?i)(?:bearer|token)["\s]*[:=]["\s]*([a-zA-Z0-9_\-\.]{20,})',
                r'(?i)(?:sk|pk)_[a-zA-Z0-9]{20,}',  # Stripe-like keys
                r'(?i)AIza[0-9A-Za-z_\-]{35}',  # Google API keys
                r'(?i)AKIA[0-9A-Z]{16}',  # AWS access keys
            ],
            DataType.PASSWORD: [
                r'(?i)(?:password|passwd|pwd)["\s]*[:=]["\s]*([^\s"\']{6,})',
                r'(?i)(?:pass|secret)["\s]*[:=]["\s]*([^\s"\']{6,})',
            ],
            DataType.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            DataType.PHONE: [
                r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                r'(?:\+?[1-9]\d{1,14})',  # International format
            ],
            DataType.SSN: [
                r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{9}\b',
            ],
            DataType.CREDIT_CARD: [
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            ],
            DataType.IP_ADDRESS: [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6
            ],
            DataType.PERSONAL_NAME: [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Simple name pattern
            ],
        }

        # Severity mapping
        self.severity_mapping = {
            DataType.API_KEY: SensitivityLevel.RESTRICTED,
            DataType.PASSWORD: SensitivityLevel.RESTRICTED,
            DataType.SSN: SensitivityLevel.RESTRICTED,
            DataType.CREDIT_CARD: SensitivityLevel.RESTRICTED,
            DataType.MEDICAL: SensitivityLevel.RESTRICTED,
            DataType.BIOMETRIC: SensitivityLevel.RESTRICTED,
            DataType.EMAIL: SensitivityLevel.CONFIDENTIAL,
            DataType.PHONE: SensitivityLevel.CONFIDENTIAL,
            DataType.PERSONAL_NAME: SensitivityLevel.CONFIDENTIAL,
            DataType.ADDRESS: SensitivityLevel.CONFIDENTIAL,
            DataType.FINANCIAL: SensitivityLevel.CONFIDENTIAL,
            DataType.IP_ADDRESS: SensitivityLevel.INTERNAL,
        }

    async def analyze_privacy(self, content: str, content_id: Optional[str] = None) -> PrivacyReport:
        """Analyze content for privacy and security issues."""
        if not content_id:
            content_id = f"privacy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting privacy analysis for {content_id}")

            # Detect sensitive data using multiple methods
            matches = []

            # 1. Pattern-based detection
            pattern_matches = await self._detect_with_patterns(content)
            matches.extend(pattern_matches)

            # 2. MCP-based detection (API key sniffer)
            mcp_matches = await self._detect_with_mcp(content)
            matches.extend(mcp_matches)

            # 3. AI-based detection for complex patterns
            ai_matches = await self._detect_with_ai(content)
            matches.extend(ai_matches)

            # Remove duplicates and merge overlapping matches
            matches = self._deduplicate_matches(matches)

            # Determine overall sensitivity level
            sensitivity_level = self._determine_sensitivity_level(matches)

            # Generate redacted content
            redacted_content = self._redact_content(content, matches)

            # Generate recommendations
            recommendations = self._generate_recommendations(matches)

            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            report = PrivacyReport(
                content_id=content_id,
                total_matches=len(matches),
                sensitivity_level=sensitivity_level,
                matches=matches,
                redacted_content=redacted_content,
                recommendations=recommendations,
                processing_time_seconds=processing_time,
                created_at=start_time
            )

            logger.info(
                f"Privacy analysis completed for {content_id}: {len(matches)} matches found")
            return report

        except Exception as e:
            self.error_handler.handle_workflow_error(
                error=e,
                workflow_id="privacy_analysis",
                execution_id=content_id,
                context={"content_length": len(content)}
            )
            raise

    async def _detect_with_patterns(self, content: str) -> List[SensitiveDataMatch]:
        """Detect sensitive data using regex patterns."""
        matches = []

        for data_type, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    for match in re.finditer(pattern, content):
                        # Extract context around the match
                        start = max(0, match.start() - 20)
                        end = min(len(content), match.end() + 20)
                        context = content[start:end]

                        # Calculate confidence based on pattern specificity
                        confidence = self._calculate_pattern_confidence(
                            data_type, match.group())

                        matches.append(SensitiveDataMatch(
                            data_type=data_type,
                            value=match.group(),
                            confidence=confidence,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            context=context,
                            severity=self.severity_mapping.get(
                                data_type, SensitivityLevel.INTERNAL)
                        ))

                except re.error as e:
                    logger.warning(
                        f"Invalid regex pattern for {data_type}: {e}")

        return matches

    async def _detect_with_mcp(self, content: str) -> List[SensitiveDataMatch]:
        """Detect sensitive data using MCP API key sniffer."""
        matches = []

        try:
            # Use API key sniffer MCP server
            detection_result = await self.mcp_client.call_tool(
                server_name="api-key-sniffer",
                tool_name="analyze_text",
                arguments={"text": content}
            )

            if isinstance(detection_result, dict) and detection_result.get("keys_found"):
                patterns = detection_result.get("patterns", [])

                for pattern in patterns:
                    # Find all occurrences of this pattern in content
                    for match in re.finditer(re.escape(pattern), content):
                        # Extract context
                        start = max(0, match.start() - 20)
                        end = min(len(content), match.end() + 20)
                        context = content[start:end]

                        matches.append(SensitiveDataMatch(
                            data_type=DataType.API_KEY,
                            value=pattern,
                            confidence=0.9,  # High confidence from specialized tool
                            start_pos=match.start(),
                            end_pos=match.end(),
                            context=context,
                            severity=SensitivityLevel.RESTRICTED
                        ))

        except Exception as e:
            logger.warning(f"MCP-based detection failed: {e}")

        return matches

    async def _detect_with_ai(self, content: str) -> List[SensitiveDataMatch]:
        """Detect sensitive data using AI analysis."""
        matches = []

        try:
            # Use AI to detect complex sensitive patterns
            prompt = f"""
            Analyze the following content for sensitive information that might not be caught by simple patterns.
            Look for:
            1. Personal information (names, addresses, dates of birth)
            2. Financial information (account numbers, routing numbers)
            3. Medical information (patient IDs, medical record numbers)
            4. Business confidential information
            5. Authentication credentials in unusual formats
            
            Content (first 1000 chars):
            {content[:1000]}
            
            Return findings in format: TYPE:VALUE:CONFIDENCE (0-1)
            """

            ai_result = await self.mcp_client.call_tool(
                server_name="groq-llm",
                tool_name="groq_generate",
                arguments={
                    "prompt": prompt,
                    "model": "llama-3.1-70b-versatile",
                    "max_tokens": 500,
                    "temperature": 0.1  # Low temperature for consistency
                }
            )

            if isinstance(ai_result, dict) and "content" in ai_result:
                findings = ai_result["content"].split('\n')

                for finding in findings:
                    if ':' in finding and finding.count(':') >= 2:
                        parts = finding.split(':', 2)
                        if len(parts) >= 3:
                            try:
                                data_type_str = parts[0].strip().lower()
                                value = parts[1].strip()
                                confidence = float(parts[2].strip())

                                # Map AI detection to our data types
                                data_type = self._map_ai_detection_type(
                                    data_type_str)

                                if data_type and value in content:
                                    # Find position in content
                                    pos = content.find(value)
                                    if pos >= 0:
                                        start = max(0, pos - 20)
                                        end = min(len(content),
                                                  pos + len(value) + 20)
                                        context = content[start:end]

                                        matches.append(SensitiveDataMatch(
                                            data_type=data_type,
                                            value=value,
                                            confidence=confidence,
                                            start_pos=pos,
                                            end_pos=pos + len(value),
                                            context=context,
                                            severity=self.severity_mapping.get(
                                                data_type, SensitivityLevel.INTERNAL)
                                        ))
                            except (ValueError, IndexError):
                                continue

        except Exception as e:
            logger.warning(f"AI-based detection failed: {e}")

        return matches

    def _calculate_pattern_confidence(self, data_type: DataType, value: str) -> float:
        """Calculate confidence score for pattern matches."""
        base_confidence = 0.7

        # Adjust confidence based on data type and value characteristics
        if data_type == DataType.API_KEY:
            if len(value) > 30:
                base_confidence = 0.9
            elif len(value) > 20:
                base_confidence = 0.8
        elif data_type == DataType.EMAIL:
            if '@' in value and '.' in value.split('@')[1]:
                base_confidence = 0.95
        elif data_type == DataType.CREDIT_CARD:
            # Luhn algorithm check could be added here
            base_confidence = 0.85

        return min(base_confidence, 1.0)

    def _map_ai_detection_type(self, ai_type: str) -> Optional[DataType]:
        """Map AI detection type to our DataType enum."""
        mapping = {
            "personal": DataType.PERSONAL_NAME,
            "name": DataType.PERSONAL_NAME,
            "financial": DataType.FINANCIAL,
            "medical": DataType.MEDICAL,
            "credential": DataType.API_KEY,
            "auth": DataType.API_KEY,
            "address": DataType.ADDRESS,
            "phone": DataType.PHONE,
            "email": DataType.EMAIL,
        }

        for key, data_type in mapping.items():
            if key in ai_type:
                return data_type

        return None

    def _deduplicate_matches(self, matches: List[SensitiveDataMatch]) -> List[SensitiveDataMatch]:
        """Remove duplicate and overlapping matches."""
        if not matches:
            return matches

        # Sort by position
        matches.sort(key=lambda x: x.start_pos)

        deduplicated = []
        for match in matches:
            # Check for overlaps with existing matches
            overlaps = False
            for existing in deduplicated:
                if (match.start_pos < existing.end_pos and
                        match.end_pos > existing.start_pos):
                    # Overlapping matches - keep the one with higher confidence
                    if match.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(match)
                    overlaps = True
                    break

            if not overlaps:
                deduplicated.append(match)

        return deduplicated

    def _determine_sensitivity_level(self, matches: List[SensitiveDataMatch]) -> SensitivityLevel:
        """Determine overall sensitivity level based on matches."""
        if not matches:
            return SensitivityLevel.PUBLIC

        # Find highest sensitivity level
        max_level = SensitivityLevel.PUBLIC
        level_order = [
            SensitivityLevel.PUBLIC,
            SensitivityLevel.INTERNAL,
            SensitivityLevel.CONFIDENTIAL,
            SensitivityLevel.RESTRICTED
        ]

        for match in matches:
            if level_order.index(match.severity) > level_order.index(max_level):
                max_level = match.severity

        return max_level

    def _redact_content(self, content: str, matches: List[SensitiveDataMatch]) -> str:
        """Redact sensitive information from content."""
        if not matches:
            return content

        # Sort matches by position (reverse order to maintain positions)
        matches.sort(key=lambda x: x.start_pos, reverse=True)

        redacted = content
        for match in matches:
            # Create redaction text based on data type
            redaction = self._create_redaction_text(
                match.data_type, match.value)

            # Replace the sensitive data
            redacted = (redacted[:match.start_pos] +
                        redaction +
                        redacted[match.end_pos:])

        return redacted

    def _create_redaction_text(self, data_type: DataType, original_value: str) -> str:
        """Create appropriate redaction text."""
        redaction_templates = {
            DataType.API_KEY: "[API_KEY_REDACTED]",
            DataType.PASSWORD: "[PASSWORD_REDACTED]",
            DataType.EMAIL: "[EMAIL_REDACTED]",
            DataType.PHONE: "[PHONE_REDACTED]",
            DataType.SSN: "[SSN_REDACTED]",
            DataType.CREDIT_CARD: "[CREDIT_CARD_REDACTED]",
            DataType.IP_ADDRESS: "[IP_ADDRESS_REDACTED]",
            DataType.PERSONAL_NAME: "[NAME_REDACTED]",
            DataType.ADDRESS: "[ADDRESS_REDACTED]",
            DataType.FINANCIAL: "[FINANCIAL_INFO_REDACTED]",
            DataType.MEDICAL: "[MEDICAL_INFO_REDACTED]",
            DataType.BIOMETRIC: "[BIOMETRIC_DATA_REDACTED]",
        }

        return redaction_templates.get(data_type, "[SENSITIVE_DATA_REDACTED]")

    def _generate_recommendations(self, matches: List[SensitiveDataMatch]) -> List[str]:
        """Generate privacy and security recommendations."""
        recommendations = []

        if not matches:
            recommendations.append(
                "No sensitive data detected. Content appears safe for sharing.")
            return recommendations

        # Count matches by type
        type_counts = {}
        for match in matches:
            type_counts[match.data_type] = type_counts.get(
                match.data_type, 0) + 1

        # Generate specific recommendations
        if DataType.API_KEY in type_counts:
            recommendations.append(
                f"Found {type_counts[DataType.API_KEY]} API key(s). "
                "Immediately rotate these keys and review access logs."
            )

        if DataType.PASSWORD in type_counts:
            recommendations.append(
                f"Found {type_counts[DataType.PASSWORD]} password(s). "
                "Change these passwords immediately and enable 2FA where possible."
            )

        if DataType.CREDIT_CARD in type_counts:
            recommendations.append(
                f"Found {type_counts[DataType.CREDIT_CARD]} credit card number(s). "
                "Contact card issuer to report potential exposure."
            )

        if DataType.SSN in type_counts:
            recommendations.append(
                f"Found {type_counts[DataType.SSN]} SSN(s). "
                "Consider identity monitoring and fraud alerts."
            )

        if DataType.EMAIL in type_counts or DataType.PHONE in type_counts:
            recommendations.append(
                "Personal contact information detected. "
                "Ensure compliance with privacy regulations (GDPR, CCPA)."
            )

        # General recommendations
        recommendations.append(
            "Review data handling policies and ensure proper encryption for sensitive data."
        )

        if len(matches) > 5:
            recommendations.append(
                "High volume of sensitive data detected. "
                "Consider implementing automated data loss prevention (DLP) tools."
            )

        return recommendations

    async def get_privacy_score(self, content: str) -> Dict[str, Any]:
        """Get a privacy score for content."""
        report = await self.analyze_privacy(content)

        # Calculate privacy score (0-100, higher is better)
        base_score = 100

        # Deduct points based on sensitivity
        for match in report.matches:
            if match.severity == SensitivityLevel.RESTRICTED:
                base_score -= 20
            elif match.severity == SensitivityLevel.CONFIDENTIAL:
                base_score -= 10
            elif match.severity == SensitivityLevel.INTERNAL:
                base_score -= 5

        privacy_score = max(0, base_score)

        return {
            "privacy_score": privacy_score,
            "risk_level": self._get_risk_level(privacy_score),
            "total_issues": report.total_matches,
            "sensitivity_level": report.sensitivity_level.value,
            "safe_to_share": privacy_score >= 80,
            "recommendations_count": len(report.recommendations)
        }

    def _get_risk_level(self, score: int) -> str:
        """Get risk level based on privacy score."""
        if score >= 90:
            return "low"
        elif score >= 70:
            return "medium"
        elif score >= 50:
            return "high"
        else:
            return "critical"


# Factory function
def create_privacy_security_service() -> PrivacySecurityService:
    """Create a privacy security service instance."""
    from ..core.interfaces import MCPServerConfig
    
    # Create a dummy config for privacy security service
    dummy_config = MCPServerConfig(
        name="privacy-security-service",
        command="echo",
        args=["dummy"],
        env={}
    )
    
    mcp_client = MCPClient(dummy_config)
    return PrivacySecurityService(mcp_client)
