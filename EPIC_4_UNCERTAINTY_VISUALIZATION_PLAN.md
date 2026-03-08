# Epic 4: Uncertainty & Risk Visualization - Implementation Plan

## Overview

Epic 4 adds uncertainty visualization and risk management capabilities to help users understand the range of possible outcomes and key risk factors for policy decisions.

## Requirements

### Backend Components

1. **Forecast Distribution Storage** (`storage_forecasts.py`)
   - Store forecast distributions (P10/P50/P90, confidence intervals)
   - Link to policies, decisions, or analyses
   - Support multiple forecast scenarios

2. **Sensitivity Parameter Storage** (`storage_sensitivity.py`)
   - Store sensitivity analysis parameters
   - Track which parameters drive uncertainty
   - Store parameter ranges and distributions

3. **Scenario Run Storage** (`storage_scenarios.py`)
   - Store scenario analysis runs
   - Link scenarios to forecasts
   - Track scenario parameters and outcomes

4. **Risk Register Storage** (`storage_risks.py`)
   - Store identified risks
   - Risk scoring and prioritization
   - Risk mitigation tracking

5. **Uncertainty Visualization API** (`routers/uncertainty_visualization.py`)
   - Endpoints for forecasts, sensitivity, scenarios, risks
   - CRUD operations for all uncertainty/risk entities

### Frontend Components

1. **Fan Chart Component** (`FanChart.tsx`)
   - Visualize forecast distributions
   - Show P10/P50/P90 ranges
   - Confidence intervals visualization

2. **Sensitivity Panel** (`SensitivityPanel.tsx`)
   - Display sensitivity analysis results
   - Show top uncertainty drivers
   - Parameter impact visualization

3. **Risk Register Component** (`RiskRegister.tsx`)
   - Display risk register
   - Risk scoring and filtering
   - Risk mitigation tracking

4. **Integration**
   - Add to Policy Workspace (new "Uncertainty" tab)
   - Add to Decision Workspace
   - Add to Analysis results

## Data Models (Already Defined)

From `models_enhanced.py`:
- `Forecast` - Forecast distribution with uncertainty ranges
- `SensitivityParameter` - Parameter sensitivity analysis
- `Scenario` - Scenario analysis with parameters
- `RiskDriver` - Risk factor identification
- `UncertaintyRange` - P10/P50/P90 ranges (already used in Epic 3)
- `ConfidenceInterval` - Confidence intervals (already used in Epic 3)

## Implementation Order

1. **Storage Modules** (Backend)
   - `storage_forecasts.py`
   - `storage_sensitivity.py`
   - `storage_scenarios.py`
   - `storage_risks.py`

2. **API Endpoints** (Backend)
   - `routers/uncertainty_visualization.py`
   - Register in `main.py`

3. **Frontend Components**
   - `FanChart.tsx`
   - `SensitivityPanel.tsx`
   - `RiskRegister.tsx`

4. **Integration**
   - Add to Policy Workspace
   - Add to Decision Workspace
   - Add to Analysis results

## Next Steps

Start with storage modules, then API endpoints, then frontend components.


