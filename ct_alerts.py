import pandas as pd

from ct_trend import analyze_company_trend


def _number(value):
    """将值转换为有限数值；缺失、无穷或非数字返回 None。"""
    try:
        result = pd.to_numeric(value, errors="coerce")
        if pd.isna(result):
            return None
        result = float(result)
        if not pd.notna(result) or result in (float("inf"), float("-inf")):
            return None
        return result
    except (TypeError, ValueError):
        return None


def _is_consecutive_quarter(dates):
    """检查报告期是否为连续季度，避免跨过缺失季度后误报。"""
    if len(dates) < 2:
        return False

    normalized = [pd.Timestamp(date) for date in dates]
    for previous, current in zip(normalized, normalized[1:]):
        if previous + pd.offsets.QuarterEnd(1) != current:
            return False
    return True


def _latest_consecutive_rows(df, count):
    """取得末尾 count 个报告期；若日期不连续则返回空表。"""
    if len(df) < count:
        return df.iloc[0:0].copy()

    recent = df.tail(count).copy()
    if not _is_consecutive_quarter(recent["报告期"].tolist()):
        return df.iloc[0:0].copy()

    return recent


def _add_alert(alerts, alert_type, level, report_date, message):
    alerts.append({
        "类型": alert_type,
        "级别": level,
        "报告期": pd.Timestamp(report_date).strftime("%Y-%m-%d"),
        "说明": message,
    })


