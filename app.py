import streamlit as st

from data_fetcher import fetch_fund_name, fetch_fund_nav
from analyzer import calculate_metrics
from scoring import calculate_quality_score


st.set_page_config(
    page_title="FundScope｜基金研究工作台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 视觉方向：浅色研究工作台。仅调整呈现层，不改变分析公式与数据流程。
st.markdown(
    """
    <style>
    :root {
        --fs-ink: #17263c;
        --fs-muted: #718096;
        --fs-line: #e6ebf1;
        --fs-paper: #f5f7fa;
        --fs-card: #ffffff;
        --fs-blue: #927644;
        --fs-gold: #B4975A;
        --fs-blue-soft: #f3efe5;
        --fs-green: #16836a;
        --fs-red: #c45b5b;
        --fs-amber: #a87528;
    }

    .stApp {
        background: var(--fs-paper);
        color: var(--fs-ink);
    }
    [data-testid="stHeader"] {
        background: rgba(245, 247, 250, 0.92);
    }
    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 1440px;
        padding-top: 2.1rem;
        padding-bottom: 4rem;
    }
    [data-testid="stSidebar"] {
        background: #17263c;
        border-right: 1px solid #263a55;
    }
    [data-testid="stSidebar"] * {
        color: #edf2f7;
    }
    [data-testid="stSidebar"] [data-testid="stTextInput"] input {
        background: #223650;
        border: 1px solid #405875;
        color: #ffffff;
    }
    [data-testid="stSidebar"] [data-testid="stTextInput"] input:focus {
        border-color: #B4975A;
        box-shadow: 0 0 0 1px #B4975A;
    }
    [data-testid="stSidebar"] .stButton button {
        background: #B4975A;
        color: #17263c;
        border: 0;
        font-weight: 650;
        min-height: 2.7rem;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: #C7AD76;
        color: #17263c;
        border: 0;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #b9c7d8 !important;
    }
    [data-testid="stSidebar"] .stButton button:disabled {
        background: #58687b;
        color: #d8e0e8;
    }
    [data-testid="stSidebar"] hr {
        border-color: #344a65;
    }

    h1, h2, h3, h4 {
        color: var(--fs-ink);
        letter-spacing: -0.025em;
    }
    h1 { font-weight: 720; }
    h2 { font-weight: 680; }
    h3 { font-weight: 650; }
    p, li, label, [data-testid="stMarkdownContainer"] {
        color: #34445a;
    }
    [data-testid="stCaptionContainer"] p {
        color: var(--fs-muted);
    }
    [data-testid="stMetric"] {
        background: var(--fs-card);
        border: 1px solid var(--fs-line);
        border-radius: 12px;
        padding: 16px 18px;
        min-height: 112px;
        box-shadow: 0 2px 8px rgba(23, 38, 60, 0.025);
    }
    [data-testid="stMetricLabel"] p {
        color: var(--fs-muted) !important;
        font-size: 0.82rem;
        font-weight: 550;
    }
    [data-testid="stMetricValue"] {
        color: var(--fs-ink);
        font-weight: 680;
        font-variant-numeric: tabular-nums;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.78rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--fs-card);
        border-color: var(--fs-line) !important;
        border-radius: 14px;
    }
    .fs-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0 0 1.6rem 0;
    }
    .fs-brand-mark {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        border-radius: 11px;
        background: #223650;
        color: #B4975A;
        font-size: 21px;
        font-weight: 700;
    }
    .fs-brand-name {
        color: var(--fs-ink);
        font-size: 1.3rem;
        line-height: 1.1;
        font-weight: 760;
        letter-spacing: -0.035em;
    }
    .fs-brand-sub {
        color: var(--fs-muted);
        font-size: 0.76rem;
        margin-top: 4px;
        letter-spacing: 0.02em;
    }
    .fs-eyebrow {
        color: var(--fs-blue);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }
    .fs-page-title {
        color: var(--fs-ink);
        font-size: clamp(1.8rem, 3vw, 2.55rem);
        line-height: 1.15;
        font-weight: 760;
        letter-spacing: -0.045em;
        margin: 0;
    }
    .fs-page-subtitle {
        color: var(--fs-muted);
        font-size: 0.98rem;
        margin-top: 0.65rem;
        margin-bottom: 1.5rem;
    }
    .fs-section {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 1.9rem 0 0.9rem 0;
        padding-bottom: 0.55rem;
        border-bottom: 1px solid var(--fs-line);
    }
    .fs-section-index {
        color: var(--fs-blue);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.08em;
    }
    .fs-section-title {
        color: var(--fs-ink);
        font-size: 1.08rem;
        font-weight: 700;
    }
    .fs-fund-title {
        color: var(--fs-ink);
        font-size: 1.55rem;
        font-weight: 740;
        letter-spacing: -0.035em;
        margin-bottom: 0.15rem;
    }
    .fs-fund-code {
        color: var(--fs-muted);
        font-size: 0.83rem;
        font-variant-numeric: tabular-nums;
    }
    .fs-score-number {
        color: var(--fs-gold);
        font-size: 2.65rem;
        line-height: 1;
        font-weight: 760;
        letter-spacing: -0.05em;
        font-variant-numeric: tabular-nums;
    }
    .fs-score-denom {
        color: var(--fs-muted);
        font-size: 0.95rem;
        font-weight: 550;
    }
    .fs-score-label {
        color: var(--fs-muted);
        font-size: 0.78rem;
        font-weight: 650;
        letter-spacing: 0.08em;
        margin-bottom: 0.7rem;
    }
    .fs-note {
        color: var(--fs-muted);
        font-size: 0.82rem;
        line-height: 1.65;
    }
    .fs-footer {
        border-top: 1px solid var(--fs-line);
        padding-top: 1rem;
        margin-top: 2rem;
        color: var(--fs-muted);
        font-size: 0.78rem;
    }
    div[data-testid="stProgressBar"] > div > div {
        background: var(--fs-blue);
    }
    .stButton button, .stDownloadButton button {
        border-radius: 8px;
        font-weight: 620;
    }
    .stTextArea textarea {
        border-radius: 9px;
        border-color: var(--fs-line);
        background: #ffffff;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid var(--fs-line);
        border-radius: 10px;
        overflow: hidden;
    }
    hr { border-color: var(--fs-line); }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── 侧边栏：产品标识与分析入口 ─────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="fs-brand">
            <div class="fs-brand-mark">F</div>
            <div>
                <div class="fs-brand-name" style="color:#ffffff">FundScope</div>
                <div class="fs-brand-sub" style="color:#b5c3d3">个人金融研究工作台</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("#### 基金分析")
    st.caption("输入基金代码，获取历史净值并计算收益与风险指标。")
    fund_code = st.text_input(
        "公募基金代码",
        value="005827",
        max_chars=6,
        placeholder="例如：005827",
    )
    run_analysis = st.button("开始分析", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown("**当前版本**")
    st.caption("基金历史表现分析 · 初步规则评分")
    st.markdown("---")
    st.caption("数据来自公开数据接口。分析结果仅供研究参考，不构成投资建议。")


# ── 页面标题 ──────────────────────────────────────────────
st.markdown('<div class="fs-eyebrow">PERSONAL INVESTMENT RESEARCH</div>', unsafe_allow_html=True)
st.markdown('<div class="fs-page-title">基金分析工作台</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fs-page-subtitle">以历史净值为基础，观察收益表现、风险暴露与长期稳定性。</div>',
    unsafe_allow_html=True,
)

# 使用 session_state 保存分析结果，避免普通页面重跑清空结果。
if "fundscope_analysis" not in st.session_state:
    st.session_state["fundscope_analysis"] = None
if "fundscope_analysis_code" not in st.session_state:
    st.session_state["fundscope_analysis_code"] = None


# ── 开始分析：保留原有数据获取和计算流程 ───────────────────
if run_analysis:
    if len(fund_code) != 6 or not fund_code.isdigit():
        st.error("请输入有效的六位基金代码。")
    else:
        try:
            with st.spinner("正在获取基金信息与历史净值……"):
                fund_name = fetch_fund_name(fund_code)
                df = fetch_fund_nav(fund_code)
                df = df.set_index("date")
                metrics = calculate_metrics(df["nav"])
                score_result = calculate_quality_score(metrics)

            st.session_state["fundscope_analysis"] = {
                "fund_name": fund_name,
                "fund_code": fund_code,
                "df": df,
                "metrics": metrics,
                "score_result": score_result,
            }
            st.session_state["fundscope_analysis_code"] = fund_code
        except Exception as exc:
            st.error(f"分析失败：{exc}")
            st.warning(
                "请检查基金代码、网络连接、数据接口状态，以及分析指标是否存在缺失值。"
            )


analysis = st.session_state["fundscope_analysis"]


def section_heading(index, title):
    st.markdown(
        f'<div class="fs-section"><span class="fs-section-index">{index}</span>'
        f'<span class="fs-section-title">{title}</span></div>',
        unsafe_allow_html=True,
    )


if analysis is not None:
    fund_name = analysis["fund_name"]
    analyzed_code = analysis["fund_code"]
    df = analysis["df"]
    metrics = analysis["metrics"]
    score_result = analysis["score_result"]

    st.markdown(
        f'<div class="fs-fund-title">{fund_name}</div>'
        f'<div class="fs-fund-code">基金代码　{analyzed_code}</div>',
        unsafe_allow_html=True,
    )

    # 01 历史质量评估
    section_heading("01", "历史质量评估")
    score = score_result["基金质量分"]
    score_status = score_result["评分状态"]

    if score is not None:
        score_col, explain_col = st.columns([1, 2], gap="large")
        with score_col:
            with st.container(border=True):
                st.markdown('<div class="fs-score-label">基金历史质量分</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<span class="fs-score-number">{score}</span>'
                    '<span class="fs-score-denom"> / 100</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{score_status}**")
        with explain_col:
            with st.container(border=True):
                st.markdown("**评分说明**")
                st.write(score_result["评分说明"])

        details = score_result.get("评分明细", {})
        if details:
            st.markdown("**评分构成**")
            detail_cols = st.columns(len(details))
            for col, (name, value) in zip(detail_cols, details.items()):
                with col:
                    st.metric(name, f"{value:.1f}")
                    st.progress(max(0.0, min(1.0, value / 100)))
    else:
        st.warning("当前数据不足，暂时无法计算基金质量分。")
        st.write(score_result["评分说明"])

    # 02 收益与风险指标
    section_heading("02", "收益与风险概览")
    metric_cols = st.columns(3, gap="medium")
    metric_cols[0].metric("区间收益率", f"{metrics['区间收益率']:.2%}")
    metric_cols[1].metric("年化收益率", f"{metrics['年化收益率']:.2%}")
    metric_cols[2].metric("最大回撤", f"{metrics['最大回撤']:.2%}")

    metric_cols_2 = st.columns(3, gap="medium")
    metric_cols_2[0].metric("年化波动率", f"{metrics['年化波动率']:.2%}")
    metric_cols_2[1].metric("夏普比率", f"{metrics['夏普比率']:.3f}")
    metric_cols_2[2].metric("索提诺比率", f"{metrics['索提诺比率']:.3f}")

    # 03 关键指标解读
    section_heading("03", "关键指标解读")
    insight_a, insight_b = st.columns(2, gap="large")
    annual_return = metrics["年化收益率"]
    max_drawdown = metrics["最大回撤"]
    volatility = metrics["年化波动率"]
    sharpe = metrics["夏普比率"]

    with insight_a:
        with st.container(border=True):
            st.markdown("**收益表现**")
            if annual_return > 0:
                st.write(
                    f"历史年化收益率为 {annual_return:.2%}，"
                    "按照当前计算方法折算后的年化收益水平为正。"
                )
            elif annual_return < 0:
                st.write(
                    f"历史年化收益率为 {annual_return:.2%}，"
                    "该统计区间内的年化收益水平为负。"
                )
            else:
                st.write("当前统计区间的年化收益率为零。")
            st.markdown("**风险控制**")
            st.write(
                f"历史最大回撤为 {max_drawdown:.2%}。它反映净值从此前高点"
                "下跌到随后低点的最大幅度，不代表未来可能出现的最大损失。"
            )
    with insight_b:
        with st.container(border=True):
            st.markdown("**波动特征**")
            st.write(
                f"历史年化波动率为 {volatility:.2%}。波动率越高，通常说明"
                "净值变化越明显，但不能单独用它判断基金好坏。"
            )
            st.markdown("**风险调整后收益**")
            st.write(
                f"夏普比率为 {sharpe:.3f}，衡量基金承担单位总波动所获得的超额收益。"
                "计算结果会受到无风险利率设定和历史区间影响。"
            )

    # 04 最大回撤详情
    section_heading("04", "最大回撤详情")
    dd_cols = st.columns(3, gap="medium")
    dd_cols[0].metric("回撤峰值日期", str(metrics["回撤峰值日期"]))
    dd_cols[1].metric("回撤谷底日期", str(metrics["回撤谷底日期"]))
    dd_cols[2].metric("峰值至谷底", f"{int(metrics['峰值至谷底天数'])} 天")

    if metrics["回撤是否恢复"]:
        st.success(f"历史最大回撤已恢复，恢复日期为 {metrics['回撤恢复日期']}。")
    else:
        st.warning("截至当前数据结束日期，历史最大回撤尚未恢复。")

    # 05 历史净值走势
    section_heading("05", "历史单位净值走势")
    with st.container(border=True):
        st.line_chart(
            df[["nav"]].rename(columns={"nav": "单位净值"}),
            x_label="日期",
            y_label="单位净值",
        )

    # 06 数据质量
    section_heading("06", "数据质量与覆盖范围")
    quality_cols = st.columns(3, gap="medium")
    quality_cols[0].metric("数据起始日期", str(df.index.min().date()))
    quality_cols[1].metric("数据结束日期", str(df.index.max().date()))
    quality_cols[2].metric("有效净值记录", f"{len(df)} 条")

    quality_cols_2 = st.columns(3, gap="medium")
    quality_cols_2[0].metric("原始记录数", str(metrics["原始记录数"]))
    quality_cols_2[1].metric("无效记录数", str(metrics["无效记录数"]))
    quality_cols_2[2].metric("数据覆盖天数", f"{metrics['数据覆盖天数']} 天")

    if metrics["无效记录数"] > 0:
        st.warning(
            "部分原始记录无效，分析时已按引擎规则处理。建议检查数据来源和记录完整性。"
        )
    else:
        st.info(
            "本次分析未发现被引擎判定为无效的净值记录；这不代表数据源绝对准确或完整。"
        )

    # 07 历史明细
    section_heading("07", "历史净值明细")
    with st.container(border=True):
        st.dataframe(df.sort_index(ascending=False), width="stretch")

else:
    with st.container(border=True):
        st.markdown("### 从一只基金开始")
        st.write("在左侧输入六位基金代码并点击「开始分析」，即可查看历史收益、风险和净值数据。")
        st.caption("示例代码：005827。首次获取数据时需要等待公开数据接口返回结果。")


# 08 假设与反向检验：保留现有功能，不伪装为已接入的 AI 分析。
section_heading("08", "假设与反向检验")
st.caption("提出一个观点，明确它需要哪些证据，以及可能在哪些地方出错。")
with st.expander("查看可供思考的问题"):
    st.markdown(
        """
        - 如果这只基金再下跌 20%，风险敞口会如何变化？
        - 如果过去的历史表现不能代表未来，当前结论还剩下什么？
        - 如果行业未来三年高速增长，基金是否一定受益？
        - 如果 FundScope 的结论错了，最可能错在哪里？
        """
    )

user_hypothesis = st.text_area(
    "你的假设",
    placeholder="例如：我认为这只基金未来三年可能反弹，因为它投资的行业正在复苏……",
    height=105,
    key="fundscope_hypothesis",
)
challenge_mode = st.radio(
    "检验方式",
    [
        "检查 FundScope 分析中的漏洞",
        "双向检验：同时检查系统结论与我的假设",
    ],
    horizontal=True,
)
run_hypothesis = st.button("提交假设", type="secondary", key="run_hypothesis")

if run_hypothesis:
    if not user_hypothesis.strip():
        st.warning("请先输入一个假设。")
    else:
        st.info(
            "已收到你的假设。目前反向检验引擎尚未接入，暂时不能生成经过数据验证的结论。"
        )
        st.write("**你的假设：**")
        st.write(user_hypothesis)
        st.write(f"**检验方式：** {challenge_mode}")
        if analysis is None:
            st.warning("当前没有已保存的基金分析结果。请先完成基金分析。")
        else:
            st.write(f"**当前分析基金：** {analysis['fund_name']}（{analysis['fund_code']}）")
        st.caption(
            "当前不会虚构支持证据、反面证据或预测概率。该区域暂作为研究假设记录入口。"
        )


# 09 数据说明与使用限制
section_heading("09", "数据说明与使用限制")
st.markdown(
    '<div class="fs-note">数据来源：东方财富相关公开数据接口（通过 AKShare 获取）。'
    '数据可能存在延迟、缺失或口径差异，请以基金管理人公布的信息为准。</div>',
    unsafe_allow_html=True,
)
st.info(
    "本工具仅用于历史数据分析，不构成投资建议。历史表现不代表未来收益。"
    "当前基金质量分属于初步规则评分，尚未经过充分历史回测验证，也未针对不同基金类型建立独立标准。"
    "本工具尚未提供经过验证的当前投资吸引力评分。收益计算基于当前获取的单位净值，"
    "可能未完整反映分红再投资的影响。"
)

st.markdown(
    '<div class="fs-footer">FUNDSCOPE · PERSONAL FINANCIAL RESEARCH WORKSPACE</div>',
    unsafe_allow_html=True,
)
