import pandas as pd
import pytest

import ct_metrics
import services.ct_service as service

@pytest.fixture
def fake_reports():
    return {
        "income": pd.DataFrame({"value": [100]}),
        "balance": pd.DataFrame({"value": [200]}),
        "cashflow": pd.DataFrame({"value": [50]}),
    }


def test_normal_execution_fetches_reports_once(monkeypatch, fake_reports):
    calls = {}

    def fake_fetch(symbol):
        calls["fetch"] = calls.get("fetch", 0) + 1
        return fake_reports

    def fake_basic(symbol, reports=None):
        calls["basic_reports"] = reports
        return {"result": "basic"}

    def fake_quality(symbol, reports=None):
        calls["quality_reports"] = reports
        return {"result": "quality"}

    def fake_history(symbol, periods, reports=None):
        calls["history_reports"] = reports
        calls["history_periods"] = periods
        return pd.DataFrame({"revenue": [100]})

    def fake_trend(symbol, periods, history=None):
        calls["trend_history"] = history
        return pd.DataFrame({"growth": [0.1]})

    def fake_alerts(symbol, periods, trend=None):
        calls["alerts_trend"] = trend
        return {"alert_count": 0}

    monkeypatch.setattr(service, "fetch_stock_financial_reports", fake_fetch)
    monkeypatch.setattr(service, "analyze_company", fake_basic)
    monkeypatch.setattr(service, "validate_company_data", fake_quality)
    monkeypatch.setattr(service, "build_company_history", fake_history)
    monkeypatch.setattr(service, "analyze_company_trend", fake_trend)
    monkeypatch.setattr(service, "analyze_company_alerts", fake_alerts)

    result = service.analyze_company_service("600000", periods=20)

    assert calls["fetch"] == 1
    assert calls["basic_reports"] is fake_reports
    assert calls["quality_reports"] is fake_reports
    assert calls["history_reports"] is fake_reports
    assert calls["history_periods"] == 24
    assert result["history"] is calls["trend_history"]
    assert result["trend"] is calls["alerts_trend"]

    assert all(status == "success" for status in result["status"].values())
    assert result["errors"] == {}


def test_data_failure_skips_all_downstream_modules(monkeypatch):
    def fake_fetch(symbol):
        raise ConnectionError("Data source unavailable")

    monkeypatch.setattr(service, "fetch_stock_financial_reports", fake_fetch)

    result = service.analyze_company_service("600000")

    assert result["status"]["data"] == "failed"

    for module in ("basic", "history", "trend", "alerts", "quality"):
        assert result["status"][module] == "skipped"
        assert result[module] is None

    assert result["errors"]["data"]["type"] == "ConnectionError"


def test_basic_and_quality_failures_do_not_block_other_modules(
    monkeypatch, fake_reports
):
    monkeypatch.setattr(
        service,
        "fetch_stock_financial_reports",
        lambda symbol: fake_reports,
    )

    def fail_basic(symbol, reports=None):
        raise ValueError("Basic analysis failed")

    def fail_quality(symbol, reports=None):
        raise ValueError("Quality check failed")

    monkeypatch.setattr(service, "analyze_company", fail_basic)
    monkeypatch.setattr(service, "validate_company_data", fail_quality)
    monkeypatch.setattr(
        service,
        "build_company_history",
        lambda symbol, periods, reports=None: pd.DataFrame({"value": [1]}),
    )
    monkeypatch.setattr(
        service,
        "analyze_company_trend",
        lambda symbol, periods, history=None: pd.DataFrame({"value": [1]}),
    )
    monkeypatch.setattr(
        service,
        "analyze_company_alerts",
        lambda symbol, periods, trend=None: {"alert_count": 0},
    )

    result = service.analyze_company_service("600000")

    assert result["status"]["basic"] == "failed"
    assert result["status"]["quality"] == "failed"
    assert result["status"]["history"] == "success"
    assert result["status"]["trend"] == "success"
    assert result["status"]["alerts"] == "success"


