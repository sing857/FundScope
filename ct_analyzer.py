import pandas as pd

from data_fetcher import (
    fetch_stock_income_statement,
    fetch_stock_balance_sheet,
    fetch_stock_cash_flow_statement,
)


def _number(value):
    """将财报数值转换为 float；缺失或无效时返回 None。"""
    value = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(value) else float(value)


def _ratio(numerator, denominator):
    """安全计算比率。"""
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def analyze_company(symbol):
    """生成上市公司基础财务指标，不生成综合评分。"""

    income = fetch_stock_income_statement(symbol)
    balance = fetch_stock_balance_sheet(symbol)
    cashflow = fetch_stock_cash_flow_statement(symbol)

    report_date = income.iloc[0]["REPORT_DATE"]

    def get_period_row(df):
        matched = df[df["REPORT_DATE"] == report_date]
        return matched.iloc[0] if not matched.empty else None

    inc = get_period_row(income)
    bal = get_period_row(balance)
    cash = get_period_row(cashflow)

    if inc is None or bal is None or cash is None:
        raise ValueError(
            f"报告期 {report_date.date()} 的三张财报不完整，无法进行分析。"
        )

    revenue = _number(inc.get("OPERATE_INCOME"))
    parent_profit = _number(inc.get("PARENT_NETPROFIT"))
    revenue_yoy = _number(inc.get("OPERATE_INCOME_YOY"))
    profit_yoy = _number(inc.get("PARENT_NETPROFIT_YOY"))

    total_assets = _number(bal.get("TOTAL_ASSETS"))
    total_liabilities = _number(bal.get("TOTAL_LIABILITIES"))

    operating_cashflow = _number(cash.get("NETCASH_OPERATE"))

    result = {
        "股票代码": str(symbol),
        "报告期": report_date.strftime("%Y-%m-%d"),
        "数据口径说明": "利润表和现金流量表为报告期累计值；资产负债表为期末值。",
        "盈利能力": {
            "营业收入（元，累计）": revenue,
            "归母净利润（元，累计）": parent_profit,
            "净利率": _ratio(parent_profit, revenue),
        },
        "现金流质量": {
            "经营活动现金流量净额（元，累计）": operating_cashflow,
            "经营现金流／归母净利润": _ratio(
                operating_cashflow, parent_profit
            ),
        },
        "财务安全": {
            "总资产（元，期末）": total_assets,
            "总负债（元，期末）": total_liabilities,
            "资产负债率": _ratio(total_liabilities, total_assets),
        },
        "成长性": {
            "营业收入同比增长率（%）": revenue_yoy,
            "归母净利润同比增长率（%）": profit_yoy,
        },
        "资本效率": {
            "总资产周转率": None,
            "说明": "待确认平均资产与累计收入的匹配口径后计算。",
        },
        "数据质量": {
            "利润表字段缺失": [
                name
                for name, value in {
                    "营业收入": revenue,
                    "归母净利润": parent_profit,
                    "营业收入同比": revenue_yoy,
                    "归母净利润同比": profit_yoy,
                }.items()
                if value is None
            ],
            "资产负债表字段缺失": [
                name
                for name, value in {
                    "总资产": total_assets,
                    "总负债": total_liabilities,
                }.items()
                if value is None
            ],
            "现金流量表字段缺失": (
                ["经营活动现金流量净额"]
                if operating_cashflow is None
                else []
            ),
        },
    }

    return result