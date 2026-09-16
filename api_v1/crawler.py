"""
Crawler API
Standalone endpoint to fetch a URL and extract text/links/metadata, for
ad-hoc testing outside of a full workflow. The same logic backs the
CRAWLER_AGENT workflow node (core/workflow_engine.py).
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.crawler_client import CrawlerClient

router = APIRouter(prefix="/crawler", tags=["crawler"])


class CrawlRequest(BaseModel):
    url: str
    selector: str = "body"
    base_url: Optional[str] = None


@router.post("/fetch")
async def fetch(payload: CrawlRequest):
    """Fetch a URL and return its extracted text, links, and metadata together."""

    client = CrawlerClient()
    page = await client.fetch_page(payload.url)

    if page["status"] == "error" or (isinstance(page["status"], int) and page["status"] >= 400):
        raise HTTPException(status_code=502, detail=f"Fetch failed: {page.get('error', page.get('status'))}")

    html = page["content"]

    return {
        "url": payload.url,
        "status": page["status"],
        "text": client.extract_text(html, selector=payload.selector),
        "links": client.extract_links(html, base_url=payload.base_url or payload.url),
        "metadata": client.extract_metadata(html),
    }
