import numpy as np
import pandas as pd

from data_fetcher import (
    fetch_stock_income_statement,
    fetch_stock_balance_sheet,
    fetch_stock_cash_flow_statement,
)


REPORT_CONFIG = {
    "利润表": {
        "fetcher": fetch_stock_income_statement,
        "fields": [
            "OPERATE_INCOME",
            "PARENT_NETPROFIT",
            "OPERATE_INCOME_YOY",
            "PARENT_NETPROFIT_YOY",
        ],
    },
    "资产负债表": {
        "fetcher": fetch_stock_balance_sheet,
        "fields": [
            "TOTAL_ASSETS",
            "TOTAL_LIABILITIES",
        ],
    },
    "现金流量表": {
        "fetcher": fetch_stock_cash_flow_statement,
        "fields": [
            "NETCASH_OPERATE",
        ],
    },
}


def _prepare_report(df, report_name):
    """检查报表结构、日期及重复报告期。"""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError(f"{report_name}数据无效。")

    if df.empty:
        raise ValueError(f"{report_name}没有数据。")

    if "REPORT_DATE" not in df.columns:
        raise ValueError(f"{report_name}缺少 REPORT_DATE 字段。")

    result = df.copy()
    result["REPORT_DATE"] = pd.to_datetime(
        result["REPORT_DATE"], errors="coerce"
    )

    invalid_dates = int(result["REPORT_DATE"].isna().sum())
    result = result.dropna(subset=["REPORT_DATE"]).copy()

    duplicate_mask = result.duplicated(
        subset=["REPORT_DATE"], keep=False
    )
    duplicate_rows = result.loc[duplicate_mask].copy()

    summary = {
        "报表": report_name,
        "原始记录数": len(df),
        "有效日期记录数": len(result),
        "无效日期数量": invalid_dates,
        "重复报告期数量": int(
            duplicate_rows["REPORT_DATE"].nunique()
        ),
        "涉及重复的记录数": len(duplicate_rows),
        "最早报告期": (
            result["REPORT_DATE"].min()
            if not result.empty else pd.NaT
        ),
        "最新报告期": (
            result["REPORT_DATE"].max()
            if not result.empty else pd.NaT
        ),
    }

    return result, summary


def _check_fields(df, report_name, fields):
    """检查字段存在性、缺失、非数值及无穷值。"""
    results = []

    for field in fields:
        if field not in df.columns:
            results.append({
                "报表": report_name,
                "字段": field,
                "状态": "缺少字段",
                "缺失数量": None,
                "非数值数量": None,
                "无穷值数量": None,
            })
            continue

        original = df[field]
        numeric = pd.to_numeric(original, errors="coerce")

        missing = int(original.isna().sum())
        non_numeric = int(
            (original.notna() & numeric.isna()).sum()
        )
        infinite = int(
            np.isinf(numeric.dropna().to_numpy(dtype=float)).sum()
        )

        status = (
            "正常"
            if missing == 0 and non_numeric == 0 and infinite == 0
            else "需检查"
        )

        results.append({
            "报表": report_name,
            "字段": field,
            "状态": status,
            "缺失数量": missing,
            "非数值数量": non_numeric,
            "无穷值数量": infinite,
        })

    return results


def _check_duplicate_values(df, report_name, fields):
    """检查重复报告期的关键财务字段是否存在数值冲突。"""
    results = []

    duplicate_mask = df.duplicated(
        subset=["REPORT_DATE"], keep=False
    )
    duplicated = df.loc[duplicate_mask]

    for date, group in duplicated.groupby("REPORT_DATE", sort=True):
        for field in fields:
            if field not in group.columns:
                continue

            original = group[field]
            numeric = pd.to_numeric(original, errors="coerce")
            valid = numeric.dropna()

            conflict = False

            if len(valid) > 1:
                values = valid.to_numpy(dtype=float)
                conflict = not np.allclose(
                    values,
                    values[0],
                    rtol=1e-9,
                    atol=1e-9,
                )

            missing_count = int(numeric.isna().sum())

            if conflict:
                status = "数值冲突"
            elif missing_count:
                status = "存在缺失，需复核"
            else:
                status = "数值一致"

            results.append({
                "报表": report_name,
                "报告期": date,
                "字段": field,
                "重复记录数": len(group),
                "有效数值数": len(valid),
                "缺失或非数值数量": missing_count,
                "状态": status,
            })

    return results


