import numpy as np
import pandas as pd


def calculate_metrics(nav, risk_free_rate=0.02):
    """计算基金历史收益与风险指标。

    参数:
        nav: pandas.Series，基金单位净值，最好以日期为索引。
        risk_free_rate: 年化无风险利率，默认 2%。

    返回:
        包含区间收益率、年化收益率、年化波动率、
        最大回撤和夏普比率的字典。
    """

    # 1. 清洗净值数据
    nav = pd.to_numeric(nav, errors="coerce").dropna()

    if len(nav) < 2:
        raise ValueError("至少需要两条有效的基金净值数据")

    if (nav <= 0).any():
        raise ValueError("基金净值必须大于零")

    if not np.isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("无风险利率必须是大于 -100% 的有效数值")

    # 2. 如果索引是日期，按日期升序排列
    if isinstance(nav.index, pd.DatetimeIndex):
        nav = nav.sort_index()

        if nav.index.has_duplicates:
            raise ValueError("净值数据存在重复日期，请先清理")

        days = (nav.index[-1] - nav.index[0]).days
    else:
        days = len(nav) - 1

    # 3. 区间累计收益率
    total_return = nav.iloc[-1] / nav.iloc[0] - 1

    # 4. 年化复合收益率
    if days > 0:
        annualized_return = (
            (nav.iloc[-1] / nav.iloc[0]) ** (365 / days) - 1
        )
    else:
        annualized_return = np.nan

    # 5. 每期收益率
    returns = nav.pct_change().dropna()

    # 6. 年化波动率：假设数据为日频，按 252 个交易日年化
    daily_volatility = returns.std(ddof=1)
    annualized_volatility = daily_volatility * np.sqrt(252)

    # 7. 最大回撤
    running_max = nav.cummax()
    drawdowns = nav / running_max - 1
    max_drawdown = drawdowns.min()

    # 8. 夏普比率：每日收益率与每日无风险收益率比较
    daily_risk_free_rate = (1 + risk_free_rate) ** (1 / 252) - 1
    excess_returns = returns - daily_risk_free_rate
    excess_volatility = returns.std(ddof=1)

    if (
        len(excess_returns) >= 2
        and excess_volatility > 0
        and np.isfinite(excess_volatility)
    ):
        sharpe_ratio = (
            excess_returns.mean() / excess_volatility
        ) * np.sqrt(252)
    else:
        sharpe_ratio = np.nan

    return {
        "区间收益率": float(total_return),
        "年化收益率": float(annualized_return),
        "年化波动率": float(annualized_volatility),
        "最大回撤": float(max_drawdown),
        "夏普比率": float(sharpe_ratio),
    }
