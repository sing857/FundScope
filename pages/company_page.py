import streamlit as st
import pandas as pd

from data_fetcher import fetch_stock_info
from services.ct_service import analyze_company_service


# ==============================
# 页面样式
# ==============================

st.markdown("""
<style>
    .company-heading {
        color: #17263C;
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .company-subtitle {
        color: #718096;
        font-size: 14px;
        margin-bottom: 18px;
    }

    .section-heading {
        color: #17263C;
        font-size: 19px;
        font-weight: 650;
        border-left: 4px solid #B4975A;
        padding-left: 11px;
        margin: 18px 0 14px 0;
    }

    .company-name {
        color: #17263C;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .company-meta {
        color: #718096;
        font-size: 14px;
    }

    .company-label {
        color: #718096;
        font-size: 13px;
        margin-bottom: 5px;
    }

    .company-value {
        color: #17263C;
        font-size: 23px;
        font-weight: 650;
    }

    .company-unit {
        color: #927644;
        font-size: 13px;
    }

    div[data-testid="stMetric"] {
        background: #F5F7FA;
        border: 1px solid #E5E9EF;
        padding: 15px 17px;
        border-radius: 9px;
    }

    div[data-testid="stMetricLabel"] {
        color: #718096;
    }

    div[data-testid="stMetricValue"] {
        color: #17263C;
    }

    .gold-line {
        border: none;
        border-top: 1px solid #D8C9A8;
        margin: 18px 0;
    }

    /* 小狗加载动画 */

    .dog-loader {
        background: #F5F7FA;
        border: 1px solid #E5E9EF;
        border-radius: 12px;
        padding: 18px 22px;
        margin: 16px 0;
    }

    .dog-track {
        position: relative;
        height: 42px;
        border-bottom: 2px dashed #D8C9A8;
        overflow: hidden;
    }

    .running-dog {
        position: absolute;
        left: 0;
        bottom: 3px;
        font-size: 30px;
        animation: dog-run 1.8s linear infinite;
    }

    @keyframes dog-run {
        0% {
            left: 0;
        }

        100% {
            left: calc(100% - 38px);
        }
    }

    .dog-status {
        color: #17263C;
        font-size: 14px;
        font-weight: 600;
        margin-top: 12px;
    }

    .dog-caption {
        color: #718096;
        font-size: 12px;
        margin-top: 4px;
    }

    @media (prefers-reduced-motion: reduce) {
        .running-dog {
            animation: none;
            left: 45%;
        }
    }

</style>
""", unsafe_allow_html=True)


# ==============================
# 页面标题
# ==============================

st.markdown(
    '<div class="company-heading">企业研究</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="company-subtitle">'
    'COMPANY RESEARCH · 企业基本面与财务分析'
    '</div>',
    unsafe_allow_html=True,
)


# ==============================
# 企业搜索
# ==============================

with st.form("company_search"):

    col1, col2 = st.columns([4, 1])

    with col1:
        symbol = st.text_input(
            "股票代码",
            placeholder="输入六位股票代码，例如 600519",
            max_chars=6,
        )

    with col2:
        st.write("")
        submitted = st.form_submit_button(
            "查询企业",
            use_container_width=True,
        )


# ==============================
# 查询执行与加载动画
# ==============================

