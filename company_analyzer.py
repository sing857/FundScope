import pandas as pd


def convert_cumulative_to_quarterly(
    df,
    value_columns,
):
    """
    将利润表或现金流量表的累计数据转换为单季度数据。

    原始累计字段保持不变。
    转换后的字段以 _QUARTER 结尾。
    """

    required_columns = {"REPORT_DATE", *value_columns}

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"财务数据缺少必要字段：{sorted(missing_columns)}"
        )

    result = df.copy()

    result["REPORT_DATE"] = pd.to_datetime(
        result["REPORT_DATE"],
        errors="coerce",
    )

    if result["REPORT_DATE"].isna().any():
        raise ValueError("报告日期包含无效数据。")

    if result["REPORT_DATE"].duplicated().any():
        raise ValueError("存在重复报告日期，无法进行季度转换。")

    result = result.sort_values(
        "REPORT_DATE"
    ).reset_index(drop=True)

    quarter_mapping = {
        (3, 31): 1,
        (6, 30): 2,
        (9, 30): 3,
        (12, 31): 4,
    }

    periods = {}

    for index, row in result.iterrows():
        date = row["REPORT_DATE"]

        period = quarter_mapping.get(
            (date.month, date.day)
        )

        if period is None:
            continue

        periods[(date.year, period)] = index

    for column in value_columns:

        numeric_values = pd.to_numeric(
            result[column],
            errors="coerce",
        )

        quarterly_values = pd.Series(
            float("nan"),
            index=result.index,
            dtype="float64",
        )

        for (year, quarter), index in periods.items():

            current_value = numeric_values.iloc[index]

            if pd.isna(current_value):
                continue

            if quarter == 1:
                quarterly_values.iloc[index] = current_value
                continue

            previous_index = periods.get(
                (year, quarter - 1)
            )

            if previous_index is None:
                continue

            previous_value = numeric_values.iloc[
                previous_index
            ]

            if pd.isna(previous_value):
                continue

            quarterly_values.iloc[index] = (
                current_value - previous_value
            )

        result[f"{column}_QUARTER"] = quarterly_values

    return result.sort_values(
        "REPORT_DATE",
        ascending=False,
    ).reset_index(drop=True)