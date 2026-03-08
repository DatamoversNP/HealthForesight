"""Schema mapping and transformation for flexible ingestion"""
from typing import Any, Dict, List, Optional, Callable
import pandas as pd
from datetime import datetime


class SchemaMapper:
    """Map client-provided schemas to canonical schema"""
    
    def __init__(self, mapping_config: Dict[str, Any]):
        """
        Initialize with mapping configuration
        
        mapping_config structure:
        {
            "column_mappings": {
                "client_column": "canonical_column",
                "CLM_ID": "claim_id",
                "MEMBER": "member_id",
            },
            "default_values": {
                "lob": "COMMERCIAL",
                "market": "UNKNOWN",
            },
            "transformations": {
                "service_date": "parse_date",
                "amount": "to_float",
            },
            "required_fields": ["claim_id", "member_id"],
            "optional_fields": ["diagnosis_code"],
        }
        """
        self.mapping_config = mapping_config
        self.column_mappings = mapping_config.get("column_mappings", {})
        self.default_values = mapping_config.get("default_values", {})
        self.transformations = mapping_config.get("transformations", {})
        self.required_fields = mapping_config.get("required_fields", [])
        self.optional_fields = mapping_config.get("optional_fields", [])
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map client column names to canonical names"""
        # Create mapping dict (case-insensitive)
        df_columns_lower = {col.lower(): col for col in df.columns}
        mapping_dict = {}
        
        for client_col, canonical_col in self.column_mappings.items():
            # Try exact match first
            if client_col in df.columns:
                mapping_dict[client_col] = canonical_col
            # Try case-insensitive match
            elif client_col.lower() in df_columns_lower:
                original_col = df_columns_lower[client_col.lower()]
                mapping_dict[original_col] = canonical_col
            # Try partial match (contains)
            else:
                for col in df.columns:
                    if client_col.lower() in col.lower() or col.lower() in client_col.lower():
                        mapping_dict[col] = canonical_col
                        break
        
        # Rename columns
        df_mapped = df.rename(columns=mapping_dict)
        
        return df_mapped
    
    def apply_defaults(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply default values for missing columns"""
        df = df.copy()
        
        for field, default_value in self.default_values.items():
            if field not in df.columns:
                df[field] = default_value
        
        return df
    
    def apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply data transformations"""
        df = df.copy()
        
        transformation_functions = {
            "parse_date": self._parse_date,
            "to_float": self._to_float,
            "to_int": self._to_int,
            "to_string": self._to_string,
            "to_bool": self._to_bool,
            "uppercase": self._uppercase,
            "lowercase": self._lowercase,
        }
        
        for field, transformation in self.transformations.items():
            if field in df.columns:
                if isinstance(transformation, str):
                    func = transformation_functions.get(transformation)
                    if func:
                        df[field] = df[field].apply(func)
                elif callable(transformation):
                    df[field] = df[field].apply(transformation)
        
        return df
    
    def _parse_date(self, value: Any) -> Optional[str]:
        """Parse various date formats to YYYY-MM-DD"""
        if pd.isna(value) or value is None:
            return None
        
        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%Y%m%d",
        ]
        
        for fmt in date_formats:
            try:
                if isinstance(value, str):
                    dt = datetime.strptime(value.strip(), fmt)
                    return dt.strftime("%Y-%m-%d")
                elif isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                continue
        
        return None
    
    def _to_float(self, value: Any) -> Optional[float]:
        """Convert to float, handling various formats"""
        if pd.isna(value) or value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                # Remove currency symbols, commas, etc.
                cleaned = value.replace('$', '').replace(',', '').strip()
                return float(cleaned)
        except (ValueError, TypeError):
            return None
        
        return None
    
    def _to_int(self, value: Any) -> Optional[int]:
        """Convert to integer"""
        if pd.isna(value) or value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                return int(float(value.replace(',', '')))
        except (ValueError, TypeError):
            return None
        
        return None
    
    def _to_string(self, value: Any) -> str:
        """Convert to string"""
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()
    
    def _to_bool(self, value: Any) -> bool:
        """Convert to boolean"""
        if pd.isna(value) or value is None:
            return False
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'y', 't')
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        return False
    
    def _uppercase(self, value: Any) -> str:
        """Convert to uppercase string"""
        return self._to_string(value).upper()
    
    def _lowercase(self, value: Any) -> str:
        """Convert to lowercase string"""
        return self._to_string(value).lower()
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all transformations in order"""
        df = self.map_columns(df)
        df = self.apply_defaults(df)
        df = self.apply_transformations(df)
        return df
    
    def validate_required_fields(self, df: pd.DataFrame) -> List[str]:
        """Check if all required fields are present"""
        missing = []
        for field in self.required_fields:
            if field not in df.columns:
                missing.append(field)
        return missing
    
    @staticmethod
    def auto_detect_mapping(source_df: pd.DataFrame, canonical_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-detect column mappings by comparing source columns to canonical schema
        
        canonical_schema structure:
        {
            "fields": {
                "claim_id": {"type": "string", "required": True},
                "member_id": {"type": "string", "required": True},
                "service_date": {"type": "date", "required": True},
            },
            "aliases": {
                "claim_id": ["clm_id", "claim_number", "claim_num"],
                "member_id": ["member", "mem_id", "patient_id"],
            }
        }
        """
        mappings = {}
        source_cols_lower = {col.lower(): col for col in source_df.columns}
        canonical_fields = canonical_schema.get("fields", {})
        aliases = canonical_schema.get("aliases", {})
        
        for canonical_field, field_info in canonical_fields.items():
            # Check exact match
            if canonical_field in source_df.columns:
                mappings[canonical_field] = canonical_field
                continue
            
            # Check case-insensitive match
            if canonical_field.lower() in source_cols_lower:
                mappings[source_cols_lower[canonical_field.lower()]] = canonical_field
                continue
            
            # Check aliases
            field_aliases = aliases.get(canonical_field, [])
            for alias in field_aliases:
                if alias in source_df.columns:
                    mappings[alias] = canonical_field
                    break
                elif alias.lower() in source_cols_lower:
                    mappings[source_cols_lower[alias.lower()]] = canonical_field
                    break
            
            # Try fuzzy matching (contains)
            if canonical_field not in mappings.values():
                for source_col in source_df.columns:
                    if canonical_field.lower() in source_col.lower() or source_col.lower() in canonical_field.lower():
                        mappings[source_col] = canonical_field
                        break
        
        return {
            "column_mappings": mappings,
            "default_values": {},
            "transformations": {},
            "required_fields": [f for f, info in canonical_fields.items() if info.get("required", False)],
            "optional_fields": [f for f, info in canonical_fields.items() if not info.get("required", False)],
        }

