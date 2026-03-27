"""
Tests for the insurance endpoints.

Insurance endpoints do not require authentication but DO need a working DB
(for seeding products). We use the test_client fixture from conftest so they
run against the in-memory SQLite database.

Covers:
- GET  /insurance/products                  (list products)
- POST /insurance/recommendations           (personalised recommendations)
"""
import pytest


_BASE_PROFILE = {
    "age": 35,
    "income": 60000,
    "dependents": 2,
    "risk_tolerance": "medium",
    "has_life_insurance": False,
    "has_health_insurance": False,
}


# ---------------------------------------------------------------------------
# /insurance/products
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_insurance_products_returns_list(test_client):
    """GET /insurance/products returns a non-empty list of products."""
    resp = await test_client.get("/insurance/products")
    assert resp.status_code == 200, resp.text
    products = resp.json()
    assert isinstance(products, list)
    assert len(products) > 0


@pytest.mark.asyncio
async def test_insurance_product_fields(test_client):
    """Each product has the expected fields."""
    products = (await test_client.get("/insurance/products")).json()
    required_keys = {"id", "name", "type", "coverage_amount", "monthly_premium", "min_age", "max_age"}
    for product in products:
        assert required_keys.issubset(product.keys()), f"Missing keys in: {product}"


@pytest.mark.asyncio
async def test_insurance_product_types(test_client):
    """Products cover at least life and health insurance types."""
    products = (await test_client.get("/insurance/products")).json()
    types = {p["type"] for p in products}
    assert "life" in types
    assert "health" in types


# ---------------------------------------------------------------------------
# /insurance/recommendations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recommendations_returns_list(test_client):
    """POST /insurance/recommendations returns a list of recommendations."""
    resp = await test_client.post("/insurance/recommendations", json=_BASE_PROFILE)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


@pytest.mark.asyncio
async def test_recommendations_structure(test_client):
    """Each recommendation has product, score and reason fields."""
    data = (await test_client.post("/insurance/recommendations", json=_BASE_PROFILE)).json()
    for rec in data["recommendations"]:
        assert "product" in rec
        assert "score" in rec
        assert "reason" in rec
        assert 0 <= rec["score"] <= 100


@pytest.mark.asyncio
async def test_recommendations_sorted_by_score(test_client):
    """Recommendations are returned in descending score order."""
    data = (await test_client.post("/insurance/recommendations", json=_BASE_PROFILE)).json()
    scores = [r["score"] for r in data["recommendations"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_recommendations_has_totals(test_client):
    """Response includes total_recommended_coverage and total_monthly_premium."""
    data = (await test_client.post("/insurance/recommendations", json=_BASE_PROFILE)).json()
    assert "total_recommended_coverage" in data
    assert "total_monthly_premium" in data
    assert data["total_recommended_coverage"] >= 0
    assert data["total_monthly_premium"] >= 0


@pytest.mark.asyncio
async def test_recommendations_low_risk_gets_life_insurance(test_client):
    """A user with low risk tolerance and no life insurance is recommended life cover."""
    profile = {**_BASE_PROFILE, "risk_tolerance": "low", "has_life_insurance": False}
    data = (await test_client.post("/insurance/recommendations", json=profile)).json()
    product_types = [r["product"]["type"] for r in data["recommendations"]]
    assert "life" in product_types


@pytest.mark.asyncio
async def test_recommendations_age_below_minimum_rejected(test_client):
    """age < 18 is rejected with 422 (schema enforces ge=18)."""
    profile = {**_BASE_PROFILE, "age": 5}
    resp = await test_client.post("/insurance/recommendations", json=profile)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_recommendations_missing_field(test_client):
    """Missing required field returns 422."""
    resp = await test_client.post(
        "/insurance/recommendations",
        json={"age": 30},  # missing income, dependents, etc.
    )
    assert resp.status_code == 422