def _number_at_date(df, date, field):
    """仅当报告期唯一且数值有效时返回数值。"""
    if field not in df.columns:
        return None, "缺少字段"

    rows = df.loc[df["REPORT_DATE"] == date]

    if rows.empty:
        return None, "报告期缺失"

    if len(rows) != 1:
        return None, "报告期重复，需复核"

    value = pd.to_numeric(
        rows.iloc[0][field], errors="coerce"
    )

    if pd.isna(value):
        return None, "数值缺失或无法转换"

    value = float(value)

    if not np.isfinite(value):
        return None, "数值不是有限值"

    return value, None


def _check_indicator_availability(reports):
    """检查核心财务指标是否具备计算条件，不进行风险评分。"""
    income = reports["利润表"]
    balance = reports["资产负债表"]
    cashflow = reports["现金流量表"]

    date_sets = [
        set(df["REPORT_DATE"])
        for df in reports.values()
    ]
    all_dates = sorted(set.union(*date_sets))

    definitions = [
        {
            "指标": "净利率",
            "inputs": [
                ("营业收入", income, "OPERATE_INCOME"),
                ("归母净利润", income, "PARENT_NETPROFIT"),
            ],
            "denominator": "营业收入",
        },
        {
            "指标": "资产负债率",
            "inputs": [
                ("总资产", balance, "TOTAL_ASSETS"),
                ("总负债", balance, "TOTAL_LIABILITIES"),
            ],
            "denominator": "总资产",
        },
        {
            "指标": "经营现金流／归母净利润",
            "inputs": [
                ("归母净利润", income, "PARENT_NETPROFIT"),
                ("经营现金流", cashflow, "NETCASH_OPERATE"),
            ],
            "denominator": "归母净利润",
        },
    ]

    results = []

    for date in all_dates:
        for definition in definitions:
            values = {}
            problems = []

            for label, df, field in definition["inputs"]:
                value, problem = _number_at_date(
                    df, date, field
                )

                values[label] = value

                if problem:
                    problems.append(f"{label}：{problem}")

            denominator = values.get(
                definition["denominator"]
            )

            if problems:
                status = "不可计算"
                reason = "；".join(problems)

            elif denominator == 0:
                status = "不可计算"
                reason = (
                    f"{definition['denominator']}为零，"
                    "不能作为分母"
                )

            else:
                status = "具备计算条件"
                reason = "必要字段有效且分母非零"

            results.append({
                "报告期": date,
                "指标": definition["指标"],
                "状态": status,
                "说明": reason,
            })

    return results


def _check_recent_coverage(report_date_sets, periods=20):
    """检查三张报表最近20个季度末的覆盖情况。"""
    if len(report_date_sets) != len(REPORT_CONFIG):
        return pd.DataFrame(), {
            "检查状态": "无法完整检查",
            "原因": "至少一张报表获取失败",
        }

    all_dates = set.union(*report_date_sets.values())

    quarter_dates = sorted(
        date for date in all_dates
        if date.month in (3, 6, 9, 12)
        and date.day == date.days_in_month
    )

    target_dates = quarter_dates[-periods:]

    rows = []

    for date in target_dates:
        present_count = 0

        for report_name, dates in report_date_sets.items():
            present = date in dates

            if present:
                present_count += 1

            rows.append({
                "报告期": date,
                "报表": report_name,
                "是否存在": present,
                "状态": "存在" if present else "缺失",
            })

    coverage = pd.DataFrame(rows)

    common_count = sum(
        all(date in dates for dates in report_date_sets.values())
        for date in target_dates
    )

    summary = {
        "检查状态": "完成",
        "目标季度数": len(target_dates),
        "三表共同覆盖季度数": common_count,
        "未被三表共同覆盖季度数": (
            len(target_dates) - common_count
        ),
        "最早检查报告期": (
            target_dates[0] if target_dates else None
        ),
        "最新检查报告期": (
            target_dates[-1] if target_dates else None
        ),
    }

    return coverage, summary


