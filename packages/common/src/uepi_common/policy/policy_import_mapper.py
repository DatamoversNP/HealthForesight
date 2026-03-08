"""
Policy Import Mapper
Maps external policy exports (CSV/Excel/vendor dumps) → PolicyLogic
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
import json

from ..data_contracts.policy_logic import PolicyLogic, PolicyLever, PolicyScope, LeverType
from ..data_contracts.policy_metadata import get_policy_type_metadata, LeverType as LeverTypeEnum


class PolicyImportMapper:
    """Maps external policy formats to canonical PolicyLogic"""
    
    def __init__(self):
        self.mapping_rules: Dict[str, Dict[str, str]] = {}
    
    def map_from_csv(self, file_path: Path, mapping_config: Optional[Dict[str, Any]] = None) -> List[PolicyLogic]:
        """
        Map CSV file to PolicyLogic objects
        
        Expected CSV columns (can be mapped):
        - policy_name, policy_description, policy_owner
        - lob, markets, network_id
        - lever_type, lever_name, lever_parameters (JSON)
        - effective_start, effective_end
        """
        df = pd.read_csv(file_path)
        policies = []
        
        # Group by policy identifier (if present)
        policy_group_col = mapping_config.get("policy_group_column", "policy_name") if mapping_config else "policy_name"
        
        if policy_group_col in df.columns:
            for policy_name, group_df in df.groupby(policy_group_col):
                policy = self._create_policy_from_group(group_df, mapping_config)
                if policy:
                    policies.append(policy)
        else:
            # Single policy from entire file
            policy = self._create_policy_from_group(df, mapping_config)
            if policy:
                policies.append(policy)
        
        return policies
    
    def map_from_excel(self, file_path: Path, sheet_name: Optional[str] = None, mapping_config: Optional[Dict[str, Any]] = None) -> List[PolicyLogic]:
        """Map Excel file to PolicyLogic objects"""
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
        
        return self.map_from_csv(Path(file_path), mapping_config)  # Reuse CSV logic
    
    def map_from_json(self, file_path: Path, mapping_config: Optional[Dict[str, Any]] = None) -> List[PolicyLogic]:
        """Map JSON file to PolicyLogic objects"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return [self._map_json_object(item) for item in data]
        elif isinstance(data, dict):
            return [self._map_json_object(data)]
        else:
            raise ValueError("Invalid JSON structure")
    
    def _create_policy_from_group(self, df: pd.DataFrame, mapping_config: Optional[Dict[str, Any]]) -> Optional[PolicyLogic]:
        """Create a PolicyLogic object from a DataFrame group"""
        if df.empty:
            return None
        
        # Extract policy-level fields
        policy_name = self._get_field_value(df, "policy_name", mapping_config)
        policy_description = self._get_field_value(df, "policy_description", mapping_config)
        policy_owner = self._get_field_value(df, "policy_owner", mapping_config)
        
        # Extract scope
        scope = PolicyScope(
            line_of_business=self._get_list_field(df, "lob", mapping_config),
            markets=self._get_list_field(df, "markets", mapping_config),
            network_id=self._get_field_value(df, "network_id", mapping_config),
        )
        
        # Extract levers
        levers = []
        for _, row in df.iterrows():
            lever_type_str = self._get_field_value(row, "lever_type", mapping_config)
            if lever_type_str:
                try:
                    lever_type = LeverTypeEnum(lever_type_str)
                    lever = self._create_lever_from_row(row, lever_type, mapping_config)
                    if lever:
                        levers.append(lever)
                except ValueError:
                    continue  # Skip invalid lever types
        
        if not levers:
            return None
        
        # Extract effective dates
        effective_start = self._get_date_field(df, "effective_start", mapping_config)
        effective_end = self._get_date_field(df, "effective_end", mapping_config)
        
        # Create policy
        from ..data_contracts.policy_logic import PolicyLogic
        from datetime import date
        
        return PolicyLogic(
            policy_name=policy_name or "Imported Policy",
            policy_description=policy_description,
            policy_owner=policy_owner or "Unknown",
            scope=scope,
            levers=levers,
            effective_start=effective_start or date.today(),
            effective_end=effective_end,
        )
    
    def _create_lever_from_row(self, row: pd.Series, lever_type: LeverTypeEnum, mapping_config: Optional[Dict[str, Any]]) -> Optional[PolicyLever]:
        """Create a PolicyLever from a DataFrame row"""
        lever_name = self._get_field_value(row, "lever_name", mapping_config) or lever_type.value
        
        # Extract parameters (can be JSON string or individual columns)
        parameters = {}
        params_json = self._get_field_value(row, "lever_parameters", mapping_config)
        if params_json:
            try:
                if isinstance(params_json, str):
                    parameters = json.loads(params_json)
                else:
                    parameters = params_json
            except:
                pass
        
        # Try to extract individual parameter columns
        metadata = get_policy_type_metadata(lever_type)
        if metadata:
            for param in metadata.supported_parameters:
                param_value = self._get_field_value(row, f"lever_{param.name}", mapping_config)
                if param_value is not None:
                    parameters[param.name] = param_value
        
        return PolicyLever(
            lever_type=lever_type,
            name=lever_name,
            parameters=parameters,
        )
    
    def _get_field_value(self, source: pd.DataFrame | pd.Series, field: str, mapping_config: Optional[Dict[str, Any]]) -> Optional[Any]:
        """Get field value with mapping support"""
        if mapping_config and field in mapping_config:
            mapped_field = mapping_config[field]
            if mapped_field in source:
                return source[mapped_field].iloc[0] if isinstance(source, pd.DataFrame) else source[mapped_field]
        elif field in source:
            value = source[field].iloc[0] if isinstance(source, pd.DataFrame) else source[field]
            return value if pd.notna(value) else None
        return None
    
    def _get_list_field(self, df: pd.DataFrame, field: str, mapping_config: Optional[Dict[str, Any]]) -> List[str]:
        """Get list field (comma-separated or array)"""
        value = self._get_field_value(df, field, mapping_config)
        if value is None:
            return []
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        elif isinstance(value, list):
            return [str(v) for v in value]
        else:
            return [str(value)]
    
    def _get_date_field(self, df: pd.DataFrame, field: str, mapping_config: Optional[Dict[str, Any]]) -> Optional[Any]:
        """Get date field"""
        value = self._get_field_value(df, field, mapping_config)
        if value is None:
            return None
        if isinstance(value, pd.Timestamp):
            return value.date()
        elif isinstance(value, str):
            from datetime import datetime
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except:
                return None
        return value
    
    def _map_json_object(self, obj: Dict[str, Any]) -> PolicyLogic:
        """Map a JSON object to PolicyLogic"""
        from ..data_contracts.policy_logic import PolicyLogic, PolicyScope, PolicyLever
        from datetime import date
        
        # Extract scope
        scope_data = obj.get("scope", {})
        scope = PolicyScope(
            line_of_business=scope_data.get("line_of_business", []),
            markets=scope_data.get("markets", []),
            network_id=scope_data.get("network_id"),
        )
        
        # Extract levers
        levers = []
        for lever_data in obj.get("levers", []):
            lever_type = LeverTypeEnum(lever_data["lever_type"])
            lever = PolicyLever(
                lever_type=lever_type,
                name=lever_data.get("name", lever_type.value),
                parameters=lever_data.get("parameters", {}),
            )
            levers.append(lever)
        
        # Create policy
        return PolicyLogic(
            policy_name=obj.get("policy_name", "Imported Policy"),
            policy_description=obj.get("policy_description"),
            policy_owner=obj.get("policy_owner", "Unknown"),
            scope=scope,
            levers=levers,
            effective_start=date.fromisoformat(obj.get("effective_start", date.today().isoformat())),
            effective_end=date.fromisoformat(obj["effective_end"]) if obj.get("effective_end") else None,
        )

