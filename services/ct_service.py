from data_fetcher import fetch_stock_financial_reports
from ct_analyzer import analyze_company
from ct_metrics import build_company_history
from ct_trend import analyze_company_trend
from ct_alerts import analyze_company_alerts
from ct_quality import validate_company_data


def analyze_company_service(symbol, periods=20):
    """
    统一调度企业财务分析模块。

    各分析模块独立记录执行状态。
    财报只获取一次，并在各模块之间共享。
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be a non-empty string.")

    if isinstance(periods, bool) or not isinstance(periods, int):
        raise ValueError("periods must be an integer between 1 and 100.")

    if not 1 <= periods <= 100:
        raise ValueError("periods must be between 1 and 100.")

    symbol = symbol.strip()

    result = {
        "symbol": symbol,
        "reports": None,
        "basic": None,
        "history": None,
        "trend": None,
        "alerts": None,
        "quality": None,
        "status": {
            "data": "pending",
            "basic": "pending",
            "history": "pending",
            "trend": "pending",
            "alerts": "pending",
            "quality": "pending",
        },
        "errors": {},
    }

    def record_error(module, exc):
        result["status"][module] = "failed"
        result["errors"][module] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    def skip_module(module, reason):
        result["status"][module] = "skipped"
        result["errors"][module] = {
            "reason": reason,
        }

    # 1. 获取三张财务报表
    try:
        reports = fetch_stock_financial_reports(symbol)

        required_reports = {"income", "balance", "cashflow"}
        if (
            not isinstance(reports, dict)
            or not required_reports.issubset(reports)
        ):
            raise ValueError(
                "Financial reports must contain income, balance and cashflow."
            )

        result["reports"] = reports
        result["status"]["data"] = "success"

    except Exception as exc:
        record_error("data", exc)

        for module in (
            "basic",
            "history",
            "trend",
            "alerts",
            "quality",
        ):
            skip_module(module, "Financial report retrieval failed.")

        return result

    # 2. 基础财务分析
    try:
        result["basic"] = analyze_company(
            symbol,
            reports=reports,
        )
        result["status"]["basic"] = "success"
    except Exception as exc:
        record_error("basic", exc)

    # 3. 数据质量检查
    try:
        result["quality"] = validate_company_data(
            symbol,
            reports=reports,
        )
        result["status"]["quality"] = "success"
    except Exception as exc:
        record_error("quality", exc)

    # 4. 历史财务指标
    try:
        result["history"] = build_company_history(
            symbol,
            periods=min(periods + 4, 100),
            reports=reports,
        )
        result["status"]["history"] = "success"
    except Exception as exc:
        record_error("history", exc)

    # 5. 趋势分析：依赖历史指标
    if result["status"]["history"] == "success":
        try:
            result["trend"] = analyze_company_trend(
                symbol,
                periods=periods,
                history=result["history"],
            )
            result["status"]["trend"] = "success"
        except Exception as exc:
            record_error("trend", exc)
    else:
        skip_module("trend", "Historical financial indicators are unavailable.")

    # 6. 异常提示：依赖趋势分析
    if result["status"]["trend"] == "success":
        try:
            result["alerts"] = analyze_company_alerts(
                symbol,
                periods=periods,
                trend=result["trend"],
            )
            result["status"]["alerts"] = "success"
        except Exception as exc:
            record_error("alerts", exc)
    else:
        skip_module("alerts", "Financial trend analysis is unavailable.")

    return result
