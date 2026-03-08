# Conversational Policy Intelligence Layer - Implementation Guide

## Overview

The Conversational Policy Intelligence Layer is a **governed, role-aware, action-generating interface** that translates natural language into structured system actions. It is **NOT autonomous** - it generates proposals that go through existing workflows and approvals.

## Architecture

```
UI / API / Dashboards
        ↑
Conversational AI Layer (NEW)
        ↑
Policy Engine | Data Engine | Models | Workflows
        ↑
Data Store / Pipelines
```

**Key Rule**: The Conversational AI layer **never executes actions directly**. It generates structured proposals that go through existing workflows.

## Components Created

### Backend Components

1. **Data Models** (`apps/api/src/uepi_api/models/conversational_ai.py`)
   - `Conversation`: Conversation session
   - `ConversationMessage`: Individual messages
   - `ConversationArtifact`: Structured artifacts (policies, pipelines, etc.)
   - `ConversationAuditLog`: Complete audit trail

2. **Storage Layer** (`apps/api/src/uepi_api/storage_conversational_ai.py`)
   - File-based storage for conversations
   - Artifact management
   - Audit log storage

3. **AI Service** (`apps/api/src/uepi_api/services/conversational_ai_service.py`)
   - LLM integration (ready for OpenAI, Anthropic, etc.)
   - Structured output generation
   - Role-aware prompt building
   - Domain-specific parsing

4. **API Router** (`apps/api/src/uepi_api/routers/conversational_ai.py`)
   - `/api/v1/conversational-ai/conversations` - Create/list conversations
   - `/api/v1/conversational-ai/conversations/{id}` - Get conversation
   - `/api/v1/conversational-ai/conversations/{id}/messages` - Send message
   - `/api/v1/conversational-ai/conversations/{id}/artifacts/{id}/submit` - Submit artifact
   - `/api/v1/conversational-ai/audit-logs` - Get audit logs (admin only)

### Frontend Components

1. **ConversationalAIPanel** (`apps/web/src/components/conversational-ai/ConversationalAIPanel.tsx`)
   - Full chat interface
   - Mode selector (Draft/Explain/Query)
   - Domain selector
   - Structured output display
   - Artifact review and submission

2. **ConversationalAIButton** (`apps/web/src/components/conversational-ai/ConversationalAIButton.tsx`)
   - Floating action button
   - Always accessible from any page

3. **API Client Methods** (`apps/web/src/lib/api.ts`)
   - `createConversation()`
   - `listConversations()`
   - `getConversation()`
   - `sendMessage()`
   - `submitArtifact()`
   - `getAuditLogs()`

## Three Modes

### Mode 1: DRAFT
- AI proposes configurations (policies, pipelines, baselines)
- Generates structured artifacts
- Requires review and approval
- **Never auto-executes**

### Mode 2: EXPLAIN
- AI explains system outputs using evidence
- References observed impact results, baselines, models
- Provides confidence scores and limitations
- **Read-only, no modifications**

### Mode 3: QUERY
- AI queries existing data/models
- Translates natural language to system queries
- Presents results clearly
- **Never modifies data**

## Five Domains

### 1. POLICY
- Policy creation and modification
- Generates policy JSON with scope, enforcement, levers
- Handles complex policies (composite, nested, conditional)

### 2. DATA
- Data onboarding and ingestion pipeline configuration
- Generates pipeline YAML/JSON specs
- **Never deploys pipelines - only proposes configs**

### 3. BASELINE
- Baseline creation and explanation
- Generates baseline configuration objects
- Explains what baselines are

### 4. IMPACT
- Observed impact analysis and evidence narration
- References Stage 4 observed impact models
- Compares predicted vs observed
- Provides evidence-based narratives

### 5. GOVERNANCE
- Policy lifecycle queries
- Translates queries into system queries
- Generates alerts and workflow actions
- **Never bypasses approvals**

## Role-Aware Behavior

The same prompt means different things by role:

- **UM Lead**: "Create a new policy" → Policy draft
- **Actuary**: "Create a new policy" → Simulation scenario
- **CFO**: "Create a new policy" → Policy impact summary (read-only)

