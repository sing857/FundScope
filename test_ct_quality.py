import pandas as pd
import pytest

import ct_quality


@pytest.fixture
def valid_reports():
    dates = pd.to_datetime([
        "2025-09-30",
        "2025-12-31",
        "2026-03-31",
    ])

    return {
        "income": pd.DataFrame({
            "REPORT_DATE": dates,
            "OPERATE_INCOME": [100, 110, 120],
            "PARENT_NETPROFIT": [10, 12, 15],
            "OPERATE_INCOME_YOY": [5, 8, 10],
            "PARENT_NETPROFIT_YOY": [6, 10, 12],
        }),
        "balance": pd.DataFrame({
            "REPORT_DATE": dates,
            "TOTAL_ASSETS": [500, 520, 550],
            "TOTAL_LIABILITIES": [200, 210, 220],
        }),
        "cashflow": pd.DataFrame({
            "REPORT_DATE": dates,
            "NETCASH_OPERATE": [15, 18, 20],
        }),
    }


def block_fetchers(monkeypatch):
    """确保传入 reports 后不会再次调用财报获取函数。"""

    fetchers = {
        "income": "fetch_stock_income_statement",
        "balance": "fetch_stock_balance_sheet",
        "cashflow": "fetch_stock_cash_flow_statement",
    }

    for key, name in fetchers.items():
        def should_not_fetch(symbol, report=key):
            pytest.fail(
                f"Provided reports should prevent fetching {report} again."
            )

        monkeypatch.setattr(ct_quality, name, should_not_fetch)
        monkeypatch.setitem(
            ct_quality.REPORT_CONFIG[key_name(key)],
            "fetcher",
            should_not_fetch,
        )


def key_name(key):
    return {
        "income": "利润表",
        "balance": "资产负债表",
        "cashflow": "现金流量表",
    }[key]


def test_valid_reports_are_checked_without_refetching(
    monkeypatch, valid_reports
):
    block_fetchers(monkeypatch)

    result = ct_quality.validate_company_data(
        "600000",
        reports=valid_reports,
    )

    assert result["报表概况"].shape[0] == 3
    assert result["报表获取错误"].empty
    assert result["报告期匹配"]["三张报表是否全部成功"] is True
    assert result["报告期匹配"]["共同报告期数量"] == 3


def test_one_empty_report_does_not_block_other_reports(
    monkeypatch, valid_reports
):
    block_fetchers(monkeypatch)

    valid_reports["balance"] = pd.DataFrame()

    result = ct_quality.validate_company_data(
        "600000",
        reports=valid_reports,
    )

    assert result["报表概况"].shape[0] == 2
    assert len(result["报表获取错误"]) == 1
    assert result["报表获取错误"].iloc[0]["报表"] == "资产负债表"
    assert result["报告期匹配"]["三张报表是否全部成功"] is False

    successful_reports = set(result["报表概况"]["报表"])

    assert "利润表" in successful_reports
    assert "现金流量表" in successful_reports
    assert "资产负债表" not in successful_reports


def test_missing_financial_field_is_reported_without_blocking_checks(
    monkeypatch, valid_reports
):
    block_fetchers(monkeypatch)

    valid_reports["income"] = valid_reports["income"].drop(
        columns=["PARENT_NETPROFIT"]
    )

    result = ct_quality.validate_company_data(
        "600000",
        reports=valid_reports,
    )

    # 报表结构仍然有效，三张报表均成功读取
    assert result["报表概况"].shape[0] == 3
    assert result["报表获取错误"].empty

    # 缺失字段应被明确识别
    missing_field = result["字段质量"].loc[
        result["字段质量"]["字段"] == "PARENT_NETPROFIT"
    ]

    assert len(missing_field) == 1
    assert missing_field.iloc[0]["状态"] == "缺少字段"

    # 依赖归母净利润的指标应被标记为不可计算
    unavailable = result["指标可用性"].loc[
        result["指标可用性"]["指标"].isin([
            "净利率",
            "经营现金流／归母净利润",
        ])
    ]

    assert len(unavailable) == 6
    assert (unavailable["状态"] == "不可计算").all()

    # 资产负债率不依赖利润表，应仍然具备计算条件
    debt_ratio = result["指标可用性"].loc[
        result["指标可用性"]["指标"] == "资产负债率"
    ]

    assert len(debt_ratio) == 3
    assert (debt_ratio["状态"] == "具备计算条件").all()

