# Conversational AI - Quick Start Guide

## What Was Built

A complete **Conversational Policy Intelligence Layer** that:
- ✅ Translates natural language into structured system actions
- ✅ Supports 3 modes: Draft, Explain, Query
- ✅ Supports 5 domains: Policy, Data, Baseline, Impact, Governance
- ✅ Role-aware and permission-checked
- ✅ Full audit logging
- ✅ Never executes directly - always routes through workflows

## How to Access

1. **Floating Button**: Click the AI icon button in the bottom-right corner of any page
2. **Always Available**: The button is accessible from all pages

## Quick Examples

### Policy Creation (Draft Mode)
```
User: "Create a prior authorization policy for outpatient MRI for Commercial members in Texas, excluding oncology cases, starting July 1."

AI: Generates structured policy JSON with:
- Scope: Commercial, Texas, IN network
- Enforcement: Hard deny, PA workflow
- Exceptions: Oncology, Emergency
- Status: DRAFT (requires approval)
```

### Data Pipeline Setup (Draft Mode)
```
User: "We receive weekly medical claims files from S3 with member, provider, service code, allowed amount. Help me set this up."

AI: Generates pipeline configuration with:
- Source: S3
- Frequency: Weekly
- Data type: Claims
- Schema mapping: (asks for clarification)
- Status: DRAFT (submits to Data Ops queue)
```

### Impact Explanation (Explain Mode)
```
User: "Why did imaging costs go up even though utilization went down?"

AI: Provides evidence-based explanation:
- References observed impact results
- Compares predicted vs observed
- Explains substitution effects
- Provides confidence scores
- Cites models and assumptions
```

### Governance Query (Query Mode)
```
User: "Show me all active policies with backfire risk."

AI: Translates to system queries:
- Queries policy database
- Filters by risk indicators
- Presents results with context
```

## Architecture Location

The Conversational AI layer sits **on top of** existing systems:

```
┌─────────────────────────────────────┐
│  UI / Dashboards                    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Conversational AI Layer (NEW)      │
│  - Translates intent → structure    │
│  - Generates proposals               │
│  - Routes to workflows              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Policy Engine | Data Engine         │
│  Models | Workflows                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Data Store / Pipelines             │
└─────────────────────────────────────┘
```

## Key Files

### Backend
- `apps/api/src/uepi_api/models/conversational_ai.py` - Data models
- `apps/api/src/uepi_api/storage_conversational_ai.py` - Storage layer
- `apps/api/src/uepi_api/services/conversational_ai_service.py` - AI service
- `apps/api/src/uepi_api/routers/conversational_ai.py` - API endpoints

### Frontend
- `apps/web/src/components/conversational-ai/ConversationalAIPanel.tsx` - Chat UI
- `apps/web/src/components/conversational-ai/ConversationalAIButton.tsx` - Floating button

### Integration
- Router registered in `apps/api/src/uepi_api/main.py`
- Button added to `apps/web/src/components/Layout.tsx`
- API methods in `apps/web/src/lib/api.ts`

## Testing

1. Start API: `cd apps/api && python3 -m uvicorn uepi_api.main:app --reload --port 8000`
2. Start Frontend: `cd apps/web && npm run dev`
3. Open browser: `http://localhost:3050`
4. Click AI button (bottom-right)
5. Try: "Create a prior auth policy for MRI in Texas"

## Next Steps

For production deployment:
1. Connect to actual LLM (OpenAI/Anthropic)
2. Enhance prompt parsing for complex requests
3. Add RAG for context retrieval
4. Deep workflow integration
5. Prompt template library

