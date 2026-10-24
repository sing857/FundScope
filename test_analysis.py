from data_fetcher import fetch_fund_nav
from analyzer import calculate_metrics
import math


def main():
    fund_code = "005827"
    df = fetch_fund_nav(fund_code)
    df = df.set_index("date")
    metrics = calculate_metrics(df["nav"])

    print("=" * 45)
    print(f"基金代码：{fund_code}")
    print(f"数据起始日期：{df.index.min().date()}")
    print(f"数据结束日期：{df.index.max().date()}")
    print(f"有效净值记录：{len(df)} 条")
    print("=" * 45)
    print("\n基金收益与风险分析：")

    for name, value in metrics.items():
        if math.isfinite(value):
            if name == "夏普比率":
                print(f"{name}：{value:.3f}")
            else:
                print(f"{name}：{value:.2%}")
        else:
            print(f"{name}：暂不可计算")


if __name__ == "__main__":
    main()
