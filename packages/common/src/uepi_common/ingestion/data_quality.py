"""
Data Quality & Validation Engine
Provides comprehensive data quality checks, validation, and profiling
"""
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from uuid import UUID
import pandas as pd
import numpy as np
from enum import Enum
from pydantic import BaseModel, Field


class QualityCheckType(str, Enum):
    """Types of data quality checks"""
    SCHEMA_VALIDATION = "SCHEMA_VALIDATION"
    COMPLETENESS = "COMPLETENESS"
    UNIQUENESS = "UNIQUENESS"
    REFERENTIAL_INTEGRITY = "REFERENTIAL_INTEGRITY"
    DATA_TYPE = "DATA_TYPE"
    RANGE_CHECK = "RANGE_CHECK"
    PATTERN_MATCH = "PATTERN_MATCH"
    CUSTOM_RULE = "CUSTOM_RULE"


class QualitySeverity(str, Enum):
    """Severity levels for quality issues"""
    ERROR = "ERROR"  # Blocks ingestion
    WARNING = "WARNING"  # Allows ingestion but flags issue
    INFO = "INFO"  # Informational only


class QualityIssue(BaseModel):
    """A single data quality issue"""
    check_type: QualityCheckType
    severity: QualitySeverity
    field_name: Optional[str] = None
    issue_description: str
    affected_rows: int = 0
    affected_row_indices: List[int] = Field(default_factory=list)
    sample_values: List[Any] = Field(default_factory=list)
    rule_name: Optional[str] = None


