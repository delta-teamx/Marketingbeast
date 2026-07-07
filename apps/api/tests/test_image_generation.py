"""Post-image generation: the content engine attaches an AI image to each post.

Claude can't render images, so it writes an art-direction prompt and the image
provider renders it into media_urls — which the publish path already sends to
Meta alongside the caption.
"""

from __future__ import annotations

import uuid

from app.models.brand import Brand
from app.models.content import ContentType
from app.models.organization import Organization
from app.services.content_engine import GeneratedIdea, _mock_ideas, persist_ideas
from app.services.image_provider import ImageBrief, MockImageProvider, get_image_provider


async def test_mock_image_provider_returns_stable_public_url() -> None:
    p = MockImageProvider()
    url1 = await p.generate(ImageBrief(prompt="a red sports car at sunset"))
    url2 = await p.generate(ImageBrief(prompt="a red sports car at sunset"))
    url3 = await p.generate(ImageBrief(prompt="a blue truck"))
    assert url1 and url1.startswith("https://")
    assert url1 == url2  # deterministic
    assert url1 != url3  # prompt-dependent


def test_default_provider_is_mock() -> None:
    assert get_image_provider().name == "mock"


def test_mock_ideas_include_an_image_prompt() -> None:
    brand = Brand(name="Glove Cars", industry_vertical="auto dealership")
    ideas = _mock_ideas(brand, "fall sale", 3)
    assert all(i.image_prompt for i in ideas)


async def test_persist_ideas_attaches_generated_image(db) -> None:
    org = Organization(name="Acme", slug=f"acme-{uuid.uuid4().hex[:8]}", is_personal=True)
    db.add(org)
    await db.flush()
    brand = Brand(org_id=org.id, name="Glove Cars", industry_vertical="auto")
    db.add(brand)
    await db.flush()

    ideas = [
        GeneratedIdea(body="Post one", content_type=ContentType.post, image_prompt="a car"),
        # A reel should NOT get a still image (it gets video elsewhere).
        GeneratedIdea(body="Reel two", content_type=ContentType.reel, image_prompt="a car"),
        # An idea with no image prompt stays text-only.
        GeneratedIdea(body="Post three", content_type=ContentType.post, image_prompt=""),
    ]
    items = await persist_ideas(db, brand_id=brand.id, ideas=ideas)
    by_body = {i.body.split("\n")[0]: i for i in items}

    assert by_body["Post one"].media_urls and by_body["Post one"].media_urls[0].startswith("https://")
    assert by_body["Reel two"].media_urls is None
    assert by_body["Post three"].media_urls is None
