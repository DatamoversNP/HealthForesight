# Conversational AI - Advanced Production Features

## Overview

This document describes the advanced production features implemented for the Conversational Policy Intelligence Layer:
1. Vector Search with Embeddings
2. Fine-tuning Support
3. Query Caching
4. Rate Limiting
5. Cost Tracking

## 1. Vector Search with Embeddings

### What It Does

Replaces keyword matching with semantic similarity using embeddings:
- Generates embeddings for policies, pipelines, baselines
- Stores embeddings in vector store
- Searches using cosine similarity
- Returns most semantically similar results

### Configuration

```bash
USE_VECTOR_SEARCH=true
EMBEDDING_PROVIDER=openai  # or "local"
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_PATH=./data/vector_store
```

### How It Works

1. **Indexing**: When policies are created/updated, generate embeddings
2. **Storage**: Store embeddings in vector store (file-based or vector DB)
3. **Query**: Generate embedding for user query
4. **Search**: Find similar embeddings using cosine similarity
5. **Results**: Return top K most similar items

### Implementation

- `VectorStore`: Manages embeddings storage and search
- `EmbeddingService`: Generates embeddings (OpenAI or local fallback)
- `RAGService`: Uses vector search when enabled

### Example

**Before (Keyword)**:
- Query: "MRI authorization"
- Matches: Policies with "MRI" or "authorization" in text

**After (Vector)**:
- Query: "MRI authorization"
- Embedding: [0.123, -0.456, ...]
- Matches: Policies semantically similar to MRI authorization
- Results: Prior auth policies, imaging policies, etc.

## 2. Fine-tuning Support

### What It Does

Enables use of fine-tuned models trained on policy data:
- Configure fine-tuned model ID
- Use fine-tuned model for better policy understanding
- Fallback to base model if fine-tuned unavailable

### Configuration

```bash
ENABLE_FINE_TUNING=true
FINE_TUNED_MODEL_ID=ft:gpt-4-2024-01-01:org:model:abc123
```

### Fine-tuning Process (External)

1. **Data Preparation**: Collect policy creation examples
2. **Format**: Convert to fine-tuning format (JSONL)
3. **Training**: Train model via OpenAI/Anthropic API
4. **Deployment**: Use fine-tuned model ID in config

### Usage

Fine-tuned models are automatically used when:
- `ENABLE_FINE_TUNING=true`
- `FINE_TUNED_MODEL_ID` is set
- Model is available

## 3. Query Caching

### What It Does

Caches query results to reduce LLM API calls:
- Cache based on query, mode, domain, user roles
- Configurable TTL (default: 1 hour)
- Multiple backends: memory, file, Redis

### Configuration

```bash
ENABLE_QUERY_CACHE=true
CACHE_TTL_SECONDS=3600  # 1 hour
CACHE_BACKEND=memory  # or "redis", "file"
```

### Cache Backends

**Memory** (default):
- Fast, in-memory cache
- Limited to single process
- Good for development

**File**:
- Persistent across restarts
- Slower than memory
- Good for single-server deployments

**Redis**:
- Distributed cache
- Fast and scalable
- Good for production

### Cache Key Generation

Cache key includes:
- Query text (normalized)
- Mode (DRAFT/EXPLAIN/QUERY)
- Domain (POLICY/DATA/etc.)
- User roles (sorted)

### Example

**First Request**:
- Query: "Create MRI policy"
- Cache miss → Call LLM → Store result

**Second Request** (within TTL):
- Query: "Create MRI policy"
- Cache hit → Return cached result

## 4. Rate Limiting

### What It Does

Prevents abuse by limiting requests per user:
- Per-minute limit (default: 10)
- Per-hour limit (default: 100)
- Returns 429 when exceeded

### Configuration

