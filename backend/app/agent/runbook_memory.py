"""Runbook memory store with semantic vector search and cosine similarity."""

import logging
import math
import re
from typing import Any, Dict, List, Optional
import uuid

from app.core.gemini_client import get_gemini_client
from app.models.schemas import Incident, Runbook
from app.storage.base import BaseRepository

logger = logging.getLogger("nightwatch.agent.runbook_memory")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a, b in zip(vec1, vec1)))
    norm2 = math.sqrt(sum(b * b for a, b in zip(vec2, vec2)))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot / (norm1 * norm2)


def keyword_similarity(query: str, target: str) -> float:
    """Fallback token Jaccard similarity when embeddings are unavailable."""
    def tokenize(text: str) -> set[str]:
        return set(re.findall(r"\w{3,}", text.lower()))

    q_tokens = tokenize(query)
    t_tokens = tokenize(target)

    if not q_tokens or not t_tokens:
        return 0.0

    intersection = q_tokens.intersection(t_tokens)
    union = q_tokens.union(t_tokens)
    return len(intersection) / len(union)


async def search_similar_runbooks(
    query: str,
    storage: BaseRepository,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Search historical runbooks using Gemini embeddings with keyword fallback.

    Args:
        query: Symptom or error description query string.
        storage: The storage repository.
        limit: Number of matching runbooks to return.

    Returns:
        List of matched runbooks with similarity score.
    """
    runbooks = storage.list_runbooks(limit=50)
    if not runbooks:
        return []

    # Attempt to embed query
    query_vector: Optional[List[float]] = None
    try:
        gemini = get_gemini_client()
        query_vector = await gemini.embed_content(query)
    except Exception as exc:
        logger.debug("Gemini embedding unavailable for runbook search, using lexical match: %s", exc)

    scored_results = []
    for rb in runbooks:
        score = 0.0
        if query_vector and rb.embedding and len(query_vector) == len(rb.embedding):
            score = cosine_similarity(query_vector, rb.embedding)
        else:
            # Fallback lexical similarity on symptoms and cause
            combined_text = f"{rb.symptoms} {rb.rootCause} {rb.fixApplied}"
            score = keyword_similarity(query, combined_text)

        scored_results.append({
            "id": rb.id,
            "incident_id": rb.incidentId,
            "symptoms": rb.symptoms,
            "root_cause": rb.rootCause,
            "fix_applied": rb.fixApplied,
            "outcome": rb.outcome,
            "similarity_score": round(score, 3),
        })

    # Sort descending by similarity score
    scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_results[:limit]


async def save_incident_to_runbook(
    incident: Incident,
    fix_applied: str,
    storage: BaseRepository,
    outcome: str = "Resolved via rollback",
) -> Runbook:
    """Store a resolved incident in runbook memory with text embedding."""
    symptoms = incident.summary
    root_cause = incident.rootCause or "Investigated and resolved"
    combined_text = f"{symptoms}. Cause: {root_cause}. Fix: {fix_applied}"

    vector: Optional[List[float]] = None
    try:
        gemini = get_gemini_client()
        vector = await gemini.embed_content(combined_text)
    except Exception as exc:
        logger.debug("Could not compute embedding for runbook record: %s", exc)

    runbook = Runbook(
        id=f"rb-{uuid.uuid4().hex[:6]}",
        incidentId=incident.id,
        symptoms=symptoms,
        rootCause=root_cause,
        fixApplied=fix_applied,
        embedding=vector,
        outcome=outcome,
    )

    return storage.create_runbook(runbook)
