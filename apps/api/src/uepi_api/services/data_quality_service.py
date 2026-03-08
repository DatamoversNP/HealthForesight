"""
Enterprise-Grade Data Quality Service
Provides comprehensive data quality validation with business-friendly trust indicators
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import pandas as pd
import numpy as np
from pathlib import Path
import json

from uepi_api.models.data_quality import DataQualityReport, DataQualityIssue
from uepi_api.database import SessionLocal


class EnterpriseDataQualityService:
    """Enterprise-grade data quality service with business trust indicators"""
    
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
    
    def calculate_trust_score(
        self,
        completeness_score: float,
        validity_score: float,
        uniqueness_score: float,
        integrity_score: float,
        consistency_score: float,
        critical_issues: int,
        high_issues: int,
        total_rows: int,
    ) -> Dict[str, Any]:
        """
        Calculate business-friendly trust score and recommendation
        
        Returns:
            Dict with trust_score, trust_level, and trust_recommendation
        """
        # Weighted component scores
        component_weights = {
            'completeness': 0.25,
            'validity': 0.30,
            'uniqueness': 0.15,
            'integrity': 0.20,
            'consistency': 0.10,
        }
        
        weighted_score = (
            completeness_score * component_weights['completeness'] +
            validity_score * component_weights['validity'] +
            uniqueness_score * component_weights['uniqueness'] +
            integrity_score * component_weights['integrity'] +
            consistency_score * component_weights['consistency']
        )
        
        # Penalize for critical and high issues
        issue_penalty = 0.0
        if total_rows > 0:
            critical_penalty = (critical_issues / total_rows) * 100 * 0.5  # Each critical issue reduces by 0.5%
            high_penalty = (high_issues / total_rows) * 100 * 0.2  # Each high issue reduces by 0.2%
            issue_penalty = min(critical_penalty + high_penalty, 30.0)  # Cap penalty at 30%
        
        trust_score = max(0.0, min(100.0, weighted_score - issue_penalty))
        
        # Determine trust level
        if trust_score >= 90:
            trust_level = "EXCELLENT"
            trust_recommendation = "Data quality is excellent. You can confidently use this data for policy analysis, impact predictions, and business decisions. All critical quality checks passed."
        elif trust_score >= 80:
            trust_level = "GOOD"
            trust_recommendation = "Data quality is good. Minor issues exist but should not significantly impact analysis. Review identified issues and proceed with confidence for most use cases."
        elif trust_score >= 70:
            trust_level = "FAIR"
            trust_recommendation = "Data quality is fair. Some quality issues may affect analysis accuracy. Review and address identified issues before making critical business decisions. Use with caution for high-stakes analysis."
        elif trust_score >= 60:
            trust_level = "POOR"
            trust_recommendation = "Data quality is poor. Significant quality issues detected. Do not use this data for policy analysis or business decisions without addressing critical issues first. Data may produce unreliable results."
        else:
            trust_level = "UNTRUSTWORTHY"
            trust_recommendation = "Data quality is untrustworthy. Critical quality issues prevent reliable analysis. Do not use this data until quality issues are resolved. Contact data management team immediately."
        
        return {
            "trust_score": round(trust_score, 2),
            "trust_level": trust_level,
            "trust_recommendation": trust_recommendation,
        }
    
    def generate_executive_summary(
        self,
        overall_score: float,
        trust_level: str,
        datasets_summary: Dict[str, Any],
        issues_summary: List[Dict[str, Any]],
        total_rows: int,
    ) -> str:
        """Generate business-friendly executive summary"""
        summary_parts = []
        
        summary_parts.append(f"Data Quality Assessment Summary")
        summary_parts.append(f"Overall Quality Score: {overall_score:.1f}%")
        summary_parts.append(f"Trust Level: {trust_level}")
        summary_parts.append("")
        
        # Dataset summary
        if datasets_summary:
            summary_parts.append("Dataset Quality Scores:")
            for dataset_name, dataset_info in datasets_summary.items():
                score = dataset_info.get("quality_score", 0)
                summary_parts.append(f"  • {dataset_name}: {score:.1f}%")
            summary_parts.append("")
        
        # Key concerns
        critical_issues = [i for i in issues_summary if i.get("severity") == "CRITICAL" or i.get("severity") == "HIGH"]
        if critical_issues:
            summary_parts.append("Key Concerns:")
            for issue in critical_issues[:5]:  # Top 5
                summary_parts.append(f"  • {issue.get('description', 'Unknown issue')}")
            summary_parts.append("")
        
        # Recommendation
        if trust_level in ["EXCELLENT", "GOOD"]:
            summary_parts.append("Recommendation: Proceed with analysis. Data quality is sufficient for reliable policy impact predictions.")
        elif trust_level == "FAIR":
            summary_parts.append("Recommendation: Review identified issues and consider data remediation before critical analysis.")
        else:
            summary_parts.append("Recommendation: Address data quality issues before proceeding with analysis.")
        
        return "\n".join(summary_parts)
    
    def extract_key_concerns(
        self,
        issues: List[Dict[str, Any]],
        max_concerns: int = 10,
    ) -> List[Dict[str, Any]]:
        """Extract key concerns for business users"""
        # Sort by severity and affected rows
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        
        sorted_issues = sorted(
            issues,
            key=lambda x: (
                severity_order.get(x.get("severity", "LOW"), 0),
                x.get("affected_rows", 0)
            ),
            reverse=True
        )
        
        key_concerns = []
        for issue in sorted_issues[:max_concerns]:
            concern = {
                "severity": issue.get("severity", "UNKNOWN"),
                "type": issue.get("type", "UNKNOWN"),
                "dataset": issue.get("dataset", "UNKNOWN"),
                "description": issue.get("description", ""),
                "business_impact": self._generate_business_impact(issue),
                "affected_rows": issue.get("affected_rows", 0),
                "affected_percentage": issue.get("affected_percentage", 0),
            }
            key_concerns.append(concern)
        
        return key_concerns
    
    def _generate_business_impact(self, issue: Dict[str, Any]) -> str:
        """Generate business-friendly impact description"""
        issue_type = issue.get("type", "")
        severity = issue.get("severity", "")
        affected_pct = issue.get("affected_percentage", 0)
        
        if issue_type == "MISSING_FIELD":
            return f"Missing required field may prevent accurate policy analysis and impact predictions. {affected_pct:.1f}% of records affected."
        elif issue_type == "INCOMPLETE_FIELD":
            return f"Incomplete data in this field may reduce analysis accuracy. {affected_pct:.1f}% of records have missing values."
        elif issue_type == "DUPLICATE_VALUES":
            return f"Duplicate records detected. This may cause double-counting in analysis and incorrect impact predictions."
        elif issue_type == "ORPHANED_REFERENCE":
            return f"Data references point to non-existent records. This may cause analysis errors and incomplete results."
        elif issue_type == "INVALID_DATE":
            return f"Invalid date values detected. This may cause time-series analysis errors and incorrect baseline calculations."
        elif issue_type == "DATA_INCONSISTENCY":
            return f"Data inconsistencies between datasets detected. This may cause analysis discrepancies and unreliable results."
        else:
            return f"Data quality issue detected that may impact analysis accuracy. {affected_pct:.1f}% of records affected."
    
    def store_quality_report(
        self,
        report_data: Dict[str, Any],
        created_by: Optional[UUID] = None,
    ) -> DataQualityReport:
        """Store data quality report in database"""
        db = SessionLocal()
        try:
            # Calculate trust score
            trust_info = self.calculate_trust_score(
                completeness_score=report_data.get("completeness_score", 0),
                validity_score=report_data.get("validity_score", 0),
                uniqueness_score=report_data.get("uniqueness_score", 0),
                integrity_score=report_data.get("integrity_score", 0),
                consistency_score=report_data.get("consistency_score", 85.0),  # Default if not calculated
                critical_issues=report_data.get("critical_issues", 0),
                high_issues=report_data.get("high_issues", 0),
                total_rows=report_data.get("total_rows", 0),
            )
            
            # Generate executive summary
            executive_summary = self.generate_executive_summary(
                overall_score=report_data.get("overall_score", 0),
                trust_level=trust_info["trust_level"],
                datasets_summary=report_data.get("datasets", {}),
                issues_summary=report_data.get("issues", []),
                total_rows=report_data.get("total_rows", 0),
            )
            
            # Extract key concerns
            key_concerns = self.extract_key_concerns(report_data.get("issues", []))
            
            # Count issues by severity
            issues = report_data.get("issues", [])
            critical_count = sum(1 for i in issues if i.get("severity") == "CRITICAL")
            high_count = sum(1 for i in issues if i.get("severity") == "HIGH")
            medium_count = sum(1 for i in issues if i.get("severity") == "MEDIUM")
            low_count = sum(1 for i in issues if i.get("severity") == "LOW")
            
            # Convert numpy types to Python native types for JSON serialization
            def convert_numpy_types(obj):
                if isinstance(obj, (np.integer, np.floating)):
                    return float(obj) if isinstance(obj, np.floating) else int(obj)
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                return obj
            
            # Convert report_data to ensure no numpy types
            report_data_clean = convert_numpy_types(report_data)
            
            # Create report record
            quality_report = DataQualityReport(
                tenant_id=self.tenant_id,
                overall_quality_score=float(report_data_clean.get("overall_score", 0)),
                trust_score=float(trust_info["trust_score"]),
                trust_level=trust_info["trust_level"],
                trust_recommendation=trust_info["trust_recommendation"],
                completeness_score=float(report_data_clean.get("completeness_score", 0)),
                validity_score=float(report_data_clean.get("validity_score", 0)),
                uniqueness_score=float(report_data_clean.get("uniqueness_score", 0)),
                integrity_score=float(report_data_clean.get("integrity_score", 0)),
                consistency_score=float(report_data_clean.get("consistency_score", 85.0)),
                total_issues=int(len(issues)),
                critical_issues=int(critical_count),
                high_issues=int(high_count),
                medium_issues=int(medium_count),
                low_issues=int(low_count),
                report_json=report_data_clean,
                datasets_summary=report_data_clean.get("datasets", {}),
                issues_summary=issues,
                executive_summary=executive_summary,
                key_concerns=key_concerns,
                data_coverage=report_data_clean.get("data_coverage", {}),
                validation_started_at=datetime.fromisoformat(report_data_clean.get("timestamp", datetime.utcnow().isoformat()).replace("Z", "+00:00")) if isinstance(report_data_clean.get("timestamp"), str) else report_data_clean.get("timestamp", datetime.utcnow()),
                validation_completed_at=datetime.utcnow(),
                created_by=created_by,
            )
            
            db.add(quality_report)
            db.flush()  # Get the ID
            
            # Store individual issues
            for issue_data in issues:
                # Convert numpy types to Python native types
                affected_percentage = issue_data.get("affected_percentage", 0)
                if isinstance(affected_percentage, (np.integer, np.floating)):
                    affected_percentage = float(affected_percentage) if isinstance(affected_percentage, np.floating) else int(affected_percentage)
                
                issue = DataQualityIssue(
                    report_id=quality_report.id,
                    tenant_id=self.tenant_id,
                    issue_type=issue_data.get("type", "UNKNOWN"),
                    severity=issue_data.get("severity", "LOW"),
                    dataset=issue_data.get("dataset", None),
                    field_name=issue_data.get("field", None),
                    description=issue_data.get("description", ""),
                    business_impact=self._generate_business_impact(issue_data),
                    affected_rows=int(issue_data.get("affected_rows", issue_data.get("missing_count", issue_data.get("duplicate_count", issue_data.get("orphaned_count", 0))))),
                    affected_percentage=affected_percentage,
                    sample_values=issue_data.get("sample_values", []),
                )
                db.add(issue)
            
            db.commit()
            db.refresh(quality_report)
            
            return quality_report
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    
    def get_latest_report(self) -> Optional[DataQualityReport]:
        """Get the latest data quality report for tenant"""
        db = SessionLocal()
        try:
            report = db.query(DataQualityReport).filter(
                DataQualityReport.tenant_id == self.tenant_id
            ).order_by(DataQualityReport.created_at.desc()).first()
            return report
        finally:
            db.close()

