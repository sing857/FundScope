from scoring import calculate_quality_score


def make_metrics():
    return {
        "年化收益率": 0.10,
        "年化波动率": 0.20,
        "最大回撤": -0.30,
        "夏普比率": 0.50,
        "索提诺比率": 0.70,
        "卡玛比率": 0.33,
    }


def get_score(metrics):
    result = calculate_quality_score(metrics)
    return result["基金质量分"], result["评分明细"]


baseline = make_metrics()
base_score, base_details = get_score(baseline)

print(f"基准总分：{base_score}")
print("基准分项得分：")

for name, score in base_details.items():
    print(f"  {name}：{score}")


scenarios = [
    ("年化收益率提高至15%", "年化收益率", 0.15),
    ("年化收益率提高至20%", "年化收益率", 0.20),
    ("年化收益率提高至30%", "年化收益率", 0.30),
    ("年化波动率提高至30%", "年化波动率", 0.30),
    ("最大回撤扩大至40%", "最大回撤", -0.40),
    ("夏普比率提高至1.0", "夏普比率", 1.00),
]

print("\n单项指标敏感性测试：")

for description, metric_name, new_value in scenarios:
    metrics = make_metrics()
    metrics[metric_name] = new_value

    score, details = get_score(metrics)

    print(
        f"{description}："
        f"总分 {score}，"
        f"变化 {score - base_score:+d}"
    )


print("\n收益评分边界测试：")

for annual_return in [0.19, 0.20, 0.21, 0.30, 0.50]:
    metrics = make_metrics()
    metrics["年化收益率"] = annual_return

    score, details = get_score(metrics)

    print(
        f"年化收益率 {annual_return:.0%}："
        f"收益表现得分 {details['收益表现']:.1f}，"
        f"总分 {score}"
    )