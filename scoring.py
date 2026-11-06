import numpy as np


def calculate_quality_score(metrics):
    """计算基金历史质量分。当前为未经历史回测验证的初步规则模型。"""

    required_metrics = [
        "年化收益率",
        "年化波动率",
        "最大回撤",
        "夏普比率",
        "索提诺比率",
        "卡玛比率",
    ]

    for name in required_metrics:
        if name not in metrics:
            return {
                "基金质量分": None,
                "评分状态": "数据不足",
                "评分说明": f"缺少必要指标：{name}",
                "评分明细": {},
            }

    values = {}

    for name in required_metrics:
        value = metrics[name]

        try:
            value = float(value)
        except (TypeError, ValueError):
            return {
                "基金质量分": None,
                "评分状态": "数据异常",
                "评分说明": f"指标 {name} 不是有效数值。",
                "评分明细": {},
            }

        if not np.isfinite(value):
            return {
                "基金质量分": None,
                "评分状态": "数据不足",
                "评分说明": f"指标 {name} 不是有限数值。",
                "评分明细": {},
            }

        values[name] = value

    def clamp(value):
        return max(0.0, min(100.0, value))

    sharpe_score = clamp(
        (values["夏普比率"] + 0.5) / 2.0 * 100
    )

    sortino_score = clamp(
        (values["索提诺比率"] + 0.5) / 2.5 * 100
    )

    risk_adjusted_score = (
        sharpe_score * 0.6 + sortino_score * 0.4
    )

    drawdown_score = clamp(
        (1 - abs(values["最大回撤"]) / 0.6) * 100
    )

    return_score = clamp(
        (values["年化收益率"] + 0.1) / 0.3 * 100
    )

    stability_score = clamp(
        (0.4 - values["年化波动率"]) / 0.4 * 100
    )

    calmar_score = clamp(
        (values["卡玛比率"] + 0.5) / 2.5 * 100
    )

    components = {
        "风险调整后收益": (risk_adjusted_score, 0.35),
        "回撤控制": (drawdown_score, 0.30),
        "收益表现": (return_score, 0.15),
        "波动稳定性": (stability_score, 0.10),
        "收益回撤关系": (calmar_score, 0.10),
    }

    score = sum(
        component_score * weight
        for component_score, weight in components.values()
    )

    score = round(clamp(score))

    details = {
        name: round(component_score, 1)
        for name, (component_score, _) in components.items()
    }

    return {
        "基金质量分": score,
        "评分状态": "初步评分",
        "评分说明": (
            "根据历史收益与风险指标计算的初步规则评分，"
            "尚未经过历史回测验证，不代表未来收益或买入建议。"
        ),
        "评分明细": details,
    }


def calculate_attractiveness_score(
    quality_score=None,
    valuation_data=None,
    market_data=None,
    holdings_data=None,
    investor_profile=None,
):
    """当前尚未建立经过验证的投资吸引力评分模型。"""

    return {
        "当前投资吸引力分": None,
        "评分状态": "暂未开放",
        "评分说明": (
            "当前尚未建立经过验证的投资吸引力模型。"
            "不会仅凭基金历史质量分推断当前是否值得买入。"
        ),
    }