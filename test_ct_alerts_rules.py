import unittest
from unittest.mock import patch

import pandas as pd

import ct_alerts


def make_history():
    """构造四个连续季度的中性基准数据。"""
    return pd.DataFrame({
        "报告期": pd.to_datetime([
            "2025-03-31",
            "2025-06-30",
            "2025-09-30",
            "2025-12-31",
        ]),
        "营业收入单季度同比": [0.05, 0.05, 0.05, 0.05],
        "归母净利润单季度同比": [0.05, 0.05, 0.05, 0.05],
        "单季度净利率": [0.10, 0.10, 0.10, 0.10],
        "单季度经营现金流／归母净利润": [1.20, 1.20, 1.20, 1.20],
        "归母净利润（单季度，元）": [100, 100, 100, 100],
        "资产负债率": [0.40, 0.40, 0.40, 0.40],
    })


def run_with_history(history):
    """用人工数据替代真实联网取数，直接测试异常识别规则。"""
    with patch.object(
        ct_alerts,
        "analyze_company_trend",
        return_value=history.copy()
    ):
        return ct_alerts.analyze_company_alerts("TEST", periods=20)


class TestCompanyAlerts(unittest.TestCase):

    def alert_types(self, result):
        return {item["类型"] for item in result["异常提示"]}

    def test_normal_data_no_alert(self):
        result = run_with_history(make_history())
        self.assertEqual(result["异常数量"], 0)
        self.assertEqual(result["异常提示"], [])

    def test_rule_1_revenue_up_profit_down(self):
        df = make_history()
        df.loc[3, "营业收入单季度同比"] = 0.12
        df.loc[3, "归母净利润单季度同比"] = -0.20
        result = run_with_history(df)
        self.assertIn("营收与利润背离", self.alert_types(result))

    def test_rule_2_margin_falls_three_quarters(self):
        df = make_history()
        df.loc[1:, "单季度净利率"] = [0.12, 0.11, 0.10]
        result = run_with_history(df)
        self.assertIn("盈利能力连续下降", self.alert_types(result))

    def test_rule_3_cash_flow_below_profit_three_quarters(self):
        df = make_history()
        df.loc[1:, "单季度经营现金流／归母净利润"] = [0.80, 0.70, 0.60]
        result = run_with_history(df)
        self.assertIn("经营现金流低于净利润", self.alert_types(result))

    def test_rule_4_debt_ratio_rises_three_quarters(self):
        df = make_history()
        df.loc[1:, "资产负债率"] = [0.41, 0.43, 0.45]
        result = run_with_history(df)
        self.assertIn("资产负债率连续上升", self.alert_types(result))

    def test_rule_5_revenue_and_profit_fall_two_quarters(self):
        df = make_history()
        df.loc[2:, "营业收入单季度同比"] = [-0.08, -0.12]
        df.loc[2:, "归母净利润单季度同比"] = [-0.10, -0.18]
        result = run_with_history(df)
        self.assertIn("营收与利润连续同比下降", self.alert_types(result))

    def test_missing_quarter_does_not_count_as_consecutive(self):
        df = make_history()
        # 删除第二季度，剩余报告期不连续；连续季度规则不应触发。
        df = df[df["报告期"] != pd.Timestamp("2025-06-30")].reset_index(drop=True)
        df.loc[df.index[-1], "单季度净利率"] = 0.08
        df.loc[df.index[-2], "单季度净利率"] = 0.09
        df.loc[df.index[-1], "单季度经营现金流／归母净利润"] = 0.50
        df.loc[df.index[-2], "单季度经营现金流／归母净利润"] = 0.60
        df.loc[df.index[-1], "资产负债率"] = 0.50
        df.loc[df.index[-2], "资产负债率"] = 0.45
        result = run_with_history(df)
        types = self.alert_types(result)
        self.assertNotIn("盈利能力连续下降", types)
        self.assertNotIn("经营现金流低于净利润", types)
        self.assertNotIn("资产负债率连续上升", types)
        self.assertNotIn("营收与利润连续同比下降", types)

    def test_negative_profit_does_not_trigger_cash_ratio_alert(self):
        df = make_history()
        df.loc[1:, "归母净利润（单季度，元）"] = [-100, -100, -100]
        df.loc[1:, "单季度经营现金流／归母净利润"] = [0.50, 0.50, 0.50]
        result = run_with_history(df)
        self.assertNotIn("经营现金流低于净利润", self.alert_types(result))

    def test_profit_turnaround_does_not_trigger_rule_1(self):
        df = make_history()
        df.loc[3, "营业收入单季度同比"] = 0.10
        df.loc[3, "归母净利润单季度同比"] = -1.20
        result = run_with_history(df)
        self.assertNotIn("营收与利润背离", self.alert_types(result))

    def test_missing_required_column_raises_clear_error(self):
        df = make_history().drop(columns=["资产负债率"])
        with self.assertRaisesRegex(ValueError, "缺少必要字段"):
            run_with_history(df)


if __name__ == "__main__":
    unittest.main(verbosity=2)
