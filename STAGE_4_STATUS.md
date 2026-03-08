# Stage 4 — Observed Policy Impact Implementation Status

## Overview
Stage 4 measures what happened after policy changes and explains it via substitution + provider/patient behavior.

## Current Status

### ✅ Already Implemented
1. **ImpactAnalysisEngine** (`packages/common/src/uepi_common/analytics/impact.py`)
   - Difference-in-Differences (DiD) ✅
   - Pre/Post analysis ✅
   - Bootstrap confidence intervals ✅
   
2. **SubstitutionDetector** (`packages/common/src/uepi_common/analytics/substitution.py`)
   - Service substitution detection ✅
   - Site shift detection ✅
   - Lag detection (30/60/90 days) ✅
   
3. **ProviderSegmentation** (`packages/common/src/uepi_common/analytics/provider_segmentation.py`)
   - Provider clustering/archetypes ✅
   - Provider response patterns ✅
   
4. **API Endpoint** (`/analyses/impact`)
   - Creates impact analysis ✅
   - Triggers worker jobs ✅
   - **BUT**: Only works with database mode (needs file storage support)

5. **Comparison with Baseline and Predicted Impact** ✅
   - Compares observed outcomes against baseline (Stage 3) ✅
   - Compares observed outcomes against predicted impact (Stage 3.5) ✅
   - Includes prediction error and accuracy metrics ✅
   - Results included in `comparisons` field of analysis results ✅

6. **Frontend Page** (`AnalysisWorkspacePage.tsx`)
   - Basic UI for impact analysis ✅
   - **BUT**: Needs enhancement for Stage 4 features (including comparison visualization)

### 🔄 Needs Enhancement/Implementation

1. **File Storage Support**
   - Impact analysis endpoint needs file storage mode (like baseline analysis)
   - Policy retrieval in file storage mode
   
2. **Interrupted Time Series**
   - Add to ImpactAnalysisEngine (currently only DiD and Pre/Post)
   
3. **Leakage Detection**
   - Out-of-network shifts
   - Alternate coding proxies
   - **NEW MODULE NEEDED**
   
4. **Provider Response Classification Enhancement**
   - Enhance existing ProviderSegmentation to classify as:
     - Compliant
     - Adaptive
     - Resistant
     - Circumvention-prone
   
5. **Patient Response Signals**
   - Defer signals
   - Substitute signals
   - ER fallback (segment-level)
   - **NEW MODULE NEEDED**
   
6. **Frontend Enhancements**
   - Display all Stage 4 outputs:
     - Impact estimates (Δ util, Δ PMPM, Δ allowed)
     - Confidence score + limitations
     - Substitution pathways ranked
     - Provider response distributions
     - Patient response indicators
     - "Backfire" flags (net cost↑ or ER↑ etc.)

## Implementation Approach

Given the existing infrastructure, the fastest path to Stage 4 completion:

1. **Enhance Impact Analysis Endpoint** (Priority 1)
   - Add file storage support
   - Run analysis synchronously (like baseline) for file storage mode
   - Integrate all components (DiD, substitution, provider/patient behavior)
   
2. **Enhance Analytics Engines** (Priority 2)
   - Add Interrupted Time Series to ImpactAnalysisEngine
   - Create Leakage Detection module
   - Enhance ProviderSegmentation with response classification
   - Create Patient Response Signals module
   
3. **Frontend** (Priority 3)
   - Enhance AnalysisWorkspacePage or create new PolicyImpactAnalysisPage
   - Add charts and visualizations for all Stage 4 outputs

## Next Steps

Starting with enhancing the impact analysis endpoint to support file storage mode and integrate all Stage 4 components.
