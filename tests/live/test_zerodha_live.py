import pytest

@pytest.mark.live
async def test_profile_returns_real_client_id(broker):
    profile = await broker.get_profile()
    assert profile.client_id
    assert "@" in profile.email

@pytest.mark.live
async def test_funds_are_non_negative(broker):
    fund = await broker.get_funds()
    assert fund.available >= 0
    assert fund.total >= 0

@pytest.mark.live
async def test_get_holdings(broker):
    holdings = await broker.get_holdings()
    assert isinstance(holdings, list)

@pytest.mark.live
async def test_get_positions(broker):
    positions = await broker.get_positions()
    assert isinstance(positions, list)