if submitted:

    symbol = symbol.strip()

    if len(symbol) != 6 or not symbol.isdigit():

        st.error("请输入有效的六位股票代码。")

    else:

        loader = st.empty()

        def show_loading(message):

            loader.markdown(
                f"""
                <div class="dog-loader">
                    <div class="dog-track">
                        <div class="running-dog">🐕</div>
                    </div>

                    <div class="dog-status">
                        {message}
                    </div>

                    <div class="dog-caption">
                        FundScope 正在处理，请稍候……
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 获取企业基本信息

        try:

            show_loading("正在获取企业基本信息……")

            info = fetch_stock_info(symbol)

            st.session_state["company_info"] = info
            st.session_state.pop("company_error", None)

        except Exception as exc:

            st.session_state.pop("company_info", None)
            st.session_state["company_error"] = str(exc)

        # 获取财务分析结果

        try:

            show_loading(
                "正在并发获取三张财务报表，并进行财务分析……"
            )

            analysis = analyze_company_service(symbol)

            st.session_state["company_analysis"] = analysis
            st.session_state.pop(
                "company_analysis_error",
                None,
            )

            if analysis["status"].get("basic") != "success":

                st.session_state["company_analysis_error"] = (
                    analysis["errors"].get("basic")
                    or "企业基础财务分析未能完成。"
                )

        except Exception as exc:

            st.session_state.pop("company_analysis", None)

            st.session_state["company_analysis_error"] = str(exc)

        # 查询结束

        loader.markdown(
            """
            <div class="dog-loader">
                <div class="dog-track">
                    <div class="running-dog">🐕</div>
                </div>

                <div class="dog-status">
                    研究任务处理完成。
                </div>

                <div class="dog-caption">
                    正在展示企业研究结果……
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================
# 查询结果
# ==============================

if st.session_state.get("company_error"):

    st.error(st.session_state["company_error"])


if st.session_state.get("company_analysis_error"):

    st.error(
        "企业财务分析获取失败："
        + st.session_state["company_analysis_error"]
    )


info = st.session_state.get("company_info")
analysis = st.session_state.get("company_analysis")


# ==============================
# 企业概览与市场规模
# ==============================

if info:

    st.markdown(
        '<hr class="gold-line">',
        unsafe_allow_html=True,
    )

    # 企业身份

    st.markdown(
        '<div class="section-heading">企业概览</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])

    with col1:

        st.markdown(
            f'<div class="company-name">{info["name"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="company-meta">'
            f'{info["symbol"]}　|　'
            f'{info.get("industry") or "行业信息暂无"}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:

        st.markdown(
            '<div class="company-label">上市日期</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="company-value" style="font-size:17px;">'
            f'{info.get("listing_date") or "暂无数据"}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<hr class="gold-line">',
        unsafe_allow_html=True,
    )

    # 市场规模

    st.markdown(
        '<div class="section-heading">市场规模</div>',
        unsafe_allow_html=True,
    )

    market_cap = info.get("market_cap")
    latest_price = info.get("latest_price")

    try:

        market_cap = float(market_cap) / 100000000
        market_cap_display = f"{market_cap:,.2f}"

    except (TypeError, ValueError):

        market_cap_display = "暂无数据"

    try:

        latest_price_display = f"{float(latest_price):,.2f}"

    except (TypeError, ValueError):

        latest_price_display = "暂无数据"

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "总市值",
            market_cap_display
            if market_cap_display == "暂无数据"
            else f"{market_cap_display} 亿元",
        )

    with col2:

        st.metric(
            "最新股价",
            latest_price_display
            if latest_price_display == "暂无数据"
            else f"{latest_price_display} 元",
        )

    st.caption(
        "市场数据来自东方财富接口，可能存在延迟；"
        "市值由原始数据换算为亿元。"
    )

else:

    st.info("输入股票代码，开始企业研究。")


# ==============================
# 经营与成长
# ==============================

if analysis:

    basic = analysis.get("basic")
    history = analysis.get("history")
    trend = analysis.get("trend")

    if basic and analysis["status"].get("basic") == "success":

        st.markdown(
            '<hr class="gold-line">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-heading">经营与成长</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            f'财务报告期：{basic.get("报告期", "暂无数据")}｜'
            f'{basic.get("数据口径说明", "")}'
        )

        profitability = basic.get("盈利能力", {})
        growth = basic.get("成长性", {})

        revenue = profitability.get("营业收入（元，累计）")
        net_profit = profitability.get("归母净利润（元，累计）")

        revenue_yoy = growth.get("营业收入同比增长率（%）")
        profit_yoy = growth.get("归母净利润同比增长率（%）")

        def format_yi(value):

            if value is None:
                return "暂无数据"

            return f"{value / 100000000:,.2f} 亿元"

        def format_percent(value):

            if value is None:
                return "暂无数据"

            return f"{value:.2f}%"

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "营业收入（累计）",
                format_yi(revenue),
                format_percent(revenue_yoy),
            )

        with col2:

            st.metric(
                "归母净利润（累计）",
                format_yi(net_profit),
                format_percent(profit_yoy),
            )

        st.caption(
            "注：营业收入与归母净利润为报告期累计值；"
            "下方趋势图采用单季度同比口径。"
        )

        # 单季度经营趋势

        if trend is not None and not trend.empty:

            st.markdown("#### 单季度同比变化")

            chart_data = trend[
                [
                    "报告期",
                    "营业收入单季度同比",
                    "归母净利润单季度同比",
                ]
            ].copy()

            chart_data["报告期"] = pd.to_datetime(
                chart_data["报告期"],
                errors="coerce",
            )

            chart_data = chart_data.dropna(
                subset=["报告期"]
            )

            chart_data = chart_data.tail(8)

            chart_data = chart_data.set_index("报告期")

            chart_data = chart_data * 100

            chart_data.columns = [
                "营业收入同比（%）",
                "归母净利润同比（%）",
            ]

            st.line_chart(
                chart_data,
                use_container_width=True,
            )

            st.caption(
                "单季度同比根据相邻季度累计财务数据还原，"
                "再与上年同期比较。"
            )

            with st.expander("查看最近8个季度的详细数据"):

                display_data = chart_data.reset_index()

                display_data["报告期"] = (
                    display_data["报告期"].dt.strftime("%Y-%m-%d")
                )

                st.dataframe(
                    display_data,
                    use_container_width=True,
                    hide_index=True,
                )

        else:

            st.warning("暂无可用的季度趋势数据。")

    else:

        st.warning("企业基础财务分析暂不可用。")


# ==============================
# 财务健康
# ==============================

if analysis:
    basic = analysis.get("basic") or {}
    if basic and analysis.get("status", {}).get("basic") == "success":
        safety = basic.get("财务安全", {}) or {}
        cash_quality = basic.get("现金流质量", {}) or {}

        st.markdown('<hr class="gold-line">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-heading">财务健康</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f'报告期：{basic.get("报告期", "暂无数据")}｜'
            '资产负债表指标为期末值；现金流指标为报告期累计值。'
        )

        def financial_yi(value):
            if value is None:
                return "暂无数据"
            return f"{value / 100000000:,.2f} 亿元"

        def financial_percent(value):
            if value is None:
                return "暂无数据"
            return f"{value * 100:.2f}%"

        def financial_ratio(value):
            if value is None:
                return "暂无数据"
            return f"{value:.2f} 倍"

        # 第一层：核心财务指标
        st.markdown("#### 核心财务指标")
        debt_ratio = safety.get("资产负债率")
        current_ratio = safety.get("流动比率")
        quick_ratio = safety.get("速动比率")
        cash_ratio = safety.get("现金比率")
        operating_cashflow = cash_quality.get("经营活动现金流量净额（元，累计）")
        cash_profit_ratio = cash_quality.get("经营现金流／归母净利润")

        metric_rows = [
            ("资产负债率", financial_percent(debt_ratio)),
            ("流动比率", financial_ratio(current_ratio)),
            ("速动比率", financial_ratio(quick_ratio)),
            ("现金比率", financial_ratio(cash_ratio)),
            ("经营现金流（累计）", financial_yi(operating_cashflow)),
            ("经营现金流／归母净利润", financial_ratio(cash_profit_ratio)),
        ]
        for start in range(0, len(metric_rows), 3):
            columns = st.columns(3)
            for column, (label, value) in zip(columns, metric_rows[start:start + 3]):
                with column:
                    st.metric(label, value)

        # 第二层：资产与负债结构
        st.markdown("#### 财务结构")
        asset_col, liability_col = st.columns(2)

        current_assets_ratio = safety.get("流动资产占总资产比例")
        noncurrent_assets_ratio = safety.get("非流动资产占总资产比例")
        current_liabilities_ratio = safety.get("流动负债占总负债比例")
        noncurrent_liabilities_ratio = safety.get("非流动负债占总负债比例")

        with asset_col:
            st.markdown("**资产结构**")
            st.metric("流动资产", financial_yi(safety.get("流动资产（元，期末）")))
            if current_assets_ratio is not None:
                st.progress(min(max(current_assets_ratio, 0.0), 1.0))
                st.caption(f"占总资产 {financial_percent(current_assets_ratio)}")
            st.metric("非流动资产", financial_yi(safety.get("非流动资产（元，期末）")))
            if noncurrent_assets_ratio is not None:
                st.progress(min(max(noncurrent_assets_ratio, 0.0), 1.0))
                st.caption(f"占总资产 {financial_percent(noncurrent_assets_ratio)}")

        with liability_col:
            st.markdown("**负债结构**")
            st.metric("流动负债", financial_yi(safety.get("流动负债（元，期末）")))
            if current_liabilities_ratio is not None:
                st.progress(min(max(current_liabilities_ratio, 0.0), 1.0))
                st.caption(f"占总负债 {financial_percent(current_liabilities_ratio)}")
            st.metric("非流动负债", financial_yi(safety.get("非流动负债（元，期末）")))
            if noncurrent_liabilities_ratio is not None:
                st.progress(min(max(noncurrent_liabilities_ratio, 0.0), 1.0))
                st.caption(f"占总负债 {financial_percent(noncurrent_liabilities_ratio)}")

        st.markdown("#### 重要资产项目")
        asset_col1, asset_col2 = st.columns(2)
        with asset_col1:
            st.metric("货币资金", financial_yi(safety.get("货币资金（元，期末）")))
        with asset_col2:
            st.metric("存货", financial_yi(safety.get("存货（元，期末）")))

        with st.expander("查看财务指标口径与计算依据"):
            st.markdown(
                "- **资产负债率**：总负债 ÷ 总资产。\n"
                "- **流动比率**：流动资产 ÷ 流动负债。\n"
                "- **速动比率**：（流动资产－存货－预付款项）÷ 流动负债。\n"
                "- **现金比率**：货币资金 ÷ 流动负债。\n"
                "- **经营现金流／归母净利润**：经营活动现金流量净额 ÷ 归母净利润。"
            )
            st.caption(
                "注意：货币资金可能包含受限资金，不能直接等同于可随时动用的现金；"
                "速动比率采用扣除存货和预付款项的口径。指标应结合行业特征、"
                "企业经营模式及历史变化判断，不单独作为安全结论。"
            )


# ==============================
# 风险与核查
# ==============================

if analysis:
    alerts = analysis.get("alerts") or {}
    quality = analysis.get("quality") or {}
    status = analysis.get("status") or {}

    st.markdown('<hr class="gold-line">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-heading">风险与核查</div>',
        unsafe_allow_html=True,
    )

    if status.get("alerts") == "success" and alerts:
        alert_count = alerts.get("异常数量")
        alert_items = alerts.get("异常提示") or []
        quality_warnings = alerts.get("数据质量警告") or []

        if alert_count == 0 and not alert_items and not quality_warnings:
            st.success(
                f'规则检查完成：截至 {alerts.get("检查报告期", "暂无数据")}，'
                f'检查 {alerts.get("检查期数", "—")} 期，未触发当前规则提示。'
            )
        else:
            st.warning(
                f'规则检查发现 {alert_count if alert_count is not None else len(alert_items)} 项提示。'
            )
            for item in alert_items:
                if isinstance(item, dict):
                    st.warning("；".join(f"{key}：{value}" for key, value in item.items()))
                else:
                    st.warning(str(item))
            for item in quality_warnings:
                st.info(str(item))

        with st.expander("查看规则适用范围与结果说明"):
            if alerts.get("适用范围说明"):
                st.write(alerts["适用范围说明"])
            if alerts.get("结果说明"):
                st.write(alerts["结果说明"])
    elif status.get("alerts") != "success":
        st.warning("风险规则检查未能完成，请结合下方数据质量信息判断分析完整性。")
    else:
        st.info("当前没有可展示的风险规则结果。")

    st.markdown("#### 进一步核查方向")
    st.markdown(
        "- 结合行业特点与财务报表附注，判断资产、负债及现金流结构是否合理。\n"
        "- 核对应收账款的账龄、主要客户集中度及期后回款情况。\n"
        "- 检查存货构成、周转情况、跌价准备及存货变动原因。\n"
        "- 核实有息负债规模、期限结构、利息支出及受限资产。\n"
        "- 将经营现金流与净利润、销售回款及营运资本变化结合分析。"
    )

    st.markdown("#### 财报数据质量")
    coverage = quality.get("近期覆盖摘要") or {}
    if isinstance(coverage, dict) and coverage:
        coverage_cols = st.columns(3)
        coverage_items = [
            ("近期目标季度数", coverage.get("目标季度数")),
            ("三表共同覆盖", coverage.get("三表共同覆盖季度数")),
            ("未共同覆盖", coverage.get("未被三表共同覆盖季度数")),
        ]
        for column, (label, value) in zip(coverage_cols, coverage_items):
            with column:
                st.metric(label, "暂无数据" if value is None else str(value))
        if coverage.get("检查状态"):
            st.caption(f'覆盖检查状态：{coverage.get("检查状态")}')

    def render_quality_detail(title, value):
        if value is None:
            st.caption(f"{title}：暂无数据")
        elif isinstance(value, pd.DataFrame):
            if value.empty:
                st.caption(f"{title}：无记录")
            else:
                st.dataframe(value, use_container_width=True, hide_index=True)
        elif isinstance(value, dict):
            st.json(value)
        elif isinstance(value, (list, tuple)):
            if not value:
                st.caption(f"{title}：无记录")
            else:
                for entry in value:
                    st.write(f"- {entry}")
        else:
            st.text(str(value))

    quality_sections = [
        ("报表概况", "报表概况"),
        ("关键字段质量", "字段质量"),
        ("报告期匹配", "报告期匹配"),
        ("报告期差异明细", "报告期差异明细"),
        ("近期报表覆盖", "近期报告期覆盖"),
        ("指标可用性", "指标可用性"),
        ("重复内容检查", "重复内容检查"),
        ("报表获取错误", "报表获取错误"),
    ]
    for title, key in quality_sections:
        with st.expander(title):
            render_quality_detail(title, quality.get(key))

    st.caption(
        "风险规则是辅助筛查工具：未触发规则不代表企业不存在风险；"
        "触发提示也不等同于违规或财务造假。最终判断仍需结合原始报表、附注和外部证据。"
    )