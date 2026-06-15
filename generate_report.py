"""生成《Python数据分析与展示》项目实践报告"""
import os

import numpy as np
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

BASE_DIR = r"I:\class_project\python"
OUTPUT_DOC = os.path.join(BASE_DIR, "Python数据分析与展示_项目实践报告（2026春）.doc")
OUTPUT_DOCX = OUTPUT_DOC + "x"


def set_run_font(run, size=12, bold=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    run.font.bold = bold


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=14 if level == 1 else 12, bold=True)
    return p


def add_body(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=12)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.first_line_indent = Pt(24)
    return p


def add_code(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    p.paragraph_format.line_spacing = 1.2
    return p


def add_image(doc, filename, caption):
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        doc.add_picture(path, width=Inches(5.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        set_run_font(run, size=10.5)


def load_project_stats():
    raw = pd.read_csv(os.path.join(BASE_DIR, "hangzhou_rent_raw.csv"), encoding="utf-8-sig")
    clean = pd.read_csv(os.path.join(BASE_DIR, "hangzhou_rent_clean.csv"), encoding="utf-8-sig")

    district_stats = (
        clean.groupby("district")
        .agg(平均租金=("price", "mean"), 平均单价=("unit_price", "mean"), 样本数=("price", "count"))
        .round(2)
    )
    corr = round(clean["area"].corr(clean["price"]), 3)

    rent_type_dummy_cols = [c for c in clean.columns if c.startswith("rent_type_")]
    feature_cols = ["area", "price", "unit_price", "rooms"] + rent_type_dummy_cols
    x_scaled = StandardScaler().fit_transform(clean[feature_cols])
    pca = PCA(n_components=3, random_state=42).fit(x_scaled)
    explained = pca.explained_variance_ratio_

    max_k = int(np.sqrt(len(clean)))
    upper_k = min(max_k, len(clean) - 1)
    scores = {}
    for k in range(2, upper_k + 1):
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(x_scaled)
        scores[k] = silhouette_score(x_scaled, labels)
    best_k = max(scores, key=scores.get)

    return {
        "raw_n": len(raw),
        "clean_n": len(clean),
        "district_stats": district_stats,
        "corr": corr,
        "feature_cols": feature_cols,
        "explained": explained,
        "max_k": max_k,
        "upper_k": upper_k,
        "scores": scores,
        "best_k": best_k,
    }


def build_document(stats):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    style.font.size = Pt(12)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("《Python数据分析与展示》\n项目实践报告")
    set_run_font(run, size=16, bold=True)

    for line in [
        "报告名称：杭州市租房市场数据采集、分析与可视化",
        "专业名称：计算机科学与技术",
        "班    级：请填写班级",
        "小组组长：请填写姓名（学号）",
        "成    员：请填写姓名（学号）",
        "成    员：请填写姓名（学号）",
        "指导教师：请填写教师姓名",
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(line), size=12)

    doc.add_page_break()

    add_heading(doc, "1 引言")
    add_heading(doc, "1.1 研究背景与意义", level=2)
    add_body(
        doc,
        "随着城市化进程加快，杭州作为新一线城市，租房需求持续增长。租房者在选择房源时，"
        "需要从大量信息中比较行政区、商圈、面积、租赁方式与租金之间的关系。贝壳找房等平台虽然提供了"
        "丰富的房源信息，但数据分散在网页中，难以直接用于统计分析。本项目以杭州市租房市场为研究对象，"
        "通过网络爬虫获取公开列表数据，并结合数据清洗、特征工程、统计分析、聚类挖掘与地图可视化方法，"
        "探索不同区域租金水平、房源结构及单价差异，为租房决策和区域对比提供数据支持。"
    )

    add_heading(doc, "1.2 研究目标与主要内容", level=2)
    add_body(
        doc,
        "本项目目标包括：（1）从贝壳找房杭州租房频道抓取房源列表数据；"
        "（2）完成缺失值处理、类型转换、IQR 异常值剔除及 title 特征工程；"
        "（3）按行政区统计平均租金、平均面积和平均单价，并绘制箱线图与回归散点图；"
        "（4）基于多维特征进行 KMeans 聚类，结合 PCA 降维可视化；"
        "（5）使用 pyecharts 绘制杭州市域租金单价热力地图。"
    )

    add_heading(doc, "1.3 开发环境", level=2)
    add_body(
        doc,
        "操作系统：Windows 10；开发工具：Jupyter Notebook / Cursor；编程语言：Python 3.12；"
        "主要依赖库：requests、lxml、pandas、matplotlib、seaborn、scikit-learn、pyecharts；"
        "数据来源：https://hz.zu.ke.com/zufang/；"
        "代码仓库：https://github.com/Ckj6818/hangzhou-rent-analysis。"
    )

    add_heading(doc, "2 需求分析")
    add_heading(doc, "2.1 分析需求说明", level=2)
    add_body(
        doc,
        "业务需求围绕“帮助用户快速了解杭州各区域租房价格特征”展开，包括：多页数据采集、"
        "字段提取、数据清洗、从标题中抽取租赁方式/卧室数/朝向等结构化特征、"
        "分组统计、相关性分析、聚类分群及空间热力地图展示。"
    )

    add_heading(doc, "2.2 相关 Python 包及说明", level=2)
    add_body(
        doc,
        "requests 与 lxml 负责网页请求与 XPath 解析；pandas 负责数据清洗与统计；"
        "matplotlib 与 seaborn 负责统计图表；scikit-learn 提供 StandardScaler、PCA、KMeans 和 silhouette_score；"
        "pyecharts 负责交互式地图可视化；IPython.display 与 input 用于 Jupyter 中 Cookie 失效时的交互式续抓。"
    )

    add_heading(doc, "3 数据获取")
    add_heading(doc, "3.1 数据获取方式", level=2)
    add_body(
        doc,
        f"本项目采用 requests + lxml 抓取贝壳杭州租房列表页，原始数据共 {stats['raw_n']} 条。"
        "爬虫支持 COOKIES_POOL 多 Cookie 轮换：当请求被重定向到登录页时，程序不会直接中断，"
        "而是自动切换 Cookie 重试；若 Cookie 池全部失效，则通过 input() 挂起等待用户粘贴新 Cookie，"
        "并继续抓取剩余页数，且每页成功后立即写入 hangzhou_rent_raw.csv，避免数据丢失。"
        "翻页间隔设置为 3~6 秒随机延时，并固定 User-Agent 以降低风控触发概率。"
    )

    add_heading(doc, "3.2 关键源码", level=2)
    add_code(
        doc,
        "COOKIES_POOL = [cookie1, cookie2, cookie3]\n"
        "html = fetch_page(session, page, cookies_pool=get_active_cookies())\n"
        "if html is None:\n    new_cookie = input('请粘贴新的 Cookie >>> ')"
    )

    add_heading(doc, "3.3 数据介绍", level=2)
    add_body(
        doc,
        f"原始字段包括 title、district、biz_circle、area、price。"
        "样本覆盖拱墅区、余杭区、钱塘区、萧山区、西湖区、上城区、临安区等。"
        "部分独栋/公寓类房源存在行政区缺失或价格区间表达，需在预处理阶段进一步清洗。"
    )

    add_heading(doc, "4 数据预处理")
    add_heading(doc, "4.1 缺失值与重复值处理", level=2)
    add_body(doc, "删除包含缺失值的记录和完全重复的记录，保证后续分析字段完整。")
    add_code(doc, "df_clean = df_raw.dropna().drop_duplicates().copy()")

    add_heading(doc, "4.2 类型转换与衍生指标", level=2)
    add_body(doc, "剥离 area、price 中的中文单位，转为 float，并计算 unit_price = price / area。")
    add_code(
        doc,
        "numeric_text = re.sub(r\"[^\\d.]\", \"\", text)\n"
        "df_clean['unit_price'] = (df_clean['price'] / df_clean['area']).round(2)"
    )

    add_heading(doc, "4.3 IQR 异常值剔除", level=2)
    add_body(
        doc,
        f"采用 IQR 方法分别对 area 和 price 剔除异常值，最终保留 {stats['clean_n']} 条有效样本，"
        "保存为 hangzhou_rent_clean.csv。"
    )

    add_heading(doc, "4.4 特征工程（title 文本挖掘）", level=2)
    add_heading(doc, "4.4.1 预处理目标", level=2)
    add_body(
        doc,
        "从 title 中提取 rent_type（整租/合租/独栋）、rooms（卧室数）、orientation（朝向），"
        "并对 rent_type 进行独热编码，为后续聚类提供结构化特征。"
    )
    add_heading(doc, "4.4.2 关键源码", level=2)
    add_code(
        doc,
        "df_clean['rent_type'] = df_clean['title'].apply(extract_rent_type)\n"
        "df_clean['rooms'] = df_clean['title'].apply(extract_rooms).astype(int)\n"
        "rent_type_dummies = pd.get_dummies(df_clean['rent_type'], prefix='rent_type', dtype=int)"
    )
    add_heading(doc, "4.4.3 预处理结果", level=2)
    add_body(
        doc,
        "新增 rent_type、rooms、orientation 及 rent_type_整租、rent_type_合租 等编码列。"
        "例如“整租·望林府 3室2厅 南”可提取为整租、3 室、南向。"
    )

    add_heading(doc, "5 统计分析及结论")
    add_heading(doc, "5.1 各行政区租金指标对比", level=2)
    add_body(doc, "按行政区分组统计平均租金与平均单价，主要结果如下：")
    add_code(doc, stats["district_stats"].to_string())
    add_body(
        doc,
        "上城区、西湖区、拱墅区平均单价较高；临安区平均单价最低；"
        "萧山区样本数最多，区域内部租金差异也较明显。"
    )

    add_heading(doc, "5.2 面积与租金相关性分析", level=2)
    add_body(
        doc,
        f"面积与租金的 Pearson 相关系数约为 {stats['corr']}，呈中等强度正相关。"
        "说明面积越大，月租金总体越高，但行政区、租赁方式和商圈位置仍会显著影响租金水平。"
    )
    add_image(doc, "output_boxplot.png", "图1 杭州各行政区租金分布箱线图")
    add_image(doc, "output_scatter.png", "图2 杭州租房面积与租金相关性散点图")

    add_heading(doc, "6 数据挖掘分析")
    add_heading(doc, "6.1 KMeans 聚类与 PCA 降维", level=2)
    add_heading(doc, "6.1.1 数据挖掘目标", level=2)
    add_body(
        doc,
        f"聚类特征包括 {', '.join(stats['feature_cols'])}。"
        "先使用 StandardScaler 标准化，再用 KMeans 聚类；"
        f"K 值搜索上限设为 int(sqrt(n))={stats['max_k']}，实际搜索范围为 2~{stats['upper_k']}，"
        "以避免小样本过拟合。"
    )
    add_heading(doc, "6.1.2 关键源码", level=2)
    add_code(
        doc,
        "max_k = int(np.sqrt(len(df_cluster)))\n"
        "X_pca = PCA(n_components=3).fit_transform(X_scaled)\n"
        "best_k = argmax(silhouette_score)"
    )
    add_heading(doc, "6.1.3 建模结论", level=2)
    score_text = "；".join([f"K={k} 时轮廓系数 {v:.4f}" for k, v in stats["scores"].items()])
    add_body(
        doc,
        f"{score_text}。最优 K={stats['best_k']}。"
        f"PCA 前三主成分解释方差比例分别为 {stats['explained'][0]:.2%}、"
        f"{stats['explained'][1]:.2%}、{stats['explained'][2]:.2%}，"
        f"累计 {stats['explained'].sum():.2%}。"
        "聚类结果可区分大面积低单价、小面积高单价及主流中间价位群体。"
    )
    add_image(doc, "output_cluster_3d.png", "图3 杭州租房 KMeans 聚类 PCA 三维可视化")

    add_heading(doc, "6.2 模型评价与调优", level=2)
    add_body(
        doc,
        "本项目通过轮廓系数选择最优 K，并通过 sqrt(n) 动态限制 K 的上界，提高小样本场景下的模型严谨性。"
        "由于当前有效样本仍有限，聚类结果更适合作为方法验证；"
        "若用于答辩展示，建议配合 Cookie 池抓取更多页数据后再重新建模。"
    )

    add_heading(doc, "7 数据可视化展示")
    add_heading(doc, "7.1 统计图表", level=2)
    add_body(doc, "箱线图展示各行政区租金分布差异，散点图展示面积与租金关系及回归趋势线。")

    add_heading(doc, "7.2 杭州市租金单价热力地图", level=2)
    add_body(
        doc,
        "使用 pyecharts Map 组件，maptype='杭州'，将各行政区平均单价映射到 VisualMap 热力颜色。"
        "生成 hangzhou_rent_map.html，支持鼠标悬停查看各区单价，适合答辩现场交互展示。"
    )

    add_heading(doc, "8 分析结论及应用方向")
    add_heading(doc, "8.1 分析总结", level=2)
    add_body(
        doc,
        "（1）完成了爬虫、清洗、特征工程、统计分析、PCA+KMeans 聚类及地图可视化全流程；"
        "（2）杭州各区域租金与单价差异明显，核心城区普遍高于临安等区域；"
        "（3）title 特征工程可补充结构化信息，提升聚类解释性；"
        "（4）Cookie 池 + 手动续抓机制有效提升了爬虫稳定性；"
        "（5）PCA 三维可视化能更准确地展示高维聚类结果。"
    )

    add_heading(doc, "8.2 应用方向", level=2)
    add_body(
        doc,
        "可为租客提供区域租金参考，为平台运营提供定价对比，"
        "也可进一步结合地铁、学区、房龄等变量开展回归预测或推荐建模。"
    )

    add_heading(doc, "结束语")
    add_body(
        doc,
        "项目主要难点在于贝壳反爬、价格区间表达及小样本聚类稳定性。"
        "通过 Cookie 池轮换、Jupyter 交互式续抓、IQR 清洗、特征工程和 PCA 可视化等方法逐一解决。"
        "本次实践完整覆盖了 Python 数据分析从采集到展示的全流程，"
        "也认识到真实业务数据的质量和规模直接影响分析结论的可信度。"
    )

    doc.save(OUTPUT_DOCX)
    return OUTPUT_DOCX


def convert_to_doc(docx_path, doc_path):
    import win32com.client

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(docx_path)
    doc.SaveAs2(doc_path, FileFormat=0)
    doc.Close(False)
    word.Quit()


if __name__ == "__main__":
    stats = load_project_stats()
    docx_path = build_document(stats)
    convert_to_doc(docx_path, OUTPUT_DOC)
    if os.path.exists(OUTPUT_DOCX):
        os.remove(OUTPUT_DOCX)
    print(f"报告已更新: {OUTPUT_DOC}")
