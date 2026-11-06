import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import ct_alerts


def make_history(dates=None):
    if dates is None:
        dates = [
            "2025-03-31",
            "2025-06-30",
            "2025-09-30",
            "2025-12-31",
        ]

    n = len(dates)
    return pd.DataFrame({
        "报告期": pd.to_datetime(dates),
        "营业收入单季度同比": [0.05] * n,
        "归母净利润单季度同比": [0.05] * n,
        "单季度净利率": [0.10] * n,
        "单季度经营现金流／归母净利润": [1.20] * n,
        "归母净利润（单季度，元）": [100.0] * n,
        "资产负债率": [0.40] * n,
    })


def run_with_history(history):
    with patch.object(
        ct_alerts,
        "analyze_company_trend",
        return_value=history.copy()
    ):
        return ct_alerts.analyze_company_alerts("TEST", periods=20)


class TestCompanyAlertsBoundaries(unittest.TestCase):

    def alert_types(self, result):
        return {item["类型"] for item in result["异常提示"]}

    def test_year_boundary_is_still_consecutive(self):
        """跨自然年但季度连续时，连续季度规则仍应生效。"""
        df = make_history([
            "2025-09-30",
            "2025-12-31",
            "2026-03-31",
            "2026-06-30",
        ])
        df.loc[1:, "单季度净利率"] = [0.12, 0.11, 0.10]
        result = run_with_history(df)
        self.assertIn("盈利能力连续下降", self.alert_types(result))

    def test_duplicate_report_period_does_not_fake_three_quarters(self):
        """重复报告期不能被当作新的连续季度。"""
        df = make_history([
            "2025-03-31",
            "2025-06-30",
            "2025-06-30",
            "2025-09-30",
        ])
        df["单季度净利率"] = [0.14, 0.13, 0.12, 0.11]
        result = run_with_history(df)
        # 只有三个不同报告期，其中净利率序列存在重复期冲突；
        # 不应仅凭重复记录构造出连续三个季度下降。
        self.assertNotIn("盈利能力连续下降", self.alert_types(result))

    def test_zero_profit_cash_ratio_is_not_meaningful(self):
        """净利润为零时，现金流/净利润比率不应触发规则。"""
        df = make_history()
        df.loc[1:, "归母净利润（单季度，元）"] = [0.0, 0.0, 0.0]
        df.loc[1:, "单季度经营现金流／归母净利润"] = [
            np.inf, np.nan, -np.inf
        ]
        result = run_with_history(df)
        self.assertNotIn("经营现金流低于净利润", self.alert_types(result))

    def test_missing_ratio_in_middle_does_not_bridge_three_quarters(self):
        """三期中间缺值时，不应删除缺值后把两侧季度拼成连续序列。"""
        df = make_history()
        df.loc[1:, "单季度经营现金流／归母净利润"] = [
            0.80, np.nan, 0.60
        ]
        result = run_with_history(df)
        self.assertNotIn("经营现金流低于净利润", self.alert_types(result))

    def test_negative_operating_cash_flow_with_positive_profit_is_flagged(self):
        """正利润但连续经营现金流为负，应触发现金流质量提示。"""
        df = make_history()
        df.loc[1:, "单季度经营现金流／归母净利润"] = [
            -0.20, -0.30, -0.40
        ]
        result = run_with_history(df)
        self.assertIn("经营现金流低于净利润", self.alert_types(result))

    def test_extreme_debt_ratio_does_not_crash(self):
        """资产负债率超过100%时至少应能稳定处理，不应程序崩溃。"""
        df = make_history()
        df.loc[1:, "资产负债率"] = [1.05, 1.10, 1.15]
        result = run_with_history(df)
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result["异常数量"], 1)
        self.assertIn("资产负债率连续上升", self.alert_types(result))

    def test_multiple_rules_can_trigger_together(self):
        """同一企业同时满足多项规则时，应保留多条提示。"""
        df = make_history()
        df.loc[1:, "单季度净利率"] = [0.12, 0.11, 0.10]
        df.loc[1:, "单季度经营现金流／归母净利润"] = [0.80, 0.70, 0.60]
        df.loc[1:, "资产负债率"] = [0.41, 0.43, 0.45]
        result = run_with_history(df)
        types = self.alert_types(result)
        self.assertIn("盈利能力连续下降", types)
        self.assertIn("经营现金流低于净利润", types)
        self.assertIn("资产负债率连续上升", types)
        self.assertGreaterEqual(result["异常数量"], 3)

    def test_missing_numeric_value_does_not_crash(self):
        """其他指标有缺失值时，模块应稳定返回结果。"""
        df = make_history()
        df.loc[3, "营业收入单季度同比"] = np.nan
        df.loc[2, "资产负债率"] = np.nan
        result = run_with_history(df)
        self.assertIsInstance(result, dict)
        self.assertIn("异常数量", result)
        self.assertIn("异常提示", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