class QualityReport(BaseModel):
    """Complete data quality report"""
    dataset_id: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    quality_score: float = Field(ge=0.0, le=1.0, description="Overall quality score (0-1)")
    completeness_score: float = Field(ge=0.0, le=1.0, description="Completeness score (0-1)")
    validity_score: float = Field(ge=0.0, le=1.0, description="Validity score (0-1)")
    uniqueness_score: float = Field(ge=0.0, le=1.0, description="Uniqueness score (0-1)")
    issues: List[QualityIssue] = Field(default_factory=list)
    field_statistics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DataQualityEngine:
    """Comprehensive data quality validation engine"""
    
    def __init__(
        self,
        required_fields: Optional[List[str]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize data quality engine
        
        Args:
            required_fields: List of required field names
            validation_rules: Custom validation rules
        """
        self.required_fields = required_fields or []
        self.validation_rules = validation_rules or {}
    
    def validate(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        target_schema: Optional[Dict[str, Any]] = None,
    ) -> QualityReport:
        """
        Perform comprehensive data quality validation
        
        Args:
            df: DataFrame to validate
            dataset_id: Dataset identifier
            target_schema: Target schema definition
            
        Returns:
            QualityReport with all validation results
        """
        total_rows = len(df)
        issues: List[QualityIssue] = []
        
        # 1. Schema Validation
        schema_issues = self._validate_schema(df, target_schema)
        issues.extend(schema_issues)
        
        # 2. Completeness Checks
        completeness_issues, completeness_score = self._check_completeness(df)
        issues.extend(completeness_issues)
        
        # 3. Data Type Validation
        type_issues = self._validate_data_types(df, target_schema)
        issues.extend(type_issues)
        
        # 4. Uniqueness Checks
        uniqueness_issues, uniqueness_score = self._check_uniqueness(df)
        issues.extend(uniqueness_issues)
        
        # 5. Range and Pattern Checks
        range_issues = self._check_ranges_and_patterns(df)
        issues.extend(range_issues)
        
        # 6. Custom Rules
        custom_issues = self._check_custom_rules(df)
        issues.extend(custom_issues)
        
        # 7. Data Profiling
        field_statistics = self._profile_data(df)
        
        # Calculate scores
        error_count = sum(1 for issue in issues if issue.severity == QualitySeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == QualitySeverity.WARNING)
        
        invalid_rows = len(set(
            idx for issue in issues
            for idx in issue.affected_row_indices
            if issue.severity == QualitySeverity.ERROR
        ))
        valid_rows = total_rows - invalid_rows
        
        # Calculate quality scores
        validity_score = valid_rows / total_rows if total_rows > 0 else 1.0
        
        # Overall quality score (weighted)
        quality_score = (
            completeness_score * 0.3 +
            validity_score * 0.4 +
            uniqueness_score * 0.2 +
            (1.0 - min(error_count / max(total_rows, 1), 1.0)) * 0.1
        )
        
        return QualityReport(
            dataset_id=dataset_id,
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            quality_score=quality_score,
            completeness_score=completeness_score,
            validity_score=validity_score,
            uniqueness_score=uniqueness_score,
            issues=issues,
            field_statistics=field_statistics,
        )
    
    def _validate_schema(
        self,
        df: pd.DataFrame,
        target_schema: Optional[Dict[str, Any]],
    ) -> List[QualityIssue]:
        """Validate schema against target"""
        issues = []
        
        if not target_schema:
            return issues
        
        required_fields = target_schema.get("required_fields", [])
        schema_fields = target_schema.get("fields", {})
        
        # Check for missing required fields
        for field in required_fields:
            if field not in df.columns:
                issues.append(QualityIssue(
                    check_type=QualityCheckType.SCHEMA_VALIDATION,
                    severity=QualitySeverity.ERROR,
                    field_name=field,
                    issue_description=f"Required field '{field}' is missing from dataset",
                    affected_rows=len(df),
                ))
        
        # Check for unexpected fields (warnings only)
        for col in df.columns:
            if col not in schema_fields and col not in required_fields:
                issues.append(QualityIssue(
                    check_type=QualityCheckType.SCHEMA_VALIDATION,
                    severity=QualitySeverity.WARNING,
                    field_name=col,
                    issue_description=f"Unexpected field '{col}' not in target schema",
                    affected_rows=len(df),
                ))
        
        return issues
    
    def _check_completeness(
        self,
        df: pd.DataFrame,
    ) -> tuple[List[QualityIssue], float]:
        """Check data completeness"""
        issues = []
        total_cells = len(df) * len(df.columns)
        missing_cells = 0
        
        for col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                missing_cells += null_count
                null_indices = df[df[col].isna()].index.tolist()
                
                # Check if it's a required field
                severity = QualitySeverity.ERROR if col in self.required_fields else QualitySeverity.WARNING
                
                issues.append(QualityIssue(
                    check_type=QualityCheckType.COMPLETENESS,
                    severity=severity,
                    field_name=col,
                    issue_description=f"Field '{col}' has {null_count} missing values ({null_count/len(df)*100:.1f}%)",
                    affected_rows=null_count,
                    affected_row_indices=null_indices[:100],  # Limit to first 100
                ))
        
        completeness_score = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 1.0
        
        return issues, completeness_score
    
    def _validate_data_types(
        self,
        df: pd.DataFrame,
        target_schema: Optional[Dict[str, Any]],
    ) -> List[QualityIssue]:
        """Validate data types"""
        issues = []
        
        if not target_schema:
            return issues
        
        schema_fields = target_schema.get("fields", {})
        
        for col in df.columns:
            if col not in schema_fields:
                continue
            
            expected_type = schema_fields[col].get("type")
            if not expected_type:
                continue
            
            # Type validation logic
            if expected_type == "date" or expected_type == "datetime":
                # Check if can be parsed as date
                try:
                    pd.to_datetime(df[col], errors='raise')
                except:
                    invalid_indices = df[df[col].notna()].index.tolist()
                    issues.append(QualityIssue(
                        check_type=QualityCheckType.DATA_TYPE,
                        severity=QualitySeverity.ERROR,
                        field_name=col,
                        issue_description=f"Field '{col}' contains invalid date/datetime values",
                        affected_rows=len(invalid_indices),
                        affected_row_indices=invalid_indices[:100],
                    ))
            
            elif expected_type in ["int", "integer"]:
                # Check if numeric and can be converted to int
                non_numeric = df[df[col].notna() & ~pd.to_numeric(df[col], errors='coerce').notna()].index.tolist()
                if non_numeric:
                    issues.append(QualityIssue(
                        check_type=QualityCheckType.DATA_TYPE,
                        severity=QualitySeverity.ERROR,
                        field_name=col,
                        issue_description=f"Field '{col}' contains non-numeric values",
                        affected_rows=len(non_numeric),
                        affected_row_indices=non_numeric[:100],
                    ))
            
            elif expected_type in ["float", "decimal", "number"]:
                # Check if numeric
                non_numeric = df[df[col].notna() & ~pd.to_numeric(df[col], errors='coerce').notna()].index.tolist()
                if non_numeric:
                    issues.append(QualityIssue(
                        check_type=QualityCheckType.DATA_TYPE,
                        severity=QualitySeverity.ERROR,
                        field_name=col,
                        issue_description=f"Field '{col}' contains non-numeric values",
                        affected_rows=len(non_numeric),
                        affected_row_indices=non_numeric[:100],
                    ))
        
        return issues
    
    def _check_uniqueness(
        self,
        df: pd.DataFrame,
    ) -> tuple[List[QualityIssue], float]:
        """Check uniqueness constraints"""
        issues = []
        
        # Check for duplicate rows
        duplicates = df.duplicated()
        duplicate_count = duplicates.sum()
        
        if duplicate_count > 0:
            duplicate_indices = df[duplicates].index.tolist()
            issues.append(QualityIssue(
                check_type=QualityCheckType.UNIQUENESS,
                severity=QualitySeverity.WARNING,
                issue_description=f"Found {duplicate_count} duplicate rows",
                affected_rows=duplicate_count,
                affected_row_indices=duplicate_indices[:100],
            ))
        
        # Check for duplicate values in key fields (if specified)
        key_fields = self.validation_rules.get("unique_fields", [])
        for field in key_fields:
            if field in df.columns:
                duplicates = df[field].duplicated()
                duplicate_count = duplicates.sum()
                if duplicate_count > 0:
                    duplicate_indices = df[duplicates].index.tolist()
                    issues.append(QualityIssue(
                        check_type=QualityCheckType.UNIQUENESS,
                        severity=QualitySeverity.ERROR,
                        field_name=field,
                        issue_description=f"Field '{field}' has {duplicate_count} duplicate values",
                        affected_rows=duplicate_count,
                        affected_row_indices=duplicate_indices[:100],
                    ))
        
        # Calculate uniqueness score
        total_rows = len(df)
        unique_rows = total_rows - duplicate_count
        uniqueness_score = unique_rows / total_rows if total_rows > 0 else 1.0
        
        return issues, uniqueness_score
    
    def _check_ranges_and_patterns(
        self,
        df: pd.DataFrame,
    ) -> List[QualityIssue]:
        """Check value ranges and patterns"""
        issues = []
        
        for col in df.columns:
            col_rules = self.validation_rules.get("field_rules", {}).get(col, {})
            
            # Range checks
            if "min" in col_rules:
                min_val = col_rules["min"]
                below_min = df[df[col] < min_val].index.tolist()
                if below_min:
                    issues.append(QualityIssue(
                        check_type=QualityCheckType.RANGE_CHECK,
                        severity=QualitySeverity.ERROR,
                        field_name=col,
                        issue_description=f"Field '{col}' has values below minimum {min_val}",
                        affected_rows=len(below_min),
                        affected_row_indices=below_min[:100],
                    ))
            
            if "max" in col_rules:
                max_val = col_rules["max"]
                above_max = df[df[col] > max_val].index.tolist()
                if above_max:
                    issues.append(QualityIssue(
                        check_type=QualityCheckType.RANGE_CHECK,
                        severity=QualitySeverity.ERROR,
                        field_name=col,
                        issue_description=f"Field '{col}' has values above maximum {max_val}",
                        affected_rows=len(above_max),
                        affected_row_indices=above_max[:100],
                    ))
            
            # Pattern checks
            if "pattern" in col_rules:
                import re
                pattern = col_rules["pattern"]
                invalid = df[df[col].notna() & ~df[col].astype(str).str.match(pattern)].index.tolist()
                if invalid:
                    issues.append(QualityIssue(
                        check_type=QualityCheckType.PATTERN_MATCH,
                        severity=QualitySeverity.ERROR,
                        field_name=col,
                        issue_description=f"Field '{col}' has values that don't match pattern {pattern}",
                        affected_rows=len(invalid),
                        affected_row_indices=invalid[:100],
                    ))
        
        return issues
    
    def _check_custom_rules(
        self,
        df: pd.DataFrame,
    ) -> List[QualityIssue]:
        """Check custom validation rules"""
        issues = []
        
        custom_rules = self.validation_rules.get("custom_rules", [])
        
        for rule in custom_rules:
            rule_name = rule.get("name", "Unknown")
            rule_expression = rule.get("expression")
            severity_str = rule.get("severity", "WARNING")
            
            if not rule_expression:
                continue
            
            try:
                # Evaluate rule expression (simplified - in production use a proper expression evaluator)
                # This is a placeholder - actual implementation would use a safe expression evaluator
                result = eval(rule_expression, {"df": df, "pd": pd, "np": np})
                
                if isinstance(result, pd.Series):
                    invalid_indices = df[~result].index.tolist()
                    if len(invalid_indices) > 0:
                        issues.append(QualityIssue(
                            check_type=QualityCheckType.CUSTOM_RULE,
                            severity=QualitySeverity[severity_str],
                            issue_description=f"Custom rule '{rule_name}' failed",
                            affected_rows=len(invalid_indices),
                            affected_row_indices=invalid_indices[:100],
                            rule_name=rule_name,
                        ))
            except Exception as e:
                # Rule evaluation failed
                issues.append(QualityIssue(
                    check_type=QualityCheckType.CUSTOM_RULE,
                    severity=QualitySeverity.WARNING,
                    issue_description=f"Custom rule '{rule_name}' evaluation failed: {str(e)}",
                    affected_rows=0,
                    rule_name=rule_name,
                ))
        
        return issues
    
    def _profile_data(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Dict[str, Any]]:
        """Generate data profiling statistics"""
        statistics = {}
        
        for col in df.columns:
            col_stats = {
                "count": len(df),
                "null_count": df[col].isna().sum(),
                "null_percentage": (df[col].isna().sum() / len(df)) * 100 if len(df) > 0 else 0,
                "unique_count": df[col].nunique(),
                "unique_percentage": (df[col].nunique() / len(df)) * 100 if len(df) > 0 else 0,
            }
            
            # Numeric statistics
            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats.update({
                    "min": float(df[col].min()) if df[col].notna().any() else None,
                    "max": float(df[col].max()) if df[col].notna().any() else None,
                    "mean": float(df[col].mean()) if df[col].notna().any() else None,
                    "median": float(df[col].median()) if df[col].notna().any() else None,
                    "std": float(df[col].std()) if df[col].notna().any() else None,
                })
            
            # Sample values
            sample_values = df[col].dropna().head(5).tolist()
            col_stats["sample_values"] = [str(v) for v in sample_values]
            
            statistics[col] = col_stats
        
        return statistics

