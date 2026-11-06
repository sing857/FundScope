import math

from scoring import calculate_quality_score


def make_metrics():
    """构造一组用于测试的基准指标。"""
    return {
        "年化收益率": 0.10,
        "年化波动率": 0.20,
        "最大回撤": -0.30,
        "夏普比率": 0.50,
        "索提诺比率": 0.70,
        "卡玛比率": 0.33,
    }


def test_baseline_score():
    """基准指标应当能够正常评分。"""
    result = calculate_quality_score(make_metrics())

    assert result["基金质量分"] is not None
    assert 0 <= result["基金质量分"] <= 100

    print("通过：基准评分测试")


def test_return_monotonicity():
    """其他条件不变时，提高年化收益不应降低评分。"""
    metrics = make_metrics()
    original_score = calculate_quality_score(metrics)["基金质量分"]

    metrics["年化收益率"] = 0.15
    new_score = calculate_quality_score(metrics)["基金质量分"]

    assert new_score >= original_score

    print("通过：收益单调性测试")


def test_drawdown_monotonicity():
    """其他条件不变时，扩大最大回撤不应提高评分。"""
    metrics = make_metrics()
    original_score = calculate_quality_score(metrics)["基金质量分"]

    metrics["最大回撤"] = -0.40
    new_score = calculate_quality_score(metrics)["基金质量分"]

    assert new_score <= original_score

    print("通过：回撤单调性测试")


def test_missing_metric():
    """缺少必要指标时，应当返回数据不足。"""
    metrics = make_metrics()
    del metrics["夏普比率"]

    result = calculate_quality_score(metrics)

    assert result["基金质量分"] is None
    assert result["评分状态"] == "数据不足"

    print("通过：缺失指标测试")


def test_infinite_metric():
    """指标为无穷值时，不应生成评分。"""
    metrics = make_metrics()
    metrics["年化收益率"] = math.inf

    result = calculate_quality_score(metrics)

    assert result["基金质量分"] is None

    print("通过：无穷值测试")


if __name__ == "__main__":
    tests = [
        test_baseline_score,
        test_return_monotonicity,
        test_drawdown_monotonicity,
        test_missing_metric,
        test_infinite_metric,
    ]

    for test in tests:
        test()

    print("\n第一轮评分逻辑测试全部通过。")