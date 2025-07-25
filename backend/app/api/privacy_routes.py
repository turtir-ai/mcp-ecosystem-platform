"""
Privacy and security API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.privacy_security_service import (
    PrivacySecurityService, SensitivityLevel, DataType,
    create_privacy_security_service
)
from ..core.auth import get_current_user

router = APIRouter(prefix="/privacy", tags=["privacy"])


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


@router.post("/analyze", response_model=dict)
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


@router.post("/score", response_model=dict)
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


@router.get("/data-types", response_model=List[dict])
async def get_data_types():
    """Get supported sensitive data types."""
    return [
        {
            "type": DataType.API_KEY.value,
            "name": "API Keys",
            "description": "API keys, access tokens, and authentication credentials",
            "severity": SensitivityLevel.RESTRICTED.value,
            "examples": ["sk_test_...", "Bearer token", "AKIA..."]
        },
        {
            "type": DataType.PASSWORD.value,
            "name": "Passwords",
            "description": "Passwords and authentication secrets",
            "severity": SensitivityLevel.RESTRICTED.value,
            "examples": ["password=secret123", "pwd: mypassword"]
        },
        {
            "type": DataType.EMAIL.value,
            "name": "Email Addresses",
            "description": "Email addresses and contact information",
            "severity": SensitivityLevel.CONFIDENTIAL.value,
            "examples": ["user@example.com", "contact@company.org"]
        },
        {
            "type": DataType.PHONE.value,
            "name": "Phone Numbers",
            "description": "Phone numbers and contact details",
            "severity": SensitivityLevel.CONFIDENTIAL.value,
            "examples": ["(555) 123-4567", "+1-800-555-0123"]
        },
        {
            "type": DataType.SSN.value,
            "name": "Social Security Numbers",
            "description": "Social Security Numbers and national IDs",
            "severity": SensitivityLevel.RESTRICTED.value,
            "examples": ["123-45-6789", "987654321"]
        },
        {
            "type": DataType.CREDIT_CARD.value,
            "name": "Credit Card Numbers",
            "description": "Credit card and payment information",
            "severity": SensitivityLevel.RESTRICTED.value,
            "examples": ["4111-1111-1111-1111", "5555555555554444"]
        },
        {
            "type": DataType.IP_ADDRESS.value,
            "name": "IP Addresses",
            "description": "IP addresses and network identifiers",
            "severity": SensitivityLevel.INTERNAL.value,
            "examples": ["192.168.1.1", "2001:db8::1"]
        },
        {
            "type": DataType.PERSONAL_NAME.value,
            "name": "Personal Names",
            "description": "Personal names and identities",
            "severity": SensitivityLevel.CONFIDENTIAL.value,
            "examples": ["John Smith", "Jane Doe"]
        }
    ]


@router.get("/sensitivity-levels", response_model=List[dict])
async def get_sensitivity_levels():
    """Get available sensitivity levels."""
    return [
        {
            "level": SensitivityLevel.PUBLIC.value,
            "name": "Public",
            "description": "Information that can be freely shared",
            "color": "green",
            "risk_score": 0
        },
        {
            "level": SensitivityLevel.INTERNAL.value,
            "name": "Internal",
            "description": "Information for internal use only",
            "color": "yellow",
            "risk_score": 25
        },
        {
            "level": SensitivityLevel.CONFIDENTIAL.value,
            "name": "Confidential",
            "description": "Sensitive information requiring protection",
            "color": "orange",
            "risk_score": 50
        },
        {
            "level": SensitivityLevel.RESTRICTED.value,
            "name": "Restricted",
            "description": "Highly sensitive information with strict access controls",
            "color": "red",
            "risk_score": 100
        }
    ]


@router.post("/redact", response_model=dict)
async def redact_content(
    content: str,
    data_types: Optional[List[DataType]] = None,
    current_user: dict = Depends(get_current_user),
    privacy_service: PrivacySecurityService = Depends(get_privacy_service)
):
    """Redact sensitive information from content."""
    try:
        # Perform full analysis
        report = await privacy_service.analyze_privacy(content)

        # Filter matches by requested data types if specified
        if data_types:
            filtered_matches = [
                m for m in report.matches if m.data_type in data_types]
            # Re-redact with filtered matches
            redacted_content = privacy_service._redact_content(
                content, filtered_matches)
        else:
            redacted_content = report.redacted_content
            filtered_matches = report.matches

        return {
            "original_length": len(content),
            "redacted_content": redacted_content,
            "redacted_length": len(redacted_content),
            "items_redacted": len(filtered_matches),
            "redaction_summary": {
                match.data_type.value: len(
                    [m for m in filtered_matches if m.data_type == match.data_type])
                for match in filtered_matches
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content redaction failed: {str(e)}"
        )


@router.post("/batch-analyze", response_model=List[dict])
async def batch_analyze_privacy(
    contents: List[str],
    current_user: dict = Depends(get_current_user),
    privacy_service: PrivacySecurityService = Depends(get_privacy_service)
):
    """Perform batch privacy analysis on multiple content pieces."""
    if len(contents) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 content pieces allowed in batch"
        )

    try:
        results = []

        for i, content in enumerate(contents):
            try:
                score_info = await privacy_service.get_privacy_score(content)
                results.append({
                    "index": i,
                    "status": "completed",
                    "privacy_score": score_info["privacy_score"],
                    "risk_level": score_info["risk_level"],
                    "total_issues": score_info["total_issues"],
                    "safe_to_share": score_info["safe_to_share"]
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "status": "failed",
                    "error": str(e)
                })

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch privacy analysis failed: {str(e)}"
        )
