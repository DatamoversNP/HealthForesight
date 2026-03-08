# Conversational AI - Production Enhancements

## Overview

This document describes the production enhancements added to the Conversational Policy Intelligence Layer, including LLM integration, RAG, prompt templates, and safety guardrails.

## 1. LLM Integration

### Supported Providers

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet
- **Local Fallback**: Rule-based parsing when LLM is unavailable

### Configuration

Add to `.env` or environment variables:

```bash
# LLM Provider
LLM_PROVIDER=openai  # or "anthropic" or "local"

# OpenAI
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# LLM Settings
LLM_TEMPERATURE=0.3  # Lower for more deterministic outputs
LLM_MAX_TOKENS=2000
```

### Usage

The system automatically:
1. Tries to use configured LLM provider
2. Falls back to local rule-based parsing if LLM unavailable
3. Logs all LLM interactions for audit

## 2. RAG (Retrieval-Augmented Generation)

### What It Does

RAG retrieves relevant context from:
- **Policies**: Similar policies based on query
- **Pipelines**: Existing data pipelines
- **Baselines**: Relevant baseline configurations
- **Observations**: Impact analysis results

### Configuration

```bash
ENABLE_RAG=true
RAG_TOP_K=5  # Number of context chunks to retrieve
```

### How It Works

1. User sends query
2. RAG service searches policies/pipelines/baselines
3. Top K relevant items retrieved
4. Context included in LLM prompt
5. LLM generates response with context awareness

### Example

**User Query**: "Create a prior auth policy for MRI in Texas"

**RAG Retrieves**:
- Similar MRI policies
- Texas-specific policies
- Prior auth policies

**LLM Uses Context**: Generates policy referencing similar policies

## 3. Prompt Templates

### Template Library

Templates organized by domain and mode:

- **Policy Domain**: `CREATE_POLICY`, `MODIFY_POLICY`
- **Data Domain**: `CREATE_PIPELINE`
- **Baseline Domain**: `CREATE_BASELINE`
- **Impact Domain**: `EXPLAIN_IMPACT`
- **Governance Domain**: `QUERY_POLICIES`

### Template Structure

Each template includes:
- System instructions
- Role-aware context
- RAG context integration
- Structured output format
- Safety guidelines

### Adding New Templates

1. Create template in `prompt_templates.py`
2. Add to appropriate domain dictionary
3. Register in `get_template()` function

## 4. Enhanced Parsing

### Improvements

- **Better Policy Parsing**: Handles complex policy types, composite policies
- **RAG-Enhanced**: Uses similar policies for reference
- **Date Parsing**: Improved date extraction
- **Exception Handling**: Better exception detection
- **Multi-condition Support**: Handles nested conditions

### Example

**Before**: Simple regex matching
**After**: 
- RAG context retrieval
- Similar policy reference
- Enhanced exception detection
- Better date parsing

## 5. Safety Guardrails

### What's Protected

- **Prohibited Actions**: Never allow auto-approval, deletion, bypass
- **High-Risk Patterns**: Detect dangerous operations
- **Unauthorized Access**: Prevent privilege escalation
- **Status Validation**: Ensure DRAFT status for new artifacts
- **Role Permissions**: Validate user permissions

### Safety Checks

1. **Content Filtering**: Scans prompts and outputs
2. **Pattern Detection**: Identifies dangerous patterns
3. **Output Sanitization**: Removes dangerous fields
4. **Permission Validation**: Checks role permissions
5. **Status Enforcement**: Forces DRAFT status

### Example

**User Request**: "Approve and activate this policy immediately"

**Safety Check**:
- Detects "approve" and "activate" patterns
- Blocks request
- Returns: "Request blocked: Prohibited action detected"

## 6. Architecture

```
User Query
    ↓
RAG Service (retrieves context)
    ↓
Prompt Template (builds system prompt)
    ↓
LLM Client (generates response)
    ↓
Safety Guardrails (validates output)
    ↓
Sanitized Response
```

## 7. Files Created

### LLM Integration
- `apps/api/src/uepi_api/services/llm_client.py` - LLM client abstraction
- `apps/api/src/uepi_api/services/__init__.py` - Service exports

### RAG System
- `apps/api/src/uepi_api/services/rag_service.py` - Context retrieval

### Prompt Templates
- `apps/api/src/uepi_api/services/prompt_templates.py` - Template library

### Safety
- `apps/api/src/uepi_api/services/safety_guardrails.py` - Content filtering

### Configuration
- Updated `apps/api/src/uepi_api/config.py` - LLM settings

### Service Updates
- Updated `apps/api/src/uepi_api/services/conversational_ai_service.py` - Integration

## 8. Installation

### Install LLM Packages

```bash
# OpenAI
pip install openai

# Anthropic
pip install anthropic
```

### Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Add your API keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 9. Testing

### Test LLM Integration

1. Set `LLM_PROVIDER=openai` in `.env`
2. Add `OPENAI_API_KEY`
3. Send query: "Create a prior auth policy for MRI"
4. Verify LLM response

### Test RAG

1. Create some policies
2. Send query: "Create a similar policy"
3. Verify RAG retrieves similar policies
4. Check context in LLM prompt

### Test Safety

1. Try: "Approve this policy immediately"
2. Verify request is blocked
3. Check safety violations in response

## 10. Production Checklist

- [ ] Configure LLM provider and API keys
- [ ] Enable RAG (`ENABLE_RAG=true`)
- [ ] Set appropriate `RAG_TOP_K`
- [ ] Enable safety guardrails (`ENABLE_SAFETY_GUARDRAILS=true`)
- [ ] Review prompt templates
- [ ] Test with real policies/data
- [ ] Monitor LLM costs
- [ ] Set up audit log review
- [ ] Configure rate limiting
- [ ] Set up error alerting

## 11. Next Steps

1. **Vector Search**: Replace keyword matching with embeddings
2. **Fine-tuning**: Fine-tune models on policy data
3. **Caching**: Cache common queries
4. **Rate Limiting**: Add rate limits per user
5. **Cost Tracking**: Track LLM API costs
6. **A/B Testing**: Test different prompts/models

