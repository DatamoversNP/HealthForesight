# Epic 4: Uncertainty & Risk Visualization - Implementation Complete ✅

## Overview
Epic 4 provides comprehensive uncertainty visualization and risk management capabilities, enabling users to:
- Create and visualize forecast distributions with P10/P50/P90 ranges
- Run scenario analyses with sensitivity parameters
- Manage risk registers with risk drivers and mitigation actions

## Implementation Status: 100% Complete

### Backend Components ✅

#### 1. Storage Modules
- **`storage_forecasts.py`**: File-based CRUD for forecast distributions
  - Create, read, list, and update forecasts
  - Supports uncertainty ranges (P10/P50/P90) and confidence intervals
  
- **`storage_scenarios.py`**: File-based CRUD for scenario runs
  - Create, read, list, and update scenarios
  - Manages sensitivity parameters and results
  
- **`storage_risks.py`**: File-based CRUD for risk registers
  - Create, read, list, and update risk registers
  - Manages risk drivers with impact scores and mitigation actions

#### 2. API Endpoints (`routers/uncertainty_visualization.py`)
- **Forecast Endpoints:**
  - `POST /api/v1/forecasts` - Create forecast
  - `GET /api/v1/forecasts` - List forecasts (with optional filtering)
  - `GET /api/v1/forecasts/{forecast_id}` - Get forecast details

- **Scenario Endpoints:**
  - `POST /api/v1/scenarios` - Create scenario run
  - `GET /api/v1/scenarios` - List scenarios (with optional filtering)
  - `GET /api/v1/scenarios/{scenario_id}` - Get scenario details
  - `PUT /api/v1/scenarios/{scenario_id}` - Update scenario

- **Risk Register Endpoints:**
  - `POST /api/v1/risks` - Create or update risk register
  - `GET /api/v1/risks` - List risk registers (with optional filtering)
  - `GET /api/v1/risks/policy/{policy_id}` - Get risk register for policy
  - `PUT /api/v1/risks/policy/{policy_id}/drivers/{driver_name}` - Update risk driver

### Frontend Components ✅

#### 1. Core Visualization Components
- **`FanChart.tsx`**: Fan chart visualization for forecast distributions
  - Displays P10/P50/P90 ranges as shaded areas
  - Shows point estimates and confidence intervals
  - Time series visualization with uncertainty widening over time
  - Uses Recharts for interactive charts

- **`SensitivityPanel.tsx`**: Sensitivity analysis display
  - Shows sensitivity parameters with impact analysis
  - Highlights top 3 uncertainty drivers
  - Visual progress bars for impact scores
  - Sorted by uncertainty contribution

- **`RiskRegister.tsx`**: Risk register management
  - Displays risk drivers with impact scores
  - Shows uncertainty contributions and mitigation actions
  - Edit risk drivers inline
  - Overall risk score visualization

#### 2. Management Components
- **`ForecastManager.tsx`**: Forecast creation and management
  - Create new forecasts with uncertainty ranges
  - List all forecasts
  - View forecasts in fan chart
  - Form validation for P10 < P50 < P90

- **`ScenarioManager.tsx`**: Scenario creation and management
  - Create scenario runs with sensitivity parameters
  - Add multiple sensitivity parameters per scenario
  - View scenario sensitivity analysis
  - List all scenarios

#### 3. Integration
- **Policy Workspace Integration**: Added 3 new tabs
  - "Forecasts" tab (index 10)
  - "Scenarios" tab (index 11)
  - "Risk Register" tab (index 12)
  
- **API Client Methods**: All Epic 4 endpoints integrated
  - `createForecast()`, `getForecasts()`, `getForecast()`
  - `createScenario()`, `getScenarios()`, `getScenario()`, `updateScenario()`
  - `createOrUpdateRiskRegister()`, `getRiskRegisters()`, `getRiskRegisterForPolicy()`, `updateRiskDriver()`

## Data Models

### ForecastDistribution
```typescript
{
  forecast_id: UUID
  metric_name: string
  point_estimate: number
  uncertainty_range: {
    p10: number
    p50: number
    p90: number
  }
  confidence_interval?: {
    lower_bound: number
    upper_bound: number
    confidence_level: number
  }
  distribution_data?: any
  created_at: datetime
}
```

