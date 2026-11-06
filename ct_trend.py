import pandas as pd

from ct_metrics import build_company_history


def _safe_growth(current, previous):
    """计算同比增长率。"""
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None

    return current / previous - 1


def _safe_change(current, previous):
    """计算指标变化值。"""
    if pd.isna(current) or pd.isna(previous):
        return None

    return current - previous


def analyze_company_trend(symbol, periods=20, history=None):
    """
    企业财务趋势分析。

    分析内容：
    1. 营业收入同比增长
    2. 归母净利润同比增长
    3. 单季度净利率变化
    4. 单季度经营现金流与净利润比例
    5. 资产负债率变化

    注意：本模块不生成综合评分。
    """

    if (
        not isinstance(periods, int)
        or isinstance(periods, bool)
        or not 1 <= periods <= 100
    ):
        raise ValueError("periods 必须是 1 到 100 之间的整数。")

    # 多取四个季度，为同比计算保留历史数据。
    if history is None:
        history = build_company_history(
            symbol,
            periods=min(periods + 4, 100)
        )
    elif not isinstance(history, pd.DataFrame):
        raise ValueError("history must be a pandas DataFrame.")

    if history.empty:
        raise ValueError("没有可用的企业历史财务数据。")

    df = history.copy()
    df["报告期"] = pd.to_datetime(df["报告期"])
    df = df.sort_values("报告期").reset_index(drop=True)

    # 建立报告期索引，按去年同一报告期匹配。
    date_lookup = {
        date: index
        for index, date in enumerate(df["报告期"])
    }

    revenue_growth = []
    profit_growth = []
    margin_change = []
    cash_ratio_change = []
    debt_ratio_change = []

    for _, row in df.iterrows():
        date = row["报告期"]
        previous_date = date - pd.DateOffset(years=1)

        previous_index = date_lookup.get(previous_date)

        if previous_index is None:
            revenue_growth.append(None)
            profit_growth.append(None)
            margin_change.append(None)
            cash_ratio_change.append(None)
            debt_ratio_change.append(None)
            continue

        previous = df.iloc[previous_index]

        revenue_growth.append(
            _safe_growth(
                row["营业收入（单季度，元）"],
                previous["营业收入（单季度，元）"]
            )
        )

        profit_growth.append(
            _safe_growth(
                row["归母净利润（单季度，元）"],
                previous["归母净利润（单季度，元）"]
            )
        )

        margin_change.append(
            _safe_change(
                row["单季度净利率"],
                previous["单季度净利率"]
            )
        )

        cash_ratio_change.append(
            _safe_change(
                row["单季度经营现金流／归母净利润"],
                previous["单季度经营现金流／归母净利润"]
            )
        )

        debt_ratio_change.append(
            _safe_change(
                row["资产负债率"],
                previous["资产负债率"]
            )
        )

    df["营业收入单季度同比"] = revenue_growth
    df["归母净利润单季度同比"] = profit_growth
    df["净利率同比变化"] = margin_change
    df["现金流利润比同比变化"] = cash_ratio_change
    df["资产负债率同比变化"] = debt_ratio_change

    # 保留最近指定期数。
    return df.tail(periods).reset_index(drop=True)
