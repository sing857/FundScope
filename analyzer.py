import numpy as np
import pandas as pd


def calculate_metrics(nav, risk_free_rate=0.02):
    """计算基金历史收益、风险指标及最大回撤对应日期。"""

    # 1. 校验输入
    if not isinstance(nav, pd.Series):
        raise TypeError("净值数据必须是 pandas.Series。")

    if (
        not isinstance(risk_free_rate, (int, float))
        or isinstance(risk_free_rate, bool)
        or not np.isfinite(risk_free_rate)
        or risk_free_rate <= -1
    ):
        raise ValueError("无风险利率必须是大于 -100% 的有限数值。")

    nav = pd.to_numeric(nav, errors="coerce").dropna().astype(float)

    if len(nav) < 2:
        raise ValueError("至少需要两条有效的基金净值数据。")

    if not np.isfinite(nav.to_numpy()).all() or (nav <= 0).any():
        raise ValueError("基金净值必须是大于零的有限数值。")

    # 2. 校验日期并排序
    if not isinstance(nav.index, pd.DatetimeIndex):
        raise ValueError("净值数据必须使用日期索引。")

    if nav.index.isna().any():
        raise ValueError("日期索引包含无效日期。")

    if nav.index.has_duplicates:
        raise ValueError("净值数据存在重复日期，请先清理。")

    nav = nav.sort_index()

    days = (nav.index[-1] - nav.index[0]).total_seconds() / 86400

    if days <= 0:
        raise ValueError("净值数据的日期跨度必须大于零。")

    # 3. 区间收益率
    total_return = nav.iloc[-1] / nav.iloc[0] - 1

    # 4. 年化复合收益率
    annualized_return = (
        (nav.iloc[-1] / nav.iloc[0]) ** (365 / days) - 1
    )

    # 5. 每期收益率
    returns = nav.pct_change().dropna()

    # 6. 年化波动率和夏普比率
    # 假设净值为日频，使用 252 个交易日年化
    if len(returns) >= 2:
        period_volatility = returns.std(ddof=1)
        annualized_volatility = period_volatility * np.sqrt(252)

        daily_risk_free_rate = (1 + risk_free_rate) ** (1 / 252) - 1
        excess_returns = returns - daily_risk_free_rate

        if (
            np.isfinite(period_volatility)
            and period_volatility > 0
            and np.isfinite(excess_returns.mean())
        ):
            sharpe_ratio = (
                excess_returns.mean() / period_volatility
            ) * np.sqrt(252)
        else:
            sharpe_ratio = np.nan
    else:
        annualized_volatility = np.nan
        sharpe_ratio = np.nan

    # 7. 最大回撤及对应日期
    running_max = nav.cummax()
    drawdowns = nav / running_max - 1

    trough_date = drawdowns.idxmin()
    max_drawdown = float(drawdowns.loc[trough_date])

    # 找到谷底之前的历史最高净值
    nav_until_trough = nav.loc[:trough_date]
    peak_nav = nav_until_trough.max()

    # 如果峰值重复出现，取最后一次
    peak_date = nav_until_trough[
        nav_until_trough == peak_nav
    ].index[-1]

    drawdown_duration_days = (trough_date - peak_date).days

    # 8. 返回结果
    results = {
        "区间收益率": total_return,
        "年化收益率": annualized_return,
        "年化波动率": annualized_volatility,
        "最大回撤": max_drawdown,
        "夏普比率": sharpe_ratio,
        "回撤峰值日期": peak_date.strftime("%Y-%m-%d"),
        "回撤谷底日期": trough_date.strftime("%Y-%m-%d"),
        "峰值至谷底天数": int(drawdown_duration_days),
    }

    return {
        name: (
            float(value)
            if isinstance(value, (int, float, np.integer, np.floating))
            and np.isfinite(value)
            else value
        )
        for name, value in results.items()
    }