def test_history_failure_skips_trend_and_alerts(monkeypatch, fake_reports):
    monkeypatch.setattr(
        service,
        "fetch_stock_financial_reports",
        lambda symbol: fake_reports,
    )
    monkeypatch.setattr(
        service,
        "analyze_company",
        lambda symbol, reports=None: {"result": "basic"},
    )
    monkeypatch.setattr(
        service,
        "validate_company_data",
        lambda symbol, reports=None: {"result": "quality"},
    )

    def fail_history(symbol, periods, reports=None):
        raise ValueError("History unavailable")

    def should_not_run(*args, **kwargs):
        pytest.fail("Downstream module should not run")

    monkeypatch.setattr(service, "build_company_history", fail_history)
    monkeypatch.setattr(service, "analyze_company_trend", should_not_run)
    monkeypatch.setattr(service, "analyze_company_alerts", should_not_run)

    result = service.analyze_company_service("600000")

    assert result["status"]["history"] == "failed"
    assert result["status"]["trend"] == "skipped"
    assert result["status"]["alerts"] == "skipped"


def test_trend_failure_skips_alerts(monkeypatch, fake_reports):
    monkeypatch.setattr(
        service,
        "fetch_stock_financial_reports",
        lambda symbol: fake_reports,
    )
    monkeypatch.setattr(
        service,
        "analyze_company",
        lambda symbol, reports=None: {"result": "basic"},
    )
    monkeypatch.setattr(
        service,
        "validate_company_data",
        lambda symbol, reports=None: {"result": "quality"},
    )
    monkeypatch.setattr(
        service,
        "build_company_history",
        lambda symbol, periods, reports=None: pd.DataFrame({"value": [1]}),
    )

    def fail_trend(symbol, periods, history=None):
        raise ValueError("Trend unavailable")

    def should_not_run(*args, **kwargs):
        pytest.fail("Alert module should not run")

    monkeypatch.setattr(service, "analyze_company_trend", fail_trend)
    monkeypatch.setattr(service, "analyze_company_alerts", should_not_run)

    result = service.analyze_company_service("600000")

    assert result["status"]["history"] == "success"
    assert result["status"]["trend"] == "failed"
    assert result["status"]["alerts"] == "skipped"

@pytest.mark.parametrize("periods", [0, 101, -1, 20.5, "20", None, True, False])
def test_invalid_periods_raise_value_error_without_fetching(
    monkeypatch, periods
):
    def should_not_fetch(symbol):
        pytest.fail("Invalid parameters must be rejected before data fetching")

    monkeypatch.setattr(
        service,
        "fetch_stock_financial_reports",
        should_not_fetch,
    )

    with pytest.raises(ValueError):
        service.analyze_company_service("600000", periods=periods)


@pytest.mark.parametrize("symbol", ["", "   ", None, 600000, True])
def test_invalid_symbol_raises_value_error_without_fetching(
    monkeypatch, symbol
):
    def should_not_fetch(symbol):
        pytest.fail("Invalid parameters must be rejected before data fetching")

    monkeypatch.setattr(
        service,
        "fetch_stock_financial_reports",
        should_not_fetch,
    )

    with pytest.raises(ValueError):
        service.analyze_company_service(symbol)


@pytest.mark.parametrize("periods", [1, 100])
def test_valid_period_boundaries_are_accepted(
    monkeypatch, fake_reports, periods
):
    calls = {}

    monkeypatch.setattr(
        service,
        "fetch_stock_financial_reports",
        lambda symbol: fake_reports,
    )
    monkeypatch.setattr(
        service,
        "analyze_company",
        lambda symbol, reports=None: {},
    )
    monkeypatch.setattr(
        service,
        "validate_company_data",
        lambda symbol, reports=None: {},
    )

    def fake_history(symbol, periods, reports=None):
        calls["history_periods"] = periods
        return pd.DataFrame({"value": [1]})

    monkeypatch.setattr(service, "build_company_history", fake_history)
    monkeypatch.setattr(
        service,
        "analyze_company_trend",
        lambda symbol, periods, history=None: pd.DataFrame({"value": [1]}),
    )
    monkeypatch.setattr(
        service,
        "analyze_company_alerts",
        lambda symbol, periods, trend=None: {},
    )

    result = service.analyze_company_service("600000", periods=periods)

    assert result["status"]["history"] == "success"
    assert calls["history_periods"] == min(periods + 4, 100)
import data_fetcher


