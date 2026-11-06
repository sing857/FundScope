import pandas as pd

from data_fetcher import (
    fetch_stock_income_statement,
    fetch_stock_balance_sheet,
    fetch_stock_cash_flow_statement,
)


def validate_company_history(symbol, periods=20):
    """
    验证上市公司三张财报的历史覆盖、报告期匹配和关键字段完整性。
    不计算评分，不对企业作投资判断。
    """
    if not isinstance(periods, int) or not 1 <= periods <= 100:
        raise ValueError("periods 必须是 1 到 100 之间的整数。")

    statements = {
        "利润表": fetch_stock_income_statement(symbol),
        "资产负债表": fetch_stock_balance_sheet(symbol),
        "现金流量表": fetch_stock_cash_flow_statement(symbol),
    }

    key_fields = {
        "利润表": [
            "OPERATE_INCOME",
            "PARENT_NETPROFIT",
            "OPERATE_INCOME_YOY",
            "PARENT_NETPROFIT_YOY",
        ],
        "资产负债表": [
            "TOTAL_ASSETS",
            "TOTAL_LIABILITIES",
        ],
        "现金流量表": [
            "NETCASH_OPERATE",
        ],
    }

    result = {
        "股票代码": str(symbol),
        "检查期数": periods,
        "报表检查": {},
    }

    period_sets = {}

    for name, df in statements.items():
        if "REPORT_DATE" not in df.columns:
            raise ValueError(f"{name}缺少 REPORT_DATE 字段。")

        data = df.copy()
        data["REPORT_DATE"] = pd.to_datetime(
            data["REPORT_DATE"], errors="coerce"
        )
        data = data.dropna(subset=["REPORT_DATE"])
        data = data.sort_values("REPORT_DATE", ascending=False)
        data = data.drop_duplicates(subset=["REPORT_DATE"])

        checked = data.head(periods)
        period_sets[name] = set(checked["REPORT_DATE"])

        missing_columns = [
            field for field in key_fields[name]
            if field not in checked.columns
        ]

        missing_values = {}
        for field in key_fields[name]:
            if field in checked.columns:
                values = pd.to_numeric(checked[field], errors="coerce")
                missing_values[field] = int(values.isna().sum())

        result["报表检查"][name] = {
            "可用报告期总数": int(len(data)),
            "本次检查记录数": int(len(checked)),
            "最早报告期": (
                checked["REPORT_DATE"].min().strftime("%Y-%m-%d")
                if not checked.empty else None
            ),
            "最新报告期": (
                checked["REPORT_DATE"].max().strftime("%Y-%m-%d")
                if not checked.empty else None
            ),
            "缺少的关键字段": missing_columns,
            "关键字段缺失数量": missing_values,
        }

    common_periods = set.intersection(*period_sets.values())

    result["报告期匹配"] = {
        "三张报表共同报告期数量": len(common_periods),
        "共同报告期": [
            date.strftime("%Y-%m-%d")
            for date in sorted(common_periods, reverse=True)
        ],
    }

    return result