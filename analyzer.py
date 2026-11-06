import numpy as np
import pandas as pd


def calculate_metrics(nav, risk_free_rate=0.02):
    """计算基金收益、风险指标、最大回撤及数据质量信息。"""

    # 1. 输入校验
    if not isinstance(nav, pd.Series):
        raise TypeError("净值数据必须是 pandas.Series。")

    if (
        not isinstance(risk_free_rate, (int, float, np.integer, np.floating))
        or isinstance(risk_free_rate, (bool, np.bool_))
        or not np.isfinite(risk_free_rate)
        or risk_free_rate <= -1
    ):
        raise ValueError("无风险利率必须是大于 -100% 的有限数值。")

    if not isinstance(nav.index, pd.DatetimeIndex):
        raise ValueError("净值数据必须使用日期索引。")

    if nav.index.isna().any():
        raise ValueError("日期索引包含无效日期。")

    if nav.index.has_duplicates:
        raise ValueError("净值数据存在重复日期，请先清理。")

    if nav.index.tz is not None:
        raise ValueError("日期索引不能包含时区，请先统一为无时区日期。")

    # 2. 数据清理与质量统计
    original_count = len(nav)
    numeric_nav = pd.to_numeric(nav, errors="coerce")

    valid_mask = numeric_nav.notna() & np.isfinite(
        numeric_nav.to_numpy(dtype=float, na_value=np.nan)
    )

    invalid_count = int((~valid_mask).sum())
    nav = numeric_nav.loc[valid_mask].astype(float)

    if len(nav) < 2:
        raise ValueError("至少需要两条有效的基金净值数据。")

    if (nav <= 0).any():
        raise ValueError("基金净值必须全部大于零。")

    nav = nav.sort_index()

    # 3. 时间跨度
    days = (nav.index[-1] - nav.index[0]).total_seconds() / 86400

    if days <= 0:
        raise ValueError("净值数据的日期跨度必须大于零。")

    # 4. 区间收益率与年化收益率
    total_return = nav.iloc[-1] / nav.iloc[0] - 1

    annualized_return = (
        (nav.iloc[-1] / nav.iloc[0]) ** (365.25 / days) - 1
    )

    if not np.isfinite(annualized_return):
        annualized_return = np.nan

    # 5. 每期收益率
    returns = nav.pct_change(fill_method=None).dropna()

    # 当前版本按照日频净值处理
    annualization_factor = 252

    # 6. 波动率、夏普比率、下行波动率与索提诺比率
    if len(returns) >= 2:
        period_volatility = returns.std(ddof=1)
        annualized_volatility = (
            period_volatility * np.sqrt(annualization_factor)
        )

        daily_risk_free_rate = (
            (1 + risk_free_rate) ** (1 / annualization_factor) - 1
        )

        excess_returns = returns - daily_risk_free_rate

        if np.isfinite(period_volatility) and period_volatility > 0:
            sharpe_ratio = (
                excess_returns.mean()
                / period_volatility
                * np.sqrt(annualization_factor)
            )
        else:
            sharpe_ratio = np.nan

        downside_returns = np.minimum(
            returns.to_numpy() - daily_risk_free_rate, 0
        )

        downside_deviation = np.sqrt(np.mean(downside_returns ** 2))
        annualized_downside_volatility = (
            downside_deviation * np.sqrt(annualization_factor)
        )

        if downside_deviation > 0:
            sortino_ratio = (
                excess_returns.mean()
                / downside_deviation
                * np.sqrt(annualization_factor)
            )
        else:
            sortino_ratio = np.nan

    else:
        annualized_volatility = np.nan
        sharpe_ratio = np.nan
        annualized_downside_volatility = np.nan
        sortino_ratio = np.nan

    # 7. 最大回撤
    running_max = nav.cummax()
    drawdowns = nav / running_max - 1

    trough_date = drawdowns.idxmin()
    max_drawdown = float(drawdowns.loc[trough_date])

    nav_until_trough = nav.loc[:trough_date]
    peak_nav = nav_until_trough.max()

    peak_date = nav_until_trough[
        nav_until_trough == peak_nav
    ].index[-1]

    drawdown_duration_days = (trough_date - peak_date).days

    # 8. 回撤恢复
    # 恢复日期是谷底之后，净值首次达到或超过此前峰值的日期。
    after_trough = nav.loc[trough_date:]
    recovery_dates = after_trough.index[
        after_trough >= peak_nav
    ]

    if len(recovery_dates) > 0:
        recovery_date = recovery_dates[0]
        recovery_duration_days = (recovery_date - peak_date).days
        recovered = True
        recovery_date_text = recovery_date.strftime("%Y-%m-%d")
    else:
        recovery_duration_days = np.nan
        recovered = False
        recovery_date_text = None

    # 9. 卡玛比率
    if np.isfinite(annualized_return) and max_drawdown < 0:
        calmar_ratio = annualized_return / abs(max_drawdown)
    else:
        calmar_ratio = np.nan

    # 10. 数据质量
    results = {
        "区间收益率": total_return,
        "年化收益率": annualized_return,
        "年化波动率": annualized_volatility,
        "最大回撤": max_drawdown,
        "夏普比率": sharpe_ratio,
        "下行波动率": annualized_downside_volatility,
        "索提诺比率": sortino_ratio,
        "卡玛比率": calmar_ratio,
        "回撤峰值日期": peak_date.strftime("%Y-%m-%d"),
        "回撤谷底日期": trough_date.strftime("%Y-%m-%d"),
        "峰值至谷底天数": int(drawdown_duration_days),
        "回撤是否恢复": recovered,
        "回撤恢复日期": recovery_date_text,
        "峰值至恢复天数": (
            int(recovery_duration_days) if recovered else None
        ),
        "数据起始日期": nav.index[0].strftime("%Y-%m-%d"),
        "数据结束日期": nav.index[-1].strftime("%Y-%m-%d"),
        "有效净值记录数": int(len(nav)),
        "无效记录数": invalid_count,
        "原始记录数": original_count,
        "数据覆盖天数": int(days),
    }

    # 11. 清理 NumPy 标量与非有限数值
    cleaned_results = {}

    for name, value in results.items():
        if isinstance(value, (bool, np.bool_)):
            cleaned_results[name] = bool(value)
        elif isinstance(value, (int, float, np.integer, np.floating)):
            if np.isfinite(value):
                cleaned_results[name] = value.item() if isinstance(
                    value, np.generic
                ) else value
            else:
                cleaned_results[name] = np.nan
        else:
            cleaned_results[name] = value

    return cleaned_results