"""
Review Report Generator

This module generates comprehensive review reports in various formats
including JSON, HTML, and Markdown from ReviewResult data.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import base64

from ..core.interfaces import ReviewResult, ReviewFinding

logger = logging.getLogger(__name__)


class ReviewReportGenerator:
    """
    Generates comprehensive review reports in multiple formats
    """

    def __init__(self):
        self.report_templates = {
            "html": self._generate_html_template(),
            "markdown": self._generate_markdown_template()
        }

    def generate_json_report(self, review_result: ReviewResult) -> Dict[str, Any]:
        """Generate structured JSON report"""
        try:
            logger.info(
                f"Generating JSON report for {review_result.repository_path}")

            # Convert ReviewResult to dict with proper serialization
            report = {
                "metadata": {
                    "repository_path": review_result.repository_path,
                    "timestamp": review_result.timestamp.isoformat(),
                    "execution_time_ms": review_result.execution_time_ms,
                    "report_version": "1.0"
                },
                "summary": {
                    "files_analyzed": review_result.files_analyzed,
                    "issues_found": review_result.issues_found,
                    "security_score": review_result.security_score,
                    "quality_score": review_result.quality_score,
                    "overall_score": review_result.overall_score
                },
                "scores": {
                    "security": {
                        "score": review_result.security_score,
                        "grade": self._score_to_grade(review_result.security_score),
                        "description": self._get_score_description(review_result.security_score, "security")
                    },
                    "quality": {
                        "score": review_result.quality_score,
                        "grade": self._score_to_grade(review_result.quality_score),
                        "description": self._get_score_description(review_result.quality_score, "quality")
                    },
                    "overall": {
                        "score": review_result.overall_score,
                        "grade": self._score_to_grade(review_result.overall_score),
                        "description": self._get_score_description(review_result.overall_score, "overall")
                    }
                },
                "findings": self._serialize_findings(review_result.findings),
                "recommendations": review_result.recommendations,
                "statistics": self._generate_statistics(review_result.findings),
                "generated_at": datetime.now().isoformat()
            }

            logger.info("JSON report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise

    def generate_html_report(self, review_result: ReviewResult) -> str:
        """Generate HTML report"""
        try:
            logger.info(
                f"Generating HTML report for {review_result.repository_path}")

            # Get JSON data
            json_data = self.generate_json_report(review_result)

            # Generate HTML content
            html_content = self._build_html_report(json_data)

            logger.info("HTML report generated successfully")
            return html_content

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise

    def generate_markdown_report(self, review_result: ReviewResult) -> str:
        """Generate Markdown report"""
        try:
            logger.info(
                f"Generating Markdown report for {review_result.repository_path}")

            # Get JSON data
            json_data = self.generate_json_report(review_result)

            # Generate Markdown content
            markdown_content = self._build_markdown_report(json_data)

            logger.info("Markdown report generated successfully")
            return markdown_content

        except Exception as e:
            logger.error(f"Failed to generate Markdown report: {e}")
            raise

    def generate_summary_report(self, review_result: ReviewResult) -> Dict[str, Any]:
        """Generate a concise summary report"""
        try:
            logger.info(
                f"Generating summary report for {review_result.repository_path}")

            # Count findings by severity and category
            findings_by_severity = self._group_findings_by_severity(
                review_result.findings)
            findings_by_category = self._group_findings_by_category(
                review_result.findings)

            summary = {
                "repository": review_result.repository_path,
                "timestamp": review_result.timestamp.isoformat(),
                "overall_grade": self._score_to_grade(review_result.overall_score),
                "scores": {
                    "security": review_result.security_score,
                    "quality": review_result.quality_score,
                    "overall": review_result.overall_score
                },
                "files_analyzed": review_result.files_analyzed,
                "total_issues": review_result.issues_found,
                "issues_by_severity": findings_by_severity,
                "issues_by_category": findings_by_category,
                "top_recommendations": review_result.recommendations[:3],
                "execution_time_ms": review_result.execution_time_ms
            }

            logger.info("Summary report generated successfully")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            raise

    def _serialize_findings(self, findings: List[ReviewFinding]) -> List[Dict[str, Any]]:
        """Serialize findings to dictionary format"""
        serialized = []

        for finding in findings:
            serialized.append({
                "file_path": finding.file_path,
                "line_number": finding.line_number,
                "severity": finding.severity,
                "category": finding.category,
                "message": finding.message,
                "suggestion": finding.suggestion,
                "confidence": finding.confidence,
                "rule_id": getattr(finding, 'rule_id', None)
            })

        return serialized

    def _generate_statistics(self, findings: List[ReviewFinding]) -> Dict[str, Any]:
        """Generate statistics from findings"""
        if not findings:
            return {
                "total_findings": 0,
                "by_severity": {},
                "by_category": {},
                "by_file": {},
                "confidence_distribution": {}
            }

        # Group by severity
        by_severity = self._group_findings_by_severity(findings)

        # Group by category
        by_category = self._group_findings_by_category(findings)

        # Group by file
        by_file = {}
        for finding in findings:
            file_path = finding.file_path
            if file_path not in by_file:
                by_file[file_path] = 0
            by_file[file_path] += 1

        # Confidence distribution
        confidence_ranges = {
            "high (0.8-1.0)": 0,
            "medium (0.5-0.8)": 0,
            "low (0.0-0.5)": 0
        }

        for finding in findings:
            confidence = finding.confidence
            if confidence >= 0.8:
                confidence_ranges["high (0.8-1.0)"] += 1
            elif confidence >= 0.5:
                confidence_ranges["medium (0.5-0.8)"] += 1
            else:
                confidence_ranges["low (0.0-0.5)"] += 1

        return {
            "total_findings": len(findings),
            "by_severity": by_severity,
            "by_category": by_category,
            # Top 10 files
            "by_file": dict(sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]),
            "confidence_distribution": confidence_ranges
        }

    def _group_findings_by_severity(self, findings: List[ReviewFinding]) -> Dict[str, int]:
        """Group findings by severity"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for finding in findings:
            severity = finding.severity.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts["medium"] += 1  # Default to medium

        return severity_counts

    def _group_findings_by_category(self, findings: List[ReviewFinding]) -> Dict[str, int]:
        """Group findings by category"""
        category_counts = {}

        for finding in findings:
            category = finding.category
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1

        return category_counts

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 9.0:
            return "A+"
        elif score >= 8.5:
            return "A"
        elif score >= 8.0:
            return "A-"
        elif score >= 7.5:
            return "B+"
        elif score >= 7.0:
            return "B"
        elif score >= 6.5:
            return "B-"
        elif score >= 6.0:
            return "C+"
        elif score >= 5.5:
            return "C"
        elif score >= 5.0:
            return "C-"
        elif score >= 4.0:
            return "D"
        else:
            return "F"

    def _get_score_description(self, score: float, category: str) -> str:
        """Get description for score"""
        descriptions = {
            "security": {
                9.0: "Excellent security practices",
                8.0: "Good security with minor issues",
                7.0: "Adequate security with some concerns",
                6.0: "Security needs improvement",
                5.0: "Poor security practices",
                0.0: "Critical security vulnerabilities"
            },
            "quality": {
                9.0: "Excellent code quality",
                8.0: "Good code quality with minor issues",
                7.0: "Adequate code quality",
                6.0: "Code quality needs improvement",
                5.0: "Poor code quality",
                0.0: "Very poor code quality"
            },
            "overall": {
                9.0: "Excellent overall code health",
                8.0: "Good overall code health",
                7.0: "Adequate overall code health",
                6.0: "Overall code health needs improvement",
                5.0: "Poor overall code health",
                0.0: "Critical issues in code health"
            }
        }

        category_descriptions = descriptions.get(
            category, descriptions["overall"])

        for threshold in sorted(category_descriptions.keys(), reverse=True):
            if score >= threshold:
                return category_descriptions[threshold]

        return category_descriptions[0.0]

    def _build_html_report(self, json_data: Dict[str, Any]) -> str:
        """Build HTML report from JSON data"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Review Report - {repository}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .score-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .score-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .score-value {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .score-grade {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .security {{ color: #e74c3c; }}
        .quality {{ color: #3498db; }}
        .overall {{ color: #27ae60; }}
        .section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section-header {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
            border-radius: 10px 10px 0 0;
        }}
        .section-content {{
            padding: 20px;
        }}
        .finding {{
            border-left: 4px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 0 5px 5px 0;
        }}
        .finding.critical {{ border-left-color: #dc3545; }}
        .finding.high {{ border-left-color: #fd7e14; }}
        .finding.medium {{ border-left-color: #ffc107; }}
        .finding.low {{ border-left-color: #28a745; }}
        .finding-header {{
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .severity-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .severity-critical {{ background: #dc3545; color: white; }}
        .severity-high {{ background: #fd7e14; color: white; }}
        .severity-medium {{ background: #ffc107; color: black; }}
        .severity-low {{ background: #28a745; color: white; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat-item {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #495057;
        }}
        .recommendations {{
            list-style: none;
            padding: 0;
        }}
        .recommendations li {{
            padding: 10px;
            margin-bottom: 10px;
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            border-radius: 0 5px 5px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Code Review Report</h1>
        <p>{repository}</p>
        <p>Generated on {timestamp}</p>
    </div>

    <div class="score-cards">
        <div class="score-card">
            <h3>Security Score</h3>
            <div class="score-value security">{security_score}</div>
            <div class="score-grade security">{security_grade}</div>
            <p>{security_description}</p>
        </div>
        <div class="score-card">
            <h3>Quality Score</h3>
            <div class="score-value quality">{quality_score}</div>
            <div class="score-grade quality">{quality_grade}</div>
            <p>{quality_description}</p>
        </div>
        <div class="score-card">
            <h3>Overall Score</h3>
            <div class="score-value overall">{overall_score}</div>
            <div class="score-grade overall">{overall_grade}</div>
            <p>{overall_description}</p>
        </div>
    </div>

    <div class="section">
        <div class="section-header">
            <h2>Summary Statistics</h2>
        </div>
        <div class="section-content">
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{files_analyzed}</div>
                    <div>Files Analyzed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{issues_found}</div>
                    <div>Issues Found</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{execution_time}</div>
                    <div>Execution Time (ms)</div>
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-header">
            <h2>Recommendations</h2>
        </div>
        <div class="section-content">
            <ul class="recommendations">
                {recommendations_html}
            </ul>
        </div>
    </div>

    <div class="section">
        <div class="section-header">
            <h2>Detailed Findings</h2>
        </div>
        <div class="section-content">
            {findings_html}
        </div>
    </div>
</body>
</html>
        """

        # Format findings HTML
        findings_html = ""
        for finding in json_data["findings"]:
            findings_html += f"""
            <div class="finding {finding['severity']}">
                <div class="finding-header">
                    <strong>{finding['file_path']}:{finding['line_number']}</strong>
                    <span class="severity-badge severity-{finding['severity']}">{finding['severity']}</span>
                </div>
                <p><strong>Issue:</strong> {finding['message']}</p>
                {f"<p><strong>Suggestion:</strong> {finding['suggestion']}</p>" if finding['suggestion'] else ""}
                <p><strong>Category:</strong> {finding['category']} | <strong>Confidence:</strong> {finding['confidence']:.1%}</p>
            </div>
            """

        # Format recommendations HTML
        recommendations_html = ""
        for rec in json_data["recommendations"]:
            recommendations_html += f"<li>{rec}</li>"

        # Fill template
        return html_template.format(
            repository=json_data["metadata"]["repository_path"],
            timestamp=json_data["metadata"]["timestamp"],
            security_score=json_data["scores"]["security"]["score"],
            security_grade=json_data["scores"]["security"]["grade"],
            security_description=json_data["scores"]["security"]["description"],
            quality_score=json_data["scores"]["quality"]["score"],
            quality_grade=json_data["scores"]["quality"]["grade"],
            quality_description=json_data["scores"]["quality"]["description"],
            overall_score=json_data["scores"]["overall"]["score"],
            overall_grade=json_data["scores"]["overall"]["grade"],
            overall_description=json_data["scores"]["overall"]["description"],
            files_analyzed=json_data["summary"]["files_analyzed"],
            issues_found=json_data["summary"]["issues_found"],
            execution_time=json_data["metadata"]["execution_time_ms"],
            recommendations_html=recommendations_html,
            findings_html=findings_html
        )

    def _build_markdown_report(self, json_data: Dict[str, Any]) -> str:
        """Build Markdown report from JSON data"""
        markdown_content = f"""# Code Review Report

**Repository:** {json_data["metadata"]["repository_path"]}  
**Generated:** {json_data["metadata"]["timestamp"]}  
**Execution Time:** {json_data["metadata"]["execution_time_ms"]:.2f}ms

## 📊 Scores

| Category | Score | Grade | Description |
|----------|-------|-------|-------------|
| 🔒 Security | {json_data["scores"]["security"]["score"]}/10 | {json_data["scores"]["security"]["grade"]} | {json_data["scores"]["security"]["description"]} |
| 🔧 Quality | {json_data["scores"]["quality"]["score"]}/10 | {json_data["scores"]["quality"]["grade"]} | {json_data["scores"]["quality"]["description"]} |
| 📈 Overall | {json_data["scores"]["overall"]["score"]}/10 | {json_data["scores"]["overall"]["grade"]} | {json_data["scores"]["overall"]["description"]} |

## 📈 Summary

- **Files Analyzed:** {json_data["summary"]["files_analyzed"]}
- **Issues Found:** {json_data["summary"]["issues_found"]}

### Issues by Severity
"""

        # Add severity breakdown
        for severity, count in json_data["statistics"]["by_severity"].items():
            if count > 0:
                emoji = {"critical": "🚨", "high": "⚠️",
                         "medium": "⚡", "low": "ℹ️"}.get(severity, "•")
                markdown_content += f"- {emoji} **{severity.title()}:** {count}\n"

        markdown_content += "\n### Issues by Category\n"

        # Add category breakdown
        for category, count in json_data["statistics"]["by_category"].items():
            markdown_content += f"- **{category.title()}:** {count}\n"

        # Add recommendations
        markdown_content += "\n## 💡 Recommendations\n\n"
        for i, rec in enumerate(json_data["recommendations"], 1):
            markdown_content += f"{i}. {rec}\n"

        # Add detailed findings
        markdown_content += "\n## 🔍 Detailed Findings\n\n"

        if not json_data["findings"]:
            markdown_content += "No issues found! 🎉\n"
        else:
            for finding in json_data["findings"]:
                severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}.get(
                    finding["severity"], "•")

                markdown_content += f"""### {severity_emoji} {finding['file_path']}:{finding['line_number']}

**Severity:** {finding['severity'].title()}  
**Category:** {finding['category']}  
**Confidence:** {finding['confidence']:.1%}

**Issue:** {finding['message']}

"""
                if finding['suggestion']:
                    markdown_content += f"**Suggestion:** {finding['suggestion']}\n\n"

                markdown_content += "---\n\n"

        return markdown_content

    def _generate_html_template(self) -> str:
        """Generate HTML template"""
        # This would contain a more sophisticated HTML template
        return "html_template"

    def _generate_markdown_template(self) -> str:
        """Generate Markdown template"""
        # This would contain a more sophisticated Markdown template
        return "markdown_template"

    def save_report(self, content: str, file_path: str, format_type: str = "html") -> bool:
        """Save report to file"""
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Report saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False


# Global instance
review_report_generator = ReviewReportGenerator()


def get_review_report_generator() -> ReviewReportGenerator:
    """Get the global review report generator instance"""
    return review_report_generator
