"""Cost tracking for LLM API usage"""
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from uepi_api.config import get_settings
from uepi_api.storage_file import BASE_PATH

settings = get_settings()

# Cost per 1K tokens (as of 2024)
COST_PER_1K_TOKENS = {
    "openai": {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    },
    "anthropic": {
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    }
}


class CostTracker:
    """Track LLM API costs"""
    
    def __init__(self):
        self.enabled = settings.enable_cost_tracking
        self.cost_dir = Path(settings.cost_tracking_path)
        self.cost_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cost_file(self, date: Optional[datetime] = None) -> Path:
        """Get cost tracking file for date"""
        if date is None:
            date = datetime.now(timezone.utc)
        date_str = date.strftime("%Y-%m-%d")
        return self.cost_dir / f"costs-{date_str}.json"
    
    def _load_daily_costs(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Load cost data for a day"""
        cost_file = self._get_cost_file(date)
        if cost_file.exists():
            try:
                with open(cost_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "date": (date or datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
            "total_cost": 0.0,
            "requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "by_user": {},
            "by_model": {}
        }
    
    def _save_daily_costs(self, costs: Dict[str, Any]):
        """Save cost data for a day"""
        cost_file = self._get_cost_file(datetime.fromisoformat(costs["date"]))
        with open(cost_file, 'w') as f:
            json.dump(costs, f, indent=2)
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int = 0
    ) -> float:
        """Calculate cost for API call"""
        provider_costs = COST_PER_1K_TOKENS.get(provider, {})
        model_costs = provider_costs.get(model, {"input": 0.0, "output": 0.0})
        
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        
        return input_cost + output_cost
    
    def track_request(
        self,
        user_id: UUID,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
        request_type: str = "llm"
    ):
        """Track a single API request"""
        if not self.enabled:
            return
        
        cost = self.calculate_cost(provider, model, input_tokens, output_tokens)
        
        costs = self._load_daily_costs()
        costs["total_cost"] += cost
        costs["requests"] += 1
        costs["total_input_tokens"] += input_tokens
        costs["total_output_tokens"] += output_tokens
        
        # Track by user
        user_key = str(user_id)
        if user_key not in costs["by_user"]:
            costs["by_user"][user_key] = {
                "cost": 0.0,
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0
            }
        costs["by_user"][user_key]["cost"] += cost
        costs["by_user"][user_key]["requests"] += 1
        costs["by_user"][user_key]["input_tokens"] += input_tokens
        costs["by_user"][user_key]["output_tokens"] += output_tokens
        
        # Track by model
        model_key = f"{provider}:{model}"
        if model_key not in costs["by_model"]:
            costs["by_model"][model_key] = {
                "cost": 0.0,
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0
            }
        costs["by_model"][model_key]["cost"] += cost
        costs["by_model"][model_key]["requests"] += 1
        costs["by_model"][model_key]["input_tokens"] += input_tokens
        costs["by_model"][model_key]["output_tokens"] += output_tokens
        
        self._save_daily_costs(costs)
    
    def get_daily_costs(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get cost summary for a day"""
        return self._load_daily_costs(date)
    
    def get_user_costs(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get cost summary for a user over multiple days"""
        total_cost = 0.0
        total_requests = 0
        daily_costs = []
        
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            costs = self._load_daily_costs(date)
            user_key = str(user_id)
            
            if user_key in costs.get("by_user", {}):
                user_costs = costs["by_user"][user_key]
                total_cost += user_costs["cost"]
                total_requests += user_costs["requests"]
                daily_costs.append({
                    "date": costs["date"],
                    "cost": user_costs["cost"],
                    "requests": user_costs["requests"]
                })
        
        return {
            "user_id": str(user_id),
            "total_cost": total_cost,
            "total_requests": total_requests,
            "days": days,
            "daily_costs": daily_costs
        }