def test_real_company_analysis_end_to_end(monkeypatch):
    """模拟三张财报接口，执行真实企业财务分析全链路。"""

    dates = pd.to_datetime([
        "2024-03-31",
        "2024-06-30",
        "2024-09-30",
        "2024-12-31",
        "2025-03-31",
        "2025-06-30",
        "2025-09-30",
        "2025-12-31",
    ])

    # 单季度模拟数据
    quarterly_revenue = [100, 110, 120, 130, 110, 121, 132, 143]
    quarterly_profit = [20, 22, 24, 26, 22, 21, 20, 21]
    quarterly_cashflow = [18, 19, 20, 21, 15, 14, 13, 12]

    def to_cumulative(values):
        result = []
        total = 0

        for index, value in enumerate(values):
            if index % 4 == 0:
                total = value
            else:
                total += value

            result.append(total)

        return result

    income = pd.DataFrame({
        "REPORT_DATE": dates,
        "OPERATE_INCOME": to_cumulative(quarterly_revenue),
        "PARENT_NETPROFIT": to_cumulative(quarterly_profit),
        "OPERATE_INCOME_YOY": [5, 6, 7, 8, 10, 10, 10, 10],
        "PARENT_NETPROFIT_YOY": [5, 6, 7, 8, 0, -4, -17, -19],
    })

    balance = pd.DataFrame({
        "REPORT_DATE": dates,
        "TOTAL_ASSETS": [
            500, 510, 520, 530,
            540, 550, 560, 570,
        ],
        "TOTAL_LIABILITIES": [
            200, 204, 208, 212,
            216, 231, 246, 262.2,
        ],
    })

    cashflow = pd.DataFrame({
        "REPORT_DATE": dates,
        "NETCASH_OPERATE": to_cumulative(quarterly_cashflow),
    })

    reports = {
        "income": income,
        "balance": balance,
        "cashflow": cashflow,
    }

    calls = {
        "income": 0,
        "balance": 0,
        "cashflow": 0,
    }

    def fake_income(symbol):
        calls["income"] += 1
        return income

    def fake_balance(symbol):
        calls["balance"] += 1
        return balance

    def fake_cashflow(symbol):
        calls["cashflow"] += 1
        return cashflow

    monkeypatch.setattr(
        data_fetcher,
        "fetch_stock_income_statement",
        fake_income,
    )
    monkeypatch.setattr(
        data_fetcher,
        "fetch_stock_balance_sheet",
        fake_balance,
    )
    monkeypatch.setattr(
        data_fetcher,
        "fetch_stock_cash_flow_statement",
        fake_cashflow,
    )

    result = service.analyze_company_service(
        "600000",
        periods=20,
    )

    # 三张财报接口各调用一次
    assert calls == {
        "income": 1,
        "balance": 1,
        "cashflow": 1,
    }

    # 数据获取成功，三张报表均被保留
    assert result["reports"] is not None
    assert result["reports"]["income"] is income
    assert result["reports"]["balance"] is balance
    assert result["reports"]["cashflow"] is cashflow

    # 五个真实分析模块全部执行成功
    assert result["status"] == {
        "data": "success",
        "basic": "success",
        "history": "success",
        "trend": "success",
        "alerts": "success",
        "quality": "success",
    }

    assert result["errors"] == {}

    # 基础分析正常返回
    assert isinstance(result["basic"], dict)
    assert result["basic"]

    # 数据质量检查正常完成
    assert result["quality"]["报表概况"].shape[0] == 3
    assert result["quality"]["报表获取错误"].empty
    assert result["quality"]["报告期匹配"]["共同报告期数量"] == 8

    # 历史数据、趋势数据均包含最近八个季度
    assert len(result["history"]) == 8
    assert len(result["trend"]) == 8

    # 趋势模块正确计算最新季度同比
    latest_trend = result["trend"].iloc[-1]

    assert latest_trend["营业收入单季度同比"] > 0
    assert latest_trend["归母净利润单季度同比"] < 0

    # 异常提示模块真实执行
    alerts = result["alerts"]

    assert alerts["分析状态"] == "完成"
    assert alerts["检查期数"] == 8
    assert alerts["异常数量"] == 4

    alert_types = {
        item["类型"]
        for item in alerts["异常提示"]
    }

    assert alert_types == {
        "营收与利润背离",
        "盈利能力连续下降",
        "经营现金流低于净利润",
        "资产负债率连续上升",
    }

def test_prepare_statement_excludes_all_duplicate_report_periods():
    df = pd.DataFrame({
        "REPORT_DATE": [
            "2025-03-31",
            "2025-06-30",
            "2025-06-30",
            "2025-09-30",
        ],
        "VALUE": [100, 200, 999, 300],
    })

    result = ct_metrics._prepare_statement(df)

    assert list(result.index) == list(pd.to_datetime([
        "2025-03-31",
        "2025-09-30",
    ]))