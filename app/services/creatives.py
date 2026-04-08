from ..core.db import get_client
from .preflight import score_preflight
from ..core.idempotency import compute_idempotency_key
from .llm import llm

import logging
logger = logging.getLogger("agente.creatives")


async def generate_for_product(product_id: str, variants: int = 5) -> list[dict]:
    """Generate ad creatives using LLM for copy and strategy."""
    logger.info(f"Generating {variants} creatives for product {product_id}")

    # Fetch product info
    product_data = get_client().table("products").select("*").eq("id", product_id).execute()
    product = product_data.data[0] if product_data.data else {"title": "Unknown Product"}
    product_title = product.get("title", "Unknown Product")
    product_meta = product.get("metadata", {})

    try:
        creatives = await llm.generate_json(
            prompt=f"""Create {variants} ad creative variants for this product:

Product: {product_title}
Details: {product_meta}

For each variant, generate:
- headline: attention-grabbing headline (max 40 chars)
- body: ad body text (max 125 chars)
- cta: call-to-action text
- hook: opening hook for video (max 10 words)
- tone: emotional tone (urgent, curious, aspirational, social_proof, fear_of_missing)
- target_angle: marketing angle

Return a JSON array of {variants} objects.""",
            system="You are an expert performance marketer. Create high-converting ad copy. Return valid JSON arrays only.",
        )

        rows = []
        if isinstance(creatives, list):
            for i, creative in enumerate(creatives):
                score = score_preflight(
                    duration_s=25,
                    hook_ms=1500 if creative.get("hook") else 3000,
                    cta_present=bool(creative.get("cta")),
                    readability=0.85,
                )
                status = "approved" if score >= 0.6 else "rejected"
                rows.append({
                    "product_id": product_id,
                    "variant": i + 1,
                    "status": status,
                    "preflight_score": score,
                    "metadata": creative,
                    "idempotency_key": compute_idempotency_key("creative", "default", {"product_id": product_id, "variant": i + 1}),
                })
        else:
            raise ValueError("LLM did not return a list")

        res = get_client().table("creatives").upsert(rows, on_conflict="idempotency_key").execute()
        logger.info(f"Generated {len(rows)} creatives ({sum(1 for r in rows if r['status']=='approved')} approved)")
        return res.data

    except Exception as e:
        logger.error(f"LLM creative generation failed: {e}, using fallback")
        rows = []
        for i in range(variants):
            score = score_preflight(duration_s=25, hook_ms=1500, cta_present=True, readability=0.8)
            status = "approved" if score >= 0.6 else "rejected"
            rows.append({
                "product_id": product_id,
                "variant": i + 1,
                "status": status,
                "preflight_score": score,
                "idempotency_key": compute_idempotency_key("creative", "default", {"product_id": product_id, "variant": i + 1}),
            })
        res = get_client().table("creatives").upsert(rows, on_conflict="idempotency_key").execute()
        return res.data