def validate_company_data(symbol, reports=None):
    """执行上市公司财报质量检查。"""
    symbol = str(symbol).strip()

    if len(symbol) != 6 or not symbol.isdigit():
        raise ValueError(
            "股票代码必须是6位数字，例如600519。"
        )

    source_reports = reports
    reports = {}
    summaries = []
    field_results = []
    duplicate_results = []
    errors = []

    for report_name, config in REPORT_CONFIG.items():
        try:
            if source_reports is None:
                raw_df = config["fetcher"](symbol)
            else:
                input_key = {
                    fetch_stock_income_statement: "income",
                    fetch_stock_balance_sheet: "balance",
                    fetch_stock_cash_flow_statement: "cashflow",
                }[config["fetcher"]]
                raw_df = source_reports.get(input_key)
            df, summary = _prepare_report(
                raw_df, report_name
            )

            reports[report_name] = df
            summaries.append(summary)

            field_results.extend(
                _check_fields(
                    df, report_name, config["fields"]
                )
            )

            duplicate_results.extend(
                _check_duplicate_values(
                    df, report_name, config["fields"]
                )
            )

        except Exception as exc:
            errors.append({
                "报表": report_name,
                "错误类型": type(exc).__name__,
                "错误信息": str(exc),
            })

    all_success = len(reports) == len(REPORT_CONFIG)

    date_summary = {
        "成功检查的报表数量": len(reports),
        "应检查的报表数量": len(REPORT_CONFIG),
        "三张报表是否全部成功": all_success,
        "共同报告期数量": None,
        "报告期总数": None,
        "未共同覆盖的报告期数量": None,
    }

    date_differences = []

    if all_success:
        date_sets = {
            name: set(df["REPORT_DATE"])
            for name, df in reports.items()
        }

        common_dates = set.intersection(*date_sets.values())
        all_dates = set.union(*date_sets.values())

        date_summary.update({
            "共同报告期数量": len(common_dates),
            "报告期总数": len(all_dates),
            "未共同覆盖的报告期数量": (
                len(all_dates - common_dates)
            ),
        })

        for report_name, dates in date_sets.items():
            other_dates = set.union(*[
                other_dates
                for other_name, other_dates in date_sets.items()
                if other_name != report_name
            ])

            for date in sorted(dates - other_dates):
                date_differences.append({
                    "报表": report_name,
                    "报告期": date,
                    "差异类型": "仅该报表存在",
                })

            for date in sorted(all_dates - dates):
                date_differences.append({
                    "报表": report_name,
                    "报告期": date,
                    "差异类型": "该报表缺失",
                })

        indicator_results = _check_indicator_availability(
            reports
        )

    else:
        date_sets = {}
        indicator_results = []

    coverage_df, coverage_summary = _check_recent_coverage(
        date_sets if all_success else {},
        periods=20,
    )

    return {
        "报表概况": pd.DataFrame(summaries),
        "字段质量": pd.DataFrame(field_results),
        "重复内容检查": pd.DataFrame(duplicate_results),
        "报告期匹配": date_summary,
        "报告期差异明细": pd.DataFrame(date_differences),
        "指标可用性": pd.DataFrame(indicator_results),
        "近期报告期覆盖": coverage_df,
        "近期覆盖摘要": coverage_summary,
        "报表获取错误": pd.DataFrame(
            errors,
            columns=["报表", "错误类型", "错误信息"],
        ),
    }
