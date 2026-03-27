"""
Tests for the pension-planning endpoints and helper function.

Covers:
- calculate_pension_value (pure function – no DB, no HTTP)
- POST /pension/plans              (create)
- GET  /pension/plans              (list)
- GET  /pension/plans/{id}         (detail)
- PUT  /pension/plans/{id}         (update)
- DELETE /pension/plans/{id}       (delete)
- POST /pension/calculate          (projection without saving)
- Validation: retirement_age must be > current_age
"""
import pytest
from backend.main import calculate_pension_value


# ---------------------------------------------------------------------------
# Unit tests – calculate_pension_value (pure function)
# ---------------------------------------------------------------------------

class TestCalculatePensionValue:
    def test_zero_return_linear_growth(self):
        """With 0% return the result equals savings + total contributions."""
        result = calculate_pension_value(
            current_age=30,
            retirement_age=65,
            monthly_contribution=500.0,
            current_savings=10_000.0,
            expected_return=0.0,
        )
        expected = 10_000.0 + 500.0 * (35 * 12)  # 35 years × 12 months
        assert result == pytest.approx(expected, rel=1e-6)

    def test_positive_return_exceeds_linear(self):
        """With a positive return the projected value exceeds the linear sum."""
        linear = 10_000.0 + 500.0 * (30 * 12)
        result = calculate_pension_value(
            current_age=35,
            retirement_age=65,
            monthly_contribution=500.0,
            current_savings=10_000.0,
            expected_return=7.0,
        )
        assert result > linear

    def test_zero_contribution_only_grows_savings(self):
        """With no monthly contribution only the lump sum grows."""
        result = calculate_pension_value(
            current_age=50,
            retirement_age=65,
            monthly_contribution=0.0,
            current_savings=100_000.0,
            expected_return=5.0,
        )
        # Should be greater than the initial savings
        assert result > 100_000.0

    def test_zero_savings_and_contributions_returns_zero(self):
        """With nothing to start and no contributions the result is zero."""
        result = calculate_pension_value(
            current_age=30,
            retirement_age=65,
            monthly_contribution=0.0,
            current_savings=0.0,
            expected_return=5.0,
        )
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_one_year_to_retirement(self):
        """Edge case: one year to retirement still produces a valid positive result."""
        result = calculate_pension_value(
            current_age=64,
            retirement_age=65,
            monthly_contribution=1000.0,
            current_savings=50_000.0,
            expected_return=5.0,
        )
        assert result > 50_000.0


# ---------------------------------------------------------------------------
# Integration tests – HTTP endpoints
# ---------------------------------------------------------------------------

_PLAN_PAYLOAD = {
    "name": "My Retirement Plan",
    "current_age": 30,
    "target_retirement_age": 65,
    "monthly_contribution": 500.0,
    "current_savings": 10_000.0,
    "expected_return": 7.0,
}


@pytest.mark.asyncio
async def test_create_pension_plan(auth_client):
    """POST /pension/plans creates a plan and returns projected value."""
    resp = await auth_client.post("/pension/plans", json=_PLAN_PAYLOAD)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "My Retirement Plan"
    assert data["current_age"] == 30
    assert data["target_retirement_age"] == 65
    assert "projected_value" in data
    assert data["projected_value"] > 0


@pytest.mark.asyncio
async def test_create_pension_plan_invalid_retirement_age(auth_client):
    """Retirement age ≤ current age is rejected with 400."""
    payload = {**_PLAN_PAYLOAD, "target_retirement_age": 25}
    resp = await auth_client.post("/pension/plans", json=payload)
    assert resp.status_code == 400
    assert "retirement age" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_pension_plan_unauthenticated(test_client):
    """POST /pension/plans without auth returns 401."""
    resp = await test_client.post("/pension/plans", json=_PLAN_PAYLOAD)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_pension_plans(auth_client):
    """GET /pension/plans returns a list of plans for the current user."""
    await auth_client.post("/pension/plans", json=_PLAN_PAYLOAD)
    await auth_client.post(
        "/pension/plans", json={**_PLAN_PAYLOAD, "name": "Second Plan"}
    )

    resp = await auth_client.get("/pension/plans")
    assert resp.status_code == 200, resp.text
    plans = resp.json()
    assert isinstance(plans, list)
    names = [p["name"] for p in plans]
    assert "My Retirement Plan" in names
    assert "Second Plan" in names