### ScenarioRun
```typescript
{
  scenario_id: UUID
  scenario_name: string
  parameters: Record<string, number>
  sensitivity_parameters: Array<{
    parameter_name: string
    base_value: number
    min_value: number
    max_value: number
    step_size?: number
  }>
  results: Record<string, ForecastDistribution>
  created_at: datetime
}
```

### RiskRegister
```typescript
{
  policy_id: UUID
  top_drivers: Array<{
    driver_name: string
    impact_score: number  // 0-1
    uncertainty_contribution: number
    mitigation_action?: string
    owner?: UUID
  }>
  overall_risk_score: number  // 0-1
  last_updated: datetime
}
```

## File Structure

```
apps/api/src/uepi_api/
├── storage_forecasts.py          # Forecast storage
├── storage_scenarios.py           # Scenario storage
├── storage_risks.py              # Risk register storage
└── routers/
    └── uncertainty_visualization.py  # API endpoints

apps/web/src/
├── components/uncertainty/
│   ├── FanChart.tsx              # Fan chart visualization
│   ├── SensitivityPanel.tsx          # Sensitivity analysis
│   ├── RiskRegister.tsx          # Risk register management
│   ├── ForecastManager.tsx       # Forecast CRUD
│   └── ScenarioManager.tsx       # Scenario CRUD
├── pages/
│   └── PolicyWorkspacePage.tsx   # Integrated Epic 4 tabs
└── lib/
    └── api.ts                    # API client methods
```

## Usage

### Creating a Forecast
1. Navigate to Policy Workspace → "Forecasts" tab
2. Click "Create Forecast"
3. Enter metric name, point estimate, and P10/P50/P90 values
4. Optionally add confidence interval
5. Click "Create" to save

### Creating a Scenario
1. Navigate to Policy Workspace → "Scenarios" tab
2. Click "Create Scenario"
3. Enter scenario name
4. Add sensitivity parameters (parameter name, base/min/max values)
5. Click "Create" to save

### Viewing Risk Register
1. Navigate to Policy Workspace → "Risk Register" tab
2. View existing risk drivers and overall risk score
3. Click edit icon to update risk driver details
4. Add mitigation actions and assign owners

## Testing

### Backend Testing
```bash
# Test forecast endpoints
curl -X POST http://localhost:8000/api/v1/forecasts \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "Total Cost",
    "point_estimate": 1000000,
    "uncertainty_range": {
      "p10": 800000,
      "p50": 1000000,
      "p90": 1200000
    }
  }'

# Test scenario endpoints
curl -X POST http://localhost:8000/api/v1/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "Base Case",
    "sensitivity_parameters": [{
      "parameter_name": "Utilization Rate",
      "base_value": 0.75,
      "min_value": 0.65,
      "max_value": 0.85
    }]
  }'
```

### Frontend Testing
1. Start API server: `cd apps/api && python3 -m uvicorn uepi_api.main:app --reload --port 8000`
2. Start frontend: `cd apps/web && npm run dev`
3. Navigate to a policy workspace
4. Test each Epic 4 tab:
   - Create forecasts and view fan charts
   - Create scenarios and view sensitivity analysis
   - View and edit risk registers

## Next Steps (Future Enhancements)

1. **Delete Functionality**: Add delete endpoints for forecasts and scenarios
2. **Scenario Results**: Backend logic to compute scenario results from sensitivity parameters
3. **Risk Driver Creation**: UI to add new risk drivers (currently only edit existing)
4. **Export/Import**: Export forecasts and scenarios for sharing
5. **Advanced Visualizations**: 
   - Tornado charts for sensitivity analysis
   - Heat maps for scenario comparisons
   - Risk matrix visualizations

## Notes

- All storage is file-based (JSON files in `data/` directory)
- UUIDs are safely handled with `_safe_uuid` helper functions
- Frontend includes comprehensive error handling and validation
- All components are integrated into the Policy Workspace for easy access
- API endpoints follow RESTful conventions and include proper error handling

---

**Status**: ✅ Epic 4 is complete and ready for testing!

