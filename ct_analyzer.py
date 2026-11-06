import pandas as pd

from data_fetcher import (
    fetch_stock_income_statement,
    fetch_stock_balance_sheet,
    fetch_stock_cash_flow_statement,
    fetch_stock_financial_reports,
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


def analyze_company(symbol, reports=None):
    """生成上市公司基础财务指标，不生成综合评分。"""

    if reports is None:
        reports = fetch_stock_financial_reports(symbol)

    required_reports = {"income", "balance", "cashflow"}
    if not isinstance(reports, dict) or not required_reports.issubset(reports):
        raise ValueError("reports must contain income, balance and cashflow.")

    income = reports["income"]
    balance = reports["balance"]
    cashflow = reports["cashflow"]

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

    # 利润表指标
    revenue = _number(inc.get("OPERATE_INCOME"))
    parent_profit = _number(inc.get("PARENT_NETPROFIT"))
    revenue_yoy = _number(inc.get("OPERATE_INCOME_YOY"))
    profit_yoy = _number(inc.get("PARENT_NETPROFIT_YOY"))

    # 资产负债表指标
    total_assets = _number(bal.get("TOTAL_ASSETS"))
    total_liabilities = _number(bal.get("TOTAL_LIABILITIES"))

    current_assets = _number(bal.get("TOTAL_CURRENT_ASSETS"))
    current_liabilities = _number(bal.get("TOTAL_CURRENT_LIAB"))

    noncurrent_assets = _number(bal.get("TOTAL_NONCURRENT_ASSETS"))
    noncurrent_liabilities = _number(bal.get("TOTAL_NONCURRENT_LIAB"))

    monetary_funds = _number(bal.get("MONETARYFUNDS"))
    inventory = _number(bal.get("INVENTORY"))
    prepayment = _number(bal.get("PREPAYMENT"))

    # 现金流量表指标
    operating_cashflow = _number(cash.get("NETCASH_OPERATE"))

    # 偿债能力指标
    quick_assets = None
    if (
        current_assets is not None
        and inventory is not None
        and prepayment is not None
    ):
        quick_assets = current_assets - inventory - prepayment

    current_ratio = _ratio(current_assets, current_liabilities)
    quick_ratio = _ratio(quick_assets, current_liabilities)
    cash_ratio = _ratio(monetary_funds, current_liabilities)

    # 财务结构指标
    current_assets_ratio = _ratio(current_assets, total_assets)
    noncurrent_assets_ratio = _ratio(noncurrent_assets, total_assets)

    current_liabilities_ratio = _ratio(
        current_liabilities, total_liabilities
    )
    noncurrent_liabilities_ratio = _ratio(
        noncurrent_liabilities, total_liabilities
    )

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

            "流动资产（元，期末）": current_assets,
            "流动负债（元，期末）": current_liabilities,
            "流动比率": current_ratio,

            "速动资产（元，期末）": quick_assets,
            "速动比率": quick_ratio,
            "速动比率计算说明": "（流动资产－存货－预付款项）÷流动负债。",

            "货币资金（元，期末）": monetary_funds,
            "现金比率": cash_ratio,
            "现金比率说明": "以资产负债表货币资金计算，货币资金可能包含受限资金。",

            "存货（元，期末）": inventory,
            "预付款项（元，期末）": prepayment,

            "非流动资产（元，期末）": noncurrent_assets,
            "非流动负债（元，期末）": noncurrent_liabilities,

            "流动资产占总资产比例": current_assets_ratio,
            "非流动资产占总资产比例": noncurrent_assets_ratio,

            "流动负债占总负债比例": current_liabilities_ratio,
            "非流动负债占总负债比例": noncurrent_liabilities_ratio,
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
                    "流动资产": current_assets,
                    "流动负债": current_liabilities,
                    "非流动资产": noncurrent_assets,
                    "非流动负债": noncurrent_liabilities,
                    "货币资金": monetary_funds,
                    "存货": inventory,
                    "预付款项": prepayment,
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