Conversational AI checks role permissions before responding.

## Structured Output Contract

Every AI response includes:

```json
{
  "natural_language": "Human-readable explanation",
  "structured_output": {
    "action_type": "POLICY_DRAFT",
    "policy_name": "...",
    "scope": {...},
    "conditions": {...},
    "confidence": "DRAFT_ONLY"
  },
  "next_steps": ["Review policy draft", "Submit for approval"],
  "confidence": "HIGH|MEDIUM|LOW",
  "requires_clarification": false,
  "clarification_questions": []
}
```

## Audit & Traceability

Every conversational action logs:
- User
- Role
- Timestamp
- Prompt
- AI response
- Generated artifacts
- Downstream workflow entry

**This is mandatory for enterprise trust, regulatory defensibility, and investor confidence.**

## What Conversational AI Cannot Do

❌ **Cannot**:
- Approve policies
- Change production configurations
- Override baselines
- Generate savings claims without confidence
- Hide assumptions
- Act without audit logs

✅ **Must**:
- Produce structured artifacts
- Enter existing workflows
- Be auditable

## How to Use

### For Users

1. **Access**: Click the floating AI button (bottom-right corner)
2. **Select Mode**: Choose Draft, Explain, or Query
3. **Select Domain**: Choose Policy, Data, Baseline, Impact, or Governance
4. **Start Conversation**: Type your request in natural language
5. **Review Output**: AI generates structured artifacts
6. **Submit**: Review and submit artifacts to workflows

### Example Prompts

**Policy Creation**:
- "Create a prior authorization policy for outpatient MRI for Commercial members in Texas, excluding oncology cases, starting July 1."

**Data Onboarding**:
- "We receive weekly medical claims files from S3 with member, provider, service code, allowed amount. Help me set this up."

**Baseline Creation**:
- "Create a baseline for Commercial MA members excluding Q4 due to incomplete data."

**Impact Explanation**:
- "Why did imaging costs go up even though utilization went down?"

**Governance Query**:
- "Show me all active policies with backfire risk."

## Integration Points

### Policy Creation
- Artifacts route to `create_policy()` in `storage_policies.py`
- Creates policy as DRAFT
- Enters approval workflow

### Pipeline Creation
- Artifacts route to `create_pipeline()` in `storage_pipelines.py`
- Creates pipeline config
- Submits to Data Ops queue (not auto-run)

### Baseline Creation
- Artifacts route to baseline creation workflow
- Generates baseline configuration
- Triggers baseline job after confirmation

## Next Steps for Production

1. **LLM Integration**: Connect to OpenAI/Anthropic API
2. **Enhanced Parsing**: Improve prompt parsing for complex requests
3. **Context Retrieval**: Add RAG for policy/data context
4. **Workflow Integration**: Deep integration with approval workflows
5. **Prompt Templates**: Create approved prompt libraries
6. **Safety Architecture**: Add LLM safety guardrails

## Files Created

### Backend
- `apps/api/src/uepi_api/models/conversational_ai.py`
- `apps/api/src/uepi_api/storage_conversational_ai.py`
- `apps/api/src/uepi_api/services/conversational_ai_service.py`
- `apps/api/src/uepi_api/routers/conversational_ai.py`

### Frontend
- `apps/web/src/components/conversational-ai/ConversationalAIPanel.tsx`
- `apps/web/src/components/conversational-ai/ConversationalAIButton.tsx`

### API Client
- Added methods to `apps/web/src/lib/api.ts`

### Integration
- Router registered in `apps/api/src/uepi_api/main.py`
- Button added to `apps/web/src/components/Layout.tsx`

## Testing

To test the Conversational AI:

1. Start the API server
2. Start the frontend
3. Click the floating AI button (bottom-right)
4. Try prompts like:
   - "Create a prior auth policy for MRI in Texas"
   - "Set up a weekly claims ingestion pipeline"
   - "Explain why policy X had unexpected results"

All interactions are logged and artifacts require approval before execution.

