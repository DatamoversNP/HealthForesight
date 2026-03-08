"""
Data-driven narrative generation module
No LLM - purely rule-based based on actual data metrics
"""

from uepi_common.narrative.data_driven_narrative import DataDrivenNarrativeGenerator
from uepi_common.narrative.calculation_validator import CalculationValidator

__all__ = [
    "DataDrivenNarrativeGenerator",
    "CalculationValidator",
]