def test_report_period_mismatch_is_identified_without_invalidating_reports(
    monkeypatch, valid_reports
):
    block_fetchers(monkeypatch)

    # 现金流量表缺少 2025 年第四季度
    valid_reports["cashflow"] = valid_reports["cashflow"].loc[
        valid_reports["cashflow"]["REPORT_DATE"] != pd.Timestamp("2025-12-31")
    ].copy()

    result = ct_quality.validate_company_data(
        "600000",
        reports=valid_reports,
    )

    # 三张报表本身均成功读取
    assert result["报表概况"].shape[0] == 3
    assert result["报表获取错误"].empty

    # 共同报告期为两个
    summary = result["报告期匹配"]

    assert summary["三张报表是否全部成功"] is True
    assert summary["共同报告期数量"] == 2
    assert summary["报告期总数"] == 3
    assert summary["未共同覆盖的报告期数量"] == 1

    # 明确识别现金流量表缺失的报告期
    differences = result["报告期差异明细"]

    missing_period = differences.loc[
        (differences["报表"] == "现金流量表")
        & (differences["报告期"] == pd.Timestamp("2025-12-31"))
    ]

    assert len(missing_period) == 1
    assert missing_period.iloc[0]["差异类型"] == "该报表缺失"

    # 2025Q4 的现金流指标不可计算
    unavailable = result["指标可用性"].loc[
        (result["指标可用性"]["报告期"] == pd.Timestamp("2025-12-31"))
        & (result["指标可用性"]["指标"] == "经营现金流／归母净利润")
    ]

    assert len(unavailable) == 1
    assert unavailable.iloc[0]["状态"] == "不可计算"

    # 其他两个共同报告期的三个核心指标均可计算
    common_periods = result["指标可用性"].loc[
        result["指标可用性"]["报告期"].isin([
            pd.Timestamp("2025-09-30"),
            pd.Timestamp("2026-03-31"),
        ])
    ]

    assert len(common_periods) == 6
    assert (common_periods["状态"] == "具备计算条件").all()

def test_non_numeric_missing_and_infinite_values_are_identified(
    monkeypatch, valid_reports
):
    block_fetchers(monkeypatch)

    valid_reports["income"]["OPERATE_INCOME"] = valid_reports["income"]["OPERATE_INCOME"].astype(object)
    valid_reports["income"].loc[0, "OPERATE_INCOME"] = "abc"
    valid_reports["income"].loc[1, "OPERATE_INCOME"] = float("nan")
    valid_reports["income"].loc[2, "OPERATE_INCOME"] = float("inf")

    result = ct_quality.validate_company_data(
        "600000",
        reports=valid_reports,
    )

    # 三张报表仍应成功读取
    assert result["报表概况"].shape[0] == 3
    assert result["报表获取错误"].empty

    # 三类异常分别识别
    field = result["字段质量"].loc[
        result["字段质量"]["字段"] == "OPERATE_INCOME"
    ]

    assert len(field) == 1
    assert field.iloc[0]["状态"] == "需检查"
    assert field.iloc[0]["缺失数量"] == 1
    assert field.iloc[0]["非数值数量"] == 1
    assert field.iloc[0]["无穷值数量"] == 1

    # 营业收入异常，三个报告期的净利率均不可计算
    net_margin = result["指标可用性"].loc[
        result["指标可用性"]["指标"] == "净利率"
    ]

    assert len(net_margin) == 3
    assert (net_margin["状态"] == "不可计算").all()

    # 其他不依赖营业收入的指标不应受到影响
    other_indicators = result["指标可用性"].loc[
        result["指标可用性"]["指标"].isin([
            "资产负债率",
            "经营现金流／归母净利润",
        ])
    ]

    assert len(other_indicators) == 6
    assert (other_indicators["状态"] == "具备计算条件").all()


def test_duplicate_report_period_is_identified_and_indicators_are_blocked(
    monkeypatch, valid_reports
):
    block_fetchers(monkeypatch)

    # 增加一条重复的 2025 年第四季度利润表记录
    duplicate_row = valid_reports["income"].loc[
        valid_reports["income"]["REPORT_DATE"] == pd.Timestamp("2025-12-31")
    ].copy()

    duplicate_row.loc[:, "PARENT_NETPROFIT"] = 99

    valid_reports["income"] = pd.concat(
        [valid_reports["income"], duplicate_row],
        ignore_index=True,
    )

    result = ct_quality.validate_company_data(
        "600000",
        reports=valid_reports,
    )

    # 三张报表均应成功读取
    assert result["报表概况"].shape[0] == 3
    assert result["报表获取错误"].empty

    # 利润表应识别出一个重复报告期
    income_summary = result["报表概况"].loc[
        result["报表概况"]["报表"] == "利润表"
    ]

    assert len(income_summary) == 1
    assert income_summary.iloc[0]["重复报告期数量"] == 1
    assert income_summary.iloc[0]["涉及重复的记录数"] == 2

    # 归母净利润应识别为数值冲突
    conflicts = result["重复内容检查"].loc[
        (result["重复内容检查"]["报告期"] == pd.Timestamp("2025-12-31"))
        & (result["重复内容检查"]["字段"] == "PARENT_NETPROFIT")
    ]

    assert len(conflicts) == 1
    assert conflicts.iloc[0]["状态"] == "数值冲突"

    # 重复报告期依赖利润表的指标不可计算
    unavailable = result["指标可用性"].loc[
        (result["指标可用性"]["报告期"] == pd.Timestamp("2025-12-31"))
        & (result["指标可用性"]["指标"].isin([
            "净利率",
            "经营现金流／归母净利润",
        ]))
    ]

    assert len(unavailable) == 2
    assert (unavailable["状态"] == "不可计算").all()

    # 资产负债率不依赖利润表，仍可计算
    debt_ratio = result["指标可用性"].loc[
        (result["指标可用性"]["报告期"] == pd.Timestamp("2025-12-31"))
        & (result["指标可用性"]["指标"] == "资产负债率")
    ]

    assert len(debt_ratio) == 1
    assert debt_ratio.iloc[0]["状态"] == "具备计算条件"