```bash
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

### How It Works

1. Track request timestamps per user
2. Clean up expired timestamps
3. Check limits before processing
4. Return 429 if exceeded

### Rate Limit Status

Users can check their rate limit status:
```
GET /api/v1/conversational-ai/rate-limit-status
```

Returns:
```json
{
  "remaining_minute": 8,
  "remaining_hour": 95,
  "limit_per_minute": 10,
  "limit_per_hour": 100
}
```

## 5. Cost Tracking

### What It Does

Tracks LLM API costs:
- Per-user cost tracking
- Per-model cost tracking
- Daily cost summaries
- Token usage tracking

### Configuration

```bash
ENABLE_COST_TRACKING=true
COST_TRACKING_PATH=./data/cost_tracking
```

### Cost Calculation

Costs calculated based on:
- Provider (OpenAI, Anthropic)
- Model (GPT-4, Claude, etc.)
- Input tokens
- Output tokens

Current rates (as of 2024):
- GPT-4 Turbo: $0.01/1K input, $0.03/1K output
- GPT-3.5 Turbo: $0.0015/1K input, $0.002/1K output
- Claude 3 Opus: $0.015/1K input, $0.075/1K output

### Cost Data Structure

Daily cost file:
```json
{
  "date": "2024-01-15",
  "total_cost": 12.50,
  "requests": 150,
  "total_input_tokens": 50000,
  "total_output_tokens": 20000,
  "by_user": {
    "user-123": {
      "cost": 5.00,
      "requests": 50,
      "input_tokens": 20000,
      "output_tokens": 8000
    }
  },
  "by_model": {
    "openai:gpt-4-turbo-preview": {
      "cost": 12.50,
      "requests": 150,
      "input_tokens": 50000,
      "output_tokens": 20000
    }
  }
}
```

### Cost API

**Get User Costs**:
```
GET /api/v1/conversational-ai/costs?days=30
```

**Get All Costs** (Admin only):
```
GET /api/v1/conversational-ai/costs?days=30
```

## 6. Integration

### Service Updates

All features integrated into `ConversationalAIService`:

```python
class ConversationalAIService:
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_service = RAGService()  # With vector search
        self.safety_guardrails = SafetyGuardrails()
        self.query_cache = QueryCache()  # NEW
        self.rate_limiter = RateLimiter()  # NEW
        self.cost_tracker = CostTracker()  # NEW
```

### Request Flow

```
User Request
    ↓
Rate Limiter → Check limits
    ↓
Query Cache → Check cache
    ↓ (if miss)
RAG Service → Retrieve context (vector search)
    ↓
LLM Client → Generate response
    ↓
Cost Tracker → Track costs
    ↓
Query Cache → Store result
    ↓
Response
```

## 7. Files Created

### Vector Search
- `apps/api/src/uepi_api/services/vector_store.py` - Vector store and embeddings

### Caching
- `apps/api/src/uepi_api/services/query_cache.py` - Query caching system

### Rate Limiting
- `apps/api/src/uepi_api/services/rate_limiter.py` - Rate limiting

### Cost Tracking
- `apps/api/src/uepi_api/services/cost_tracker.py` - Cost tracking

### Updates
- `apps/api/src/uepi_api/config.py` - New configuration options
- `apps/api/src/uepi_api/services/rag_service.py` - Vector search integration
- `apps/api/src/uepi_api/services/conversational_ai_service.py` - Feature integration
- `apps/api/src/uepi_api/services/llm_client.py` - Token usage tracking
- `apps/api/src/uepi_api/routers/conversational_ai.py` - New endpoints

## 8. Production Deployment

### Recommended Settings

```bash
# Vector Search
USE_VECTOR_SEARCH=true
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

# Caching
ENABLE_QUERY_CACHE=true
CACHE_BACKEND=redis
CACHE_TTL_SECONDS=3600

# Rate Limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# Cost Tracking
ENABLE_COST_TRACKING=true
```

### Monitoring

- **Costs**: Review daily cost files
- **Rate Limits**: Monitor 429 responses
- **Cache Hit Rate**: Track cache effectiveness
- **Vector Search**: Monitor embedding generation time

## 9. Next Steps

1. **Vector Database**: Migrate to Pinecone/Weaviate for scale
2. **Fine-tuning**: Train models on policy data
3. **Cache Warming**: Pre-populate cache with common queries
4. **Cost Alerts**: Set up alerts for cost thresholds
5. **Rate Limit Tiers**: Different limits for different user roles