def analyze_company_alerts(symbol, periods=20, trend=None):
    """
    企业财务异常提示（第一版修订）。

    仅识别数据中的观察信号，不判断财务造假，不生成投资结论。
    当前规则面向一般工商企业；银行、保险、证券等金融机构不适用
    本模块的现金流和资产负债率规则。

    数据质量原则：
    若输入数据存在重复报告期，本次分析将停止生成异常提示，
    并返回数据质量警告，避免任意保留一条重复记录造成误报。
    """

    if (
        not isinstance(periods, int)
        or isinstance(periods, bool)
        or not 1 <= periods <= 100
    ):
        raise ValueError("periods 必须是 1 到 100 之间的整数。")

    if trend is None:
        df = analyze_company_trend(symbol, max(periods, 3)).copy()
    elif isinstance(trend, pd.DataFrame):
        df = trend.copy()
    else:
        raise ValueError("trend must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("没有可用的企业财务数据。")

    required_columns = [
        "报告期",
        "营业收入单季度同比",
        "归母净利润单季度同比",
        "单季度净利率",
        "单季度经营现金流／归母净利润",
        "归母净利润（单季度，元）",
        "资产负债率",
    ]
    missing_columns = [name for name in required_columns if name not in df.columns]
    if missing_columns:
        raise ValueError(
            "趋势数据缺少必要字段：" + "、".join(missing_columns)
        )

    df["报告期"] = pd.to_datetime(df["报告期"], errors="coerce")
    df = (
        df.dropna(subset=["报告期"])
        .sort_values("报告期")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError("没有有效的报告期数据。")

    # 关键修复：先识别重复报告期，不能直接 drop_duplicates(keep="last")。
    duplicate_mask = df.duplicated(subset=["报告期"], keep=False)
    duplicate_dates = (
        df.loc[duplicate_mask, "报告期"]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    data_quality_warnings = []
    if duplicate_dates:
        duplicate_text = "、".join(
            pd.Timestamp(date).strftime("%Y-%m-%d")
            for date in duplicate_dates
        )
        data_quality_warnings.append(
            "发现重复报告期：" + duplicate_text
            + "。为避免任意保留重复记录造成误报，本次已暂停全部异常规则；"
            "请核对数据来源及报表口径后再分析。"
        )
        # 对重复报告期采取保守策略：不任意挑选记录，也不继续生成风险提示。
        # 元数据仍保留去重后的报告期数量；异常提示保持为空。
        unique_dates = df["报告期"].drop_duplicates().sort_values()
        latest_date = unique_dates.iloc[-1]
        return {
            "股票代码": str(symbol),
            "检查报告期": latest_date.strftime("%Y-%m-%d"),
            "检查期数": int(len(unique_dates)),
            "异常数量": 0,
            "异常提示": [],
            "数据质量警告": data_quality_warnings,
            "分析状态": "因数据质量问题暂停异常识别",
            "适用范围说明": (
                "本版规则主要面向一般工商企业。银行、保险、证券等金融机构"
                "的负债结构和现金流特征不同，不应直接套用相关提示。"
            ),
            "结果说明": (
                "本次未生成异常提示，不代表企业没有风险；由于报告期重复，"
                "系统暂停了异常识别。请先核对重复记录、合并报表口径及数据来源。"
            ),
        }

    df = df.reset_index(drop=True)

    alerts = []
    latest = df.iloc[-1]
    latest_date = latest["报告期"]

    revenue_growth = _number(latest["营业收入单季度同比"])
    profit_growth = _number(latest["归母净利润单季度同比"])
    latest_profit = _number(latest["归母净利润（单季度，元）"])

    # 1. 营收与利润背离：只在当季仍盈利且同比基数可解释时提示。
    if (
        revenue_growth is not None
        and profit_growth is not None
        and latest_profit is not None
        and latest_profit > 0
        and revenue_growth > 0
        and -1 < profit_growth < 0
    ):
        _add_alert(
            alerts,
            "营收与利润背离",
            "关注",
            latest_date,
            "营业收入同比增长，但归母净利润同比下降；建议进一步检查成本、费用及非经常性损益。",
        )

    # 2. 净利率连续下降：必须是最近三个连续季度，且三期数据均有效。
    recent_margin = _latest_consecutive_rows(df, 3)
    if not recent_margin.empty:
        margins = [_number(x) for x in recent_margin["单季度净利率"]]
        if (
            all(x is not None for x in margins)
            and margins[0] > margins[1] > margins[2]
        ):
            _add_alert(
                alerts,
                "盈利能力连续下降",
                "关注",
                latest_date,
                "最近三个连续季度的单季度净利率逐季下降。",
            )

    # 3. 现金流与利润匹配：只在归母净利润为正时解释该比率。
    recent_cash = _latest_consecutive_rows(df, 3)
    if not recent_cash.empty:
        profits = [
            _number(x)
            for x in recent_cash["归母净利润（单季度，元）"]
        ]
        cash_ratios = [
            _number(x)
            for x in recent_cash["单季度经营现金流／归母净利润"]
        ]
        if (
            all(x is not None and x > 0 for x in profits)
            and all(x is not None and x < 1 for x in cash_ratios)
        ):
            _add_alert(
                alerts,
                "经营现金流低于净利润",
                "关注",
                latest_date,
                "最近三个连续季度的经营现金流均低于归母净利润；需结合应收账款、存货及回款周期判断。",
            )

    # 4. 资产负债率连续上升：只描述趋势，不直接等同于偿债风险。
    recent_debt = _latest_consecutive_rows(df, 3)
    if not recent_debt.empty:
        debt_ratios = [_number(x) for x in recent_debt["资产负债率"]]
        if (
            all(x is not None for x in debt_ratios)
            and debt_ratios[0] < debt_ratios[1] < debt_ratios[2]
        ):
            _add_alert(
                alerts,
                "资产负债率连续上升",
                "观察",
                latest_date,
                "最近三个连续季度的资产负债率逐季上升；该变化本身不等于偿债风险上升。",
            )

    # 5. 最近两个连续季度营收、利润同比均下降。
    recent_growth = _latest_consecutive_rows(df, 2)
    if not recent_growth.empty:
        revenue_growths = [
            _number(x)
            for x in recent_growth["营业收入单季度同比"]
        ]
        profit_growths = [
            _number(x)
            for x in recent_growth["归母净利润单季度同比"]
        ]
        current_profits = [
            _number(x)
            for x in recent_growth["归母净利润（单季度，元）"]
        ]

        if (
            all(x is not None and x < 0 for x in revenue_growths)
            and all(x is not None and -1 < x < 0 for x in profit_growths)
            and all(x is not None and x > 0 for x in current_profits)
        ):
            _add_alert(
                alerts,
                "营收与利润连续同比下降",
                "重点关注",
                latest_date,
                "最近两个连续季度的营收和归母净利润均同比下降，且当季仍保持盈利。",
            )

    return {
        "股票代码": str(symbol),
        "检查报告期": latest_date.strftime("%Y-%m-%d"),
        "检查期数": len(df),
        "异常数量": len(alerts),
        "异常提示": alerts,
        "数据质量警告": data_quality_warnings,
        "分析状态": "完成",
        "适用范围说明": (
            "本版规则主要面向一般工商企业。银行、保险、证券等金融机构"
            "的负债结构和现金流特征不同，不应直接套用相关提示。"
        ),
        "结果说明": (
            "未触发规则不代表企业没有风险；触发提示也不代表企业存在违规或财务造假。"
            "应结合行业、附注、应收账款、存货、有息负债及现金流明细进一步核查。"
        ),
    }
