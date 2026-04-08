from typing import List
from ..core.db import get_client
from ..models.product import Product
from ..core.idempotency import compute_idempotency_key
from .llm import llm

import logging
logger = logging.getLogger("agente.products")


async def scout_once(search_term: str = "trending dropshipping product") -> list[dict]:
    """Scout for products using LLM analysis."""
    logger.info(f"Scouting products for: {search_term}")

    try:
        results = await llm.generate_json(
            prompt=f"""Find 3 trending products for the search term: "{search_term}"

For each product return:
- title: product name
- description: 1-2 sentence description
- niche: market niche
- estimated_margin: percentage (e.g. "40-60%")
- target_audience: who would buy this
- trending_score: 1-10

Return a JSON array of objects.""",
            system="You are an expert e-commerce product scout. Return valid JSON arrays only.",
        )

        rows = []
        if isinstance(results, list):
            for product in results:
                idem = compute_idempotency_key("product", "default", {"title": product.get("title", search_term)})
                rows.append({
                    "title": product.get("title", f"Scouted: {search_term}"),
                    "status": "scouted",
                    "metadata": product,
                    "idempotency_key": idem,
                })
        else:
            idem = compute_idempotency_key("product", "default", {"title": search_term})
            rows.append({"title": f"Scouted: {search_term}", "status": "scouted", "idempotency_key": idem})

        res = get_client().table("products").upsert(rows, on_conflict="idempotency_key").execute()
        return res.data

    except Exception as e:
        logger.error(f"LLM scouting failed: {e}, using fallback")
        idem = compute_idempotency_key("product", "default", {"title": search_term})
        data = {"title": f"Scouted: {search_term}", "status": "scouted", "idempotency_key": idem}
        res = get_client().table("products").upsert(data, on_conflict="idempotency_key").execute()
        return res.data


async def list_products() -> list[Product]:
    res = get_client().table("products").select("*").execute()
    return res.data or []
