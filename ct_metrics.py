import pandas as pd

from data_fetcher import (
    fetch_stock_income_statement,
    fetch_stock_balance_sheet,
    fetch_stock_cash_flow_statement,
)


def _to_number(value):
    """将数据安全转换为浮点数；空值或非数字返回 None。"""
    value = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(value) else float(value)


def _safe_ratio(numerator, denominator):
    """安全计算比率，避免空值或除以零。"""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _prepare_statement(df):
    """清洗财报日期，确保每个报告期只有一条记录。"""
    if df is None or df.empty:
        raise ValueError("获取到的财报为空。")

    if "REPORT_DATE" not in df.columns:
        raise ValueError("财报缺少 REPORT_DATE 字段。")

    df = df.copy()
    df["REPORT_DATE"] = pd.to_datetime(
        df["REPORT_DATE"], errors="coerce"
    )
    df = df.dropna(subset=["REPORT_DATE"])
    df = df.drop_duplicates(
        subset=["REPORT_DATE"], keep="first"
    )
    return df.set_index("REPORT_DATE").sort_index()


def _single_quarter_value(df, date, column):
    """将年内累计值还原为单季度值。"""
    if date not in df.index or column not in df.columns:
        return None

    current = _to_number(df.at[date, column])
    if current is None:
        return None

    if date.month == 3:
        return current

    if date.month not in (6, 9, 12):
        return None

    previous_date = date - pd.offsets.QuarterEnd(1)

    if previous_date not in df.index:
        return None

    previous = _to_number(df.at[previous_date, column])
    if previous is None:
        return None

    return current - previous


def build_company_history(symbol, periods=20):
    """构建公司历史财务指标，不生成综合评分。"""

    if (
        not isinstance(periods, int)
        or isinstance(periods, bool)
        or not 1 <= periods <= 100
    ):
        raise ValueError("periods 必须是 1 到 100 之间的整数。")

    income = _prepare_statement(
        fetch_stock_income_statement(symbol)
    )
    balance = _prepare_statement(
        fetch_stock_balance_sheet(symbol)
    )
    cashflow = _prepare_statement(
        fetch_stock_cash_flow_statement(symbol)
    )

    common_dates = sorted(
        set(income.index)
        & set(balance.index)
        & set(cashflow.index)
    )

    if not common_dates:
        raise ValueError("三张财报没有共同的报告期。")

    rows = []

    for date in common_dates:
        inc = income.loc[date]
        bal = balance.loc[date]
        cash = cashflow.loc[date]

        revenue = _to_number(inc.get("OPERATE_INCOME"))
        profit = _to_number(inc.get("PARENT_NETPROFIT"))
        operating_cash = _to_number(cash.get("NETCASH_OPERATE"))

        quarter_revenue = _single_quarter_value(
            income, date, "OPERATE_INCOME"
        )
        quarter_profit = _single_quarter_value(
            income, date, "PARENT_NETPROFIT"
        )
        quarter_operating_cash = _single_quarter_value(
            cashflow, date, "NETCASH_OPERATE"
        )

        assets = _to_number(bal.get("TOTAL_ASSETS"))
        liabilities = _to_number(bal.get("TOTAL_LIABILITIES"))

        cumulative_net_margin = _safe_ratio(profit, revenue)
        cumulative_cash_profit_ratio = _safe_ratio(
            operating_cash, profit
        )

        quarterly_net_margin = _safe_ratio(
            quarter_profit, quarter_revenue
        )
        quarterly_cash_profit_ratio = _safe_ratio(
            quarter_operating_cash, quarter_profit
        )

        rows.append({
            "报告期": date,
            "营业收入（累计，元）": revenue,
            "归母净利润（累计，元）": profit,
            "经营现金流（累计，元）": operating_cash,
            "营业收入（单季度，元）": quarter_revenue,
            "归母净利润（单季度，元）": quarter_profit,
            "经营现金流（单季度，元）": quarter_operating_cash,
            "总资产（期末，元）": assets,
            "总负债（期末，元）": liabilities,
            "营业收入同比（%）": _to_number(
                inc.get("OPERATE_INCOME_YOY")
            ),
            "归母净利润同比（%）": _to_number(
                inc.get("PARENT_NETPROFIT_YOY")
            ),
            "累计净利率": cumulative_net_margin,
            "单季度净利率": quarterly_net_margin,
            "累计经营现金流／归母净利润": (
                cumulative_cash_profit_ratio
            ),
            "单季度经营现金流／归母净利润": (
                quarterly_cash_profit_ratio
            ),
            "资产负债率": _safe_ratio(liabilities, assets),

            # 兼容原有调用代码，保留旧字段。
            "净利率": cumulative_net_margin,
            "经营现金流／归母净利润": cumulative_cash_profit_ratio,
        })

    result = pd.DataFrame(rows)
    result = result.sort_values("报告期").reset_index(drop=True)

    return result.tail(periods).reset_index(drop=True)