@pytest.mark.asyncio
async def test_get_pension_plan(auth_client):
    """GET /pension/plans/{id} returns a single plan."""
    create_resp = await auth_client.post("/pension/plans", json=_PLAN_PAYLOAD)
    plan_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/pension/plans/{plan_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == plan_id


@pytest.mark.asyncio
async def test_get_pension_plan_not_found(auth_client):
    """GET /pension/plans/99999 returns 404."""
    resp = await auth_client.get("/pension/plans/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_pension_plan(auth_client):
    """PUT /pension/plans/{id} updates contribution and recalculates projection."""
    create_resp = await auth_client.post("/pension/plans", json=_PLAN_PAYLOAD)
    plan_id = create_resp.json()["id"]
    original_projection = create_resp.json()["projected_value"]

    resp = await auth_client.put(
        f"/pension/plans/{plan_id}",
        json={"monthly_contribution": 1000.0},
    )
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["monthly_contribution"] == 1000.0
    # Higher contribution → larger projection
    assert updated["projected_value"] > original_projection


@pytest.mark.asyncio
async def test_update_pension_plan_not_found(auth_client):
    """PUT /pension/plans/99999 returns 404."""
    resp = await auth_client.put(
        "/pension/plans/99999", json={"monthly_contribution": 500.0}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_pension_plan(auth_client):
    """DELETE /pension/plans/{id} removes the plan (204)."""
    create_resp = await auth_client.post(
        "/pension/plans", json={**_PLAN_PAYLOAD, "name": "To Delete"}
    )
    plan_id = create_resp.json()["id"]

    del_resp = await auth_client.delete(f"/pension/plans/{plan_id}")
    assert del_resp.status_code == 204

    get_resp = await auth_client.get(f"/pension/plans/{plan_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_pension_plan_not_found(auth_client):
    """DELETE /pension/plans/99999 returns 404."""
    resp = await auth_client.delete("/pension/plans/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /pension/calculate (stateless projection)
# ---------------------------------------------------------------------------

_CALC_PAYLOAD = {
    "current_age": 35,
    "retirement_age": 65,
    "monthly_contribution": 500.0,
    "current_savings": 20_000.0,
    "expected_return": 6.0,
}


@pytest.mark.asyncio
async def test_pension_calculate_returns_projections(test_client):
    """POST /pension/calculate returns year-by-year projections."""
    resp = await test_client.post("/pension/calculate", json=_CALC_PAYLOAD)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "projections" in data
    assert len(data["projections"]) == 30  # 65 - 35 years
    first = data["projections"][0]
    assert "year" in first
    assert "total_value" in first
    assert "total_contributions" in first


@pytest.mark.asyncio
async def test_pension_calculate_final_value_positive(test_client):
    """The final projected value is greater than initial savings."""
    resp = await test_client.post("/pension/calculate", json=_CALC_PAYLOAD)
    data = resp.json()
    final = data["projections"][-1]["total_value"]
    assert final > _CALC_PAYLOAD["current_savings"]


@pytest.mark.asyncio
async def test_pension_calculate_invalid_retirement_age(test_client):
    """retirement_age ≤ current_age returns 400."""
    payload = {**_CALC_PAYLOAD, "retirement_age": 30}
    resp = await test_client.post("/pension/calculate", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_pension_calculate_missing_field(test_client):
    """Missing required field returns 422."""
    resp = await test_client.post(
        "/pension/calculate",
        json={"current_age": 35},
    )
    assert resp.status_code == 422
