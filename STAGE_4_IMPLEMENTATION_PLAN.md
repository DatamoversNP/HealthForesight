# Stage 4 — Observed Policy Impact Implementation Plan

## Overview
Stage 4 measures what happened after policy changes and explains it via substitution + provider/patient behavior.

## Components to Implement

### 1. Enhanced Impact Analysis API Endpoint
- File storage support (like baseline analysis)
- Integration with existing ImpactAnalysisEngine
- Support for DiD, Interrupted Time Series, Pre/Post methods
- Result persistence

### 2. Enhanced Analytics Engines
- **ImpactAnalysisEngine** (exists, needs enhancement):
  - DiD (exists) ✅
  - Interrupted Time Series (needs implementation)
  - Pre/Post (exists) ✅
  
- **SubstitutionDetector** (exists, needs enhancement):
  - Service substitution ✅
  - Site shift ✅
  - Timing shift (needs enhancement)
  - Lag detection (30/60/90 days) ✅
  
- **Leakage Detection** (needs implementation):
  - Out-of-network shifts
  - Alternate coding proxies
  
- **Provider Response Classification** (exists as ProviderSegmentation, needs enhancement):
  - Compliant / Adaptive / Resistant / Circumvention-prone
  
- **Patient Response Signals** (needs implementation):
  - Defer signals
  - Substitute signals
  - ER fallback (segment-level)

### 3. Frontend Page
- Policy Impact Analysis Page (enhance existing AnalysisWorkspacePage or create new)
- Display impact estimates (Δ util, Δ PMPM, Δ allowed)
- Confidence score + limitations
- Substitution pathways ranked
- Provider response distributions
- Patient response indicators
- "Backfire" flags (net cost↑ or ER↑ etc.)

## Implementation Order

1. ✅ Review existing code
2. 🔄 Enhance Impact Analysis API endpoint with file storage support
3. ⏳ Enhance/enhance ImpactAnalysisEngine with Interrupted Time Series
4. ⏳ Implement Leakage Detection
5. ⏳ Enhance Provider Response Classification
6. ⏳ Implement Patient Response Signals
7. ⏳ Create/Enhance Frontend Page
8. ⏳ Add routing

## Next Steps
Start with enhancing the API endpoint to support file storage mode, then build out the missing components.
