"""RAG (Retrieval-Augmented Generation) Service for context retrieval"""
from typing import List, Dict, Any, Optional
from uuid import UUID
import json
from pathlib import Path
import numpy as np

from uepi_api.storage_policies import list_policies, get_policy
from uepi_api.storage_pipelines import list_pipelines
from uepi_api.storage_baselines import list_baselines
from uepi_api.storage_observations import list_observations
from uepi_api.config import get_settings
from uepi_api.services.vector_store import VectorStore, EmbeddingService

settings = get_settings()


class RAGService:
    """Retrieval-Augmented Generation service for context retrieval"""
    
    def __init__(self):
        self.top_k = settings.rag_top_k if settings.enable_rag else 0
        self.use_vector_search = settings.use_vector_search if settings.enable_rag else False
        
        if self.use_vector_search:
            self.vector_store = VectorStore()
            self.embedding_service = EmbeddingService()
        else:
            self.vector_store = None
            self.embedding_service = None
    
    async def retrieve_policy_context(
        self,
        tenant_id: UUID,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant policies based on query"""
        if not settings.enable_rag:
            return []
        
        top_k = top_k or self.top_k
        
        # Use vector search if enabled
        if self.use_vector_search and self.vector_store and self.embedding_service:
            return await self._retrieve_policies_vector(query, tenant_id, top_k)
        else:
            return self._retrieve_policies_keyword(query, tenant_id, top_k)
    
    async def _retrieve_policies_vector(
        self,
        query: str,
        tenant_id: UUID,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve policies using vector search"""
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        query_embedding_np = np.array(query_embedding)
        
        # Search vector store
        similar = self.vector_store.search_similar(
            query_embedding_np,
            entity_type="policy",
            top_k=top_k,
            threshold=0.7
        )
        
        # Get full policy data
        results = []
        for item in similar:
            policy_id = UUID(item["entity_id"])
            try:
                policy = get_policy(policy_id, tenant_id)
                if policy:
                    results.append({
                        "type": "policy",
                        "id": item["entity_id"],
                        "name": policy.get("name") or policy.get("policy_name"),
                        "description": policy.get("description", "")[:200],
                        "policy_type": policy.get("policy_type"),
                        "relevance": "HIGH" if item["similarity"] > 0.9 else "MEDIUM",
                        "score": item["similarity"]
                    })
            except Exception:
                continue
        
        return results
    
    def _retrieve_policies_keyword(
        self,
        query: str,
        tenant_id: UUID,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve policies using keyword matching"""
        # Get all policies
        all_policies = list_policies(tenant_id)
        
        # Simple keyword matching
        query_lower = query.lower()
        relevant_policies = []
        
        for policy in all_policies:
            score = 0
            
            # Check policy name
            name = (policy.get("name") or policy.get("policy_name", "")).lower()
            if any(term in name for term in query_lower.split()):
                score += 3
            
            # Check description
            desc = (policy.get("description") or "").lower()
            if any(term in desc for term in query_lower.split()):
                score += 2
            
            # Check policy type
            policy_type = (policy.get("policy_type") or "").lower()
            if any(term in policy_type for term in query_lower.split()):
                score += 1
            
            if score > 0:
                relevant_policies.append({
                    "policy": policy,
                    "score": score,
                    "relevance": "HIGH" if score >= 3 else "MEDIUM" if score >= 2 else "LOW"
                })
        
        # Sort by score and return top K
        relevant_policies.sort(key=lambda x: x["score"], reverse=True)
        
        return [
            {
                "type": "policy",
                "id": p["policy"].get("id") or p["policy"].get("policy_id"),
                "name": p["policy"].get("name") or p["policy"].get("policy_name"),
                "description": p["policy"].get("description", "")[:200],
                "policy_type": p["policy"].get("policy_type"),
                "relevance": p["relevance"],
                "score": p["score"]
            }
            for p in relevant_policies[:top_k]
        ]
    
    def retrieve_data_context(
        self,
        tenant_id: UUID,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant data pipelines/datasets based on query"""
        if not settings.enable_rag:
            return []
        
        top_k = top_k or self.top_k
        
        # Get all pipelines
        all_pipelines = list_pipelines(tenant_id)
        
        query_lower = query.lower()
        relevant_pipelines = []
        
        for pipeline in all_pipelines:
            score = 0
            
            name = (pipeline.get("pipeline_name") or pipeline.get("name", "")).lower()
            if any(term in name for term in query_lower.split()):
                score += 2
            
            desc = (pipeline.get("pipeline_description") or "").lower()
            if any(term in desc for term in query_lower.split()):
                score += 1
            
            if score > 0:
                relevant_pipelines.append({
                    "pipeline": pipeline,
                    "score": score
                })
        
        relevant_pipelines.sort(key=lambda x: x["score"], reverse=True)
        
        return [
            {
                "type": "pipeline",
                "id": p["pipeline"].get("id") or p["pipeline"].get("pipeline_id"),
                "name": p["pipeline"].get("pipeline_name") or p["pipeline"].get("name"),
                "description": p["pipeline"].get("pipeline_description", "")[:200],
                "source_type": p["pipeline"].get("source_type"),
                "score": p["score"]
            }
            for p in relevant_pipelines[:top_k]
        ]
    
    def retrieve_baseline_context(
        self,
        tenant_id: UUID,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant baselines based on query"""
        if not settings.enable_rag:
            return []
        
        top_k = top_k or self.top_k
        
        try:
            all_baselines = list_baselines(tenant_id)
        except Exception:
            return []
        
        query_lower = query.lower()
        relevant_baselines = []
        
        for baseline in all_baselines:
            score = 0
            
            name = (baseline.get("name") or baseline.get("baseline_name", "")).lower()
            if any(term in name for term in query_lower.split()):
                score += 2
            
            if score > 0:
                relevant_baselines.append({
                    "baseline": baseline,
                    "score": score
                })
        
        relevant_baselines.sort(key=lambda x: x["score"], reverse=True)
        
        return [
            {
                "type": "baseline",
                "id": b["baseline"].get("id") or b["baseline"].get("baseline_id"),
                "name": b["baseline"].get("name") or b["baseline"].get("baseline_name"),
                "score": b["score"]
            }
            for b in relevant_baselines[:top_k]
        ]
    
    def retrieve_impact_context(
        self,
        tenant_id: UUID,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant impact observations based on query"""
        if not settings.enable_rag:
            return []
        
        top_k = top_k or self.top_k
        
        try:
            all_observations = list_observations(tenant_id)
        except Exception:
            return []
        
        query_lower = query.lower()
        relevant_observations = []
        
        for observation in all_observations:
            score = 0
            
            policy_id = observation.get("policy_id")
            if policy_id:
                # Try to get policy name
                try:
                    policy = get_policy(policy_id, tenant_id)
                    if policy:
                        name = (policy.get("name") or policy.get("policy_name", "")).lower()
                        if any(term in name for term in query_lower.split()):
                            score += 2
                except Exception:
                    pass
            
            if score > 0:
                relevant_observations.append({
                    "observation": observation,
                    "score": score
                })
        
        relevant_observations.sort(key=lambda x: x["score"], reverse=True)
        
        return [
            {
                "type": "observation",
                "id": o["observation"].get("id") or o["observation"].get("observation_id"),
                "policy_id": o["observation"].get("policy_id"),
                "score": o["score"]
            }
            for o in relevant_observations[:top_k]
        ]
    
    async def retrieve_context(
        self,
        tenant_id: UUID,
        query: str,
        domain: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve relevant context across all domains"""
        context = {
            "policies": [],
            "pipelines": [],
            "baselines": [],
            "observations": []
        }
        
        if domain == "POLICY" or not domain:
            context["policies"] = await self.retrieve_policy_context(tenant_id, query, top_k)
        
        if domain == "DATA" or not domain:
            context["pipelines"] = self.retrieve_data_context(tenant_id, query, top_k)
        
        if domain == "BASELINE" or not domain:
            context["baselines"] = self.retrieve_baseline_context(tenant_id, query, top_k)
        
        if domain == "IMPACT" or not domain:
            context["observations"] = self.retrieve_impact_context(tenant_id, query, top_k)
        
        return context

