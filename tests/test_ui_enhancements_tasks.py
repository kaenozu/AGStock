import datetime
import pytest

from src.ui.ui_enhancements import (
    AlertState,
    AlertStateMachine,
    AuditLogView,
    ColorTokens,
    HeatmapDataBuilder,
    MetricTooltipCatalog,
    OnboardingTour,
    OrderHistoryQuery,
    PerformanceFilter,
    RetryPolicy,
    ShortcutManager,
)


def test_color_tokens_validation_and_resolution():
    tokens = ColorTokens.default()
    tokens.add_state("pending", "info", "#3366ff")
    assert tokens.validate_required({"success", "warning", "error", "info", "pending"})
    assert tokens.resolve_color("success") == "#0FA3B1"
    assert tokens.resolve_color("pending") == "#3366ff"

    with pytest.raises(KeyError):
        tokens.resolve_color("unknown")


def test_performance_filter_periods_and_missing_values():
    series = [
        PerformanceFilter.Point(date=datetime.date(2023, 12, 15), value=1.0),
        PerformanceFilter.Point(date=datetime.date(2023, 12, 31), value=None),
        PerformanceFilter.Point(date=datetime.date(2024, 1, 2), value=1.2),
        PerformanceFilter.Point(date=datetime.date(2024, 1, 9), value=1.3),
    ]
    now = datetime.date(2024, 1, 10)

    filtered_1w = PerformanceFilter.filter_points(series, "1W", now=now)
    assert [p.date for p in filtered_1w] == [datetime.date(2024, 1, 2), datetime.date(2024, 1, 9)]

    filtered_ytd = PerformanceFilter.filter_points(series, "YTD", now=now)
    assert [p.date for p in filtered_ytd] == [datetime.date(2024, 1, 2), datetime.date(2024, 1, 9)]

    filtered_custom = PerformanceFilter.filter_points(
        series,
        "custom",
        now=now,
        custom_range=(datetime.date(2023, 12, 1), datetime.date(2023, 12, 20)),
    )
    assert [p.date for p in filtered_custom] == [datetime.date(2023, 12, 15)]



def test_heatmap_builder_normalization_and_legend():
    builder = HeatmapDataBuilder()
    entries = [
        {"sector": "Tech", "weight": 60, "performance": 0.08},
        {"sector": "Finance", "weight": 40, "performance": -0.04},
    ]
    result = builder.build(entries)
    assert pytest.approx(sum(item["normalized_weight"] for item in result)) == 1.0
    legends = {item["legend"] for item in result}
    assert legends == {"outperform", "neutral"}



def test_order_history_query_filters_and_pagination():
    orders = [
        {"ticker": "AAA", "status": "filled", "timestamp": 3},
        {"ticker": "AAA", "status": "open", "timestamp": 2},
        {"ticker": "BBB", "status": "filled", "timestamp": 1},
    ]
    query = OrderHistoryQuery()
    filtered = query.apply_filters(
        orders,
        filters={"ticker": "AAA", "status": {"filled", "open"}},
    )
    assert [o["timestamp"] for o in filtered] == [3, 2]

    paginated = query.paginate(filtered, page=1, page_size=1)
    assert paginated["items"][0]["timestamp"] == 3
    assert paginated["offset"] == 0



def test_alert_state_machine_transitions_and_guards():
    machine = AlertStateMachine()
    assert machine.transition(AlertState.CREATED, "trigger") == AlertState.TRIGGERED
    assert machine.transition(AlertState.TRIGGERED, "snooze") == AlertState.SNOOZED
    assert machine.transition(AlertState.SNOOZED, "resolve") == AlertState.RESOLVED

    with pytest.raises(ValueError):
        machine.transition(AlertState.RESOLVED, "trigger")



def test_retry_policy_backoff_and_limits():
    policy = RetryPolicy(max_attempts=4, base_delay=1, max_delay=5)
    schedule = policy.backoff_schedule()
    assert schedule == [1, 2, 4, 5]
    assert policy.should_retry(3)
    assert not policy.should_retry(4)



def test_shortcut_manager_validation_and_focus_order():
    manager = ShortcutManager(
        shortcuts={"search": "cmd+k", "tab_next": "ctrl+arrow"},
        focus_order=["search", "filters", "table"],
    )
    manager.validate()
    assert manager.next_focus("search") == "filters"
    assert manager.next_focus("table") == "search"

    manager.shortcuts["duplicate"] = "cmd+k"
    with pytest.raises(ValueError):
        manager.validate()



def test_onboarding_tour_skip_and_resume():
    tour = OnboardingTour(["add_ticker", "set_alert", "change_period"])
    assert tour.current_step == "add_ticker"
    tour.advance()
    tour.skip()
    assert tour.current_step == "change_period"
    tour.resume()
    assert tour.current_step == "set_alert"



def test_audit_log_view_filter_and_sort_stability():
    entries = [
        {"timestamp": datetime.datetime(2024, 1, 2, 10), "model": "v1", "signal": "buy", "id": 2},
        {"timestamp": datetime.datetime(2024, 1, 2, 9), "model": "v1", "signal": "sell", "id": 1},
        {"timestamp": datetime.datetime(2024, 1, 2, 9), "model": "v2", "signal": "buy", "id": 3},
    ]
    view = AuditLogView(entries)
    filtered = view.filter(signal="buy")
    sorted_entries = view.sort(filtered)
    assert [e["id"] for e in sorted_entries] == [3, 2]



def test_metric_tooltip_catalog_consistency_and_updates():
    catalog = MetricTooltipCatalog.default()
    catalog.validate()
    tooltip = catalog.get("sharpe")
    assert "リターン" in tooltip

    catalog.update("custom", formula="x/y", period="1M", precision=2)
    assert catalog.get("custom").endswith("精度: 2桁")

