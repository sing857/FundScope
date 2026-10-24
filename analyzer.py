import numpy as np
import pandas as pd


def calculate_metrics(nav, risk_free_rate=0.02):
    # 检查并清理净值数据
    nav = pd.to_numeric(nav, errors="coerce").dropna()

    if len(nav) < 2:
        raise ValueError("至少需要两条有效的基金净值数据")

    if (nav <= 0).any():
        raise ValueError("基金净值必须大于零")

    # 计算每日收益率
    returns = nav.pct_change().dropna()

    # 计算区间累计收益率
    total_return = nav.iloc[-1] / nav.iloc[0] - 1

    # 计算年化收益率
    if isinstance(nav.index, pd.DatetimeIndex):
        days = (nav.index[-1] - nav.index[0]).days
    else:
        days = len(nav) - 1

    if days > 0:
        annualized_return = (
            (nav.iloc[-1] / nav.iloc[0]) ** (365 / days) - 1
        )
    else:
        annualized_return = np.nan

    # 计算年化波动率
    annualized_volatility = returns.std(ddof=1) * np.sqrt(252)

    # 计算最大回撤
    running_max = nav.cummax()
    drawdowns = nav / running_max - 1
    max_drawdown = drawdowns.min()

    # 计算夏普比率
    if annualized_volatility > 0 and np.isfinite(annualized_volatility):
        sharpe_ratio = (
            annualized_return - risk_free_rate
        ) / annualized_volatility
    else:
        sharpe_ratio = np.nan

    # 返回结果
    return {
        "区间收益率": float(total_return),
        "年化收益率": float(annualized_return),
        "年化波动率": float(annualized_volatility),
        "最大回撤": float(max_drawdown),
        "夏普比率": float(sharpe_ratio),
    }