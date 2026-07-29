from datetime import UTC, datetime, timedelta

from app.pipeline.ingestion.connectors import gdelt


def test_window_is_omitted_when_no_dates_are_given():
    """No window means the API returns its own most-recent slice, the old behaviour."""
    assert gdelt._window(None, None) == {}


def test_window_is_clamped_to_the_three_month_limit():
    """STARTDATETIME outside the served window returns nothing, so clamp rather than ask."""
    now = datetime.now(UTC)

    params = gdelt._window(now - timedelta(days=400), now)
    start = datetime.strptime(params["startdatetime"], "%Y%m%d%H%M%S").replace(tzinfo=UTC)

    assert (now - start).days <= gdelt.MAX_LOOKBACK_DAYS


def test_window_is_left_alone_when_already_inside_the_limit():
    now = datetime.now(UTC)
    start = now - timedelta(days=10)

    params = gdelt._window(start, now)

    assert params["startdatetime"] == start.strftime("%Y%m%d%H%M%S")


def test_inverted_window_produces_no_parameters():
    """A cursor past the frontier must not ask for a backwards range."""
    now = datetime.now(UTC)

    assert gdelt._window(now, now - timedelta(hours=1)) == {}


def test_sweep_stays_behind_the_indexing_frontier():
    """GDELT indexes with a lag; sweeping to 'now' would permanently miss late arrivals."""
    assert gdelt.INDEX_LAG_MINUTES > 0
    assert gdelt.SWEEP_WINDOW_MINUTES < gdelt.INDEX_LAG_MINUTES


def test_sweep_respects_the_documented_rate_limit():
    assert gdelt.RATE_LIMIT_SECONDS >= 5.0
