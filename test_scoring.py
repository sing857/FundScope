import unittest

from scoring import (
    calculate_quality_score,
    calculate_attractiveness_score,
)


class TestFundScoring(unittest.TestCase):

    def make_metrics(self):
        return {
            "年化收益率": 0.10,
            "年化波动率": 0.20,
            "最大回撤": -0.30,
            "夏普比率": 0.80,
            "索提诺比率": 1.20,
            "卡玛比率": 0.33,
        }

    def test_quality_score_range(self):
        result = calculate_quality_score(self.make_metrics())

        self.assertIsInstance(result["基金质量分"], int)
        self.assertGreaterEqual(result["基金质量分"], 0)
        self.assertLessEqual(result["基金质量分"], 100)

    def test_quality_score_has_details(self):
        result = calculate_quality_score(self.make_metrics())

        self.assertEqual(result["评分状态"], "初步评分")
        self.assertIn("风险调整后收益", result["评分明细"])
        self.assertIn("回撤控制", result["评分明细"])

    def test_missing_metric(self):
        metrics = self.make_metrics()
        del metrics["夏普比率"]

        result = calculate_quality_score(metrics)

        self.assertIsNone(result["基金质量分"])
        self.assertEqual(result["评分状态"], "数据不足")

    def test_invalid_metric(self):
        metrics = self.make_metrics()
        metrics["最大回撤"] = float("nan")

        result = calculate_quality_score(metrics)

        self.assertIsNone(result["基金质量分"])
        self.assertEqual(result["评分状态"], "数据不足")

    def test_attractiveness_not_yet_available(self):
        result = calculate_attractiveness_score(
            quality_score=90
        )

        self.assertIsNone(result["当前投资吸引力分"])
        self.assertEqual(result["评分状态"], "暂未开放")


if __name__ == "__main__":
    unittest.main(verbosity=2)