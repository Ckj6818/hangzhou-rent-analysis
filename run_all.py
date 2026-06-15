"""一键运行项目全流程（预处理 → 分析 → 聚类 → 地图）"""
import re
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pyecharts import options as opts
from pyecharts.charts import Map
from pyecharts.globals import CurrentConfig
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
CurrentConfig.ONLINE = True

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

RAW_FILE = "hangzhou_rent_raw.csv"
CLEAN_FILE = "hangzhou_rent_clean.csv"
MAP_FILE = "hangzhou_rent_map.html"
BOX_PLOT = "output_boxplot.png"
SCATTER_PLOT = "output_scatter.png"
CLUSTER_3D = "output_cluster_3d.png"


def strip_numeric(value) -> float:
    if pd.isna(value):
        return float("nan")
    numeric_text = re.sub(r"[^\d.]", "", str(value).strip())
    return float(numeric_text) if numeric_text else float("nan")


def remove_iqr_outliers(df: pd.DataFrame, column: str) -> pd.DataFrame:
    q1, q3 = df[column].quantile(0.25), df[column].quantile(0.75)
    iqr = q3 - q1
    return df[(df[column] >= q1 - 1.5 * iqr) & (df[column] <= q3 + 1.5 * iqr)]


def extract_rent_type(title: str) -> str:
    text = str(title)
    for rent_type in ("整租", "合租", "独栋"):
        if rent_type in text:
            return rent_type
    return "未知"


def extract_rooms(title: str) -> int:
    text = str(title)
    match = re.search(r"(\d+)\s*室", text) or re.search(r"(\d+)\s*居室", text)
    return int(match.group(1)) if match else 1


def extract_orientation(title: str) -> str:
    text = str(title)
    for direction in ("南", "北", "东", "西"):
        if direction in text:
            return direction
    return "未知"


def normalize_district(name: str) -> str:
    name = str(name).strip()
    return name if name.endswith(("区", "县", "市")) else f"{name}区"


print("=" * 55)
print("1. 数据预处理 + 特征工程")
print("=" * 55)
df_raw = pd.read_csv(RAW_FILE, encoding="utf-8-sig")
rows_before = len(df_raw)

df_clean = df_raw.dropna().drop_duplicates().copy()
df_clean["area"] = df_clean["area"].apply(strip_numeric)
df_clean["price"] = df_clean["price"].apply(strip_numeric)
df_clean = df_clean.dropna(subset=["area", "price"])
df_clean = df_clean[(df_clean["area"] > 0) & (df_clean["price"] > 0)]
df_clean["unit_price"] = (df_clean["price"] / df_clean["area"]).round(2)
df_clean = remove_iqr_outliers(df_clean, "area")
df_clean = remove_iqr_outliers(df_clean, "price")

df_clean["rent_type"] = df_clean["title"].apply(extract_rent_type)
df_clean["rooms"] = df_clean["title"].apply(extract_rooms).astype(int)
df_clean["orientation"] = df_clean["title"].apply(extract_orientation)
rent_type_dummies = pd.get_dummies(df_clean["rent_type"], prefix="rent_type", dtype=int)
df_clean = pd.concat([df_clean, rent_type_dummies], axis=1)

df_clean.to_csv(CLEAN_FILE, index=False, encoding="utf-8-sig")
print(f"清洗前: {rows_before} 行 -> 清洗后: {len(df_clean)} 行")
print(df_clean.head())

print("\n" + "=" * 55)
print("2. 分组统计")
print("=" * 55)
district_stats = (
    df_clean.groupby("district", as_index=False)
    .agg(平均租金=("price", "mean"), 平均面积=("area", "mean"), 平均单价=("unit_price", "mean"))
    .round(2)
    .sort_values("平均租金", ascending=False)
)
print(district_stats.to_string(index=False))
print(f"面积-租金相关系数: {df_clean['area'].corr(df_clean['price']):.3f}")

print("\n" + "=" * 55)
print("3. 可视化图表")
print("=" * 55)
plt.figure(figsize=(10, 5))
sns.boxplot(data=df_clean, x="district", y="price", palette="Set2")
plt.title("杭州各行政区租金分布对比")
plt.xlabel("行政区")
plt.ylabel("租金（元/月）")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(BOX_PLOT, dpi=120)
plt.close()
print(f"箱线图已保存: {BOX_PLOT}")

plt.figure(figsize=(8, 5))
sns.regplot(data=df_clean, x="area", y="price", scatter_kws={"alpha": 0.7, "s": 50}, line_kws={"color": "red"})
plt.title("杭州租房面积与租金相关性分析")
plt.xlabel("面积（㎡）")
plt.ylabel("租金（元/月）")
plt.tight_layout()
plt.savefig(SCATTER_PLOT, dpi=120)
plt.close()
print(f"散点图已保存: {SCATTER_PLOT}")

print("\n" + "=" * 55)
print("4. KMeans 聚类 + PCA 可视化")
print("=" * 55)
rent_type_dummy_cols = [c for c in df_clean.columns if c.startswith("rent_type_")]
feature_cols = ["area", "price", "unit_price", "rooms"] + rent_type_dummy_cols
print(f"聚类特征: {feature_cols}")

X_scaled = StandardScaler().fit_transform(df_clean[feature_cols])
pca = PCA(n_components=3, random_state=42)
X_pca = pca.fit_transform(X_scaled)
explained_ratio = pca.explained_variance_ratio_
print(
    f"PCA 解释方差: PC1={explained_ratio[0]:.2%}, "
    f"PC2={explained_ratio[1]:.2%}, PC3={explained_ratio[2]:.2%}, "
    f"累计={explained_ratio.sum():.2%}"
)

max_k = int(np.sqrt(len(df_clean)))
upper_k = min(max_k, len(df_clean) - 1)
k_range = range(2, upper_k + 1)
print(f"K 搜索范围: 2 ~ {upper_k} (sqrt(n)={max_k})")

for k in k_range:
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_scaled)
    print(f"K={k}, 轮廓系数={silhouette_score(X_scaled, labels):.4f}")

best_k = max(
    k_range,
    key=lambda k: silhouette_score(
        X_scaled, KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_scaled)
    ),
)
df_clean["cluster"] = KMeans(n_clusters=best_k, random_state=42, n_init=10).fit_predict(X_scaled)
df_clean["PC1"], df_clean["PC2"], df_clean["PC3"] = X_pca[:, 0], X_pca[:, 1], X_pca[:, 2]
print(f"\n最优 K={best_k}")
print(df_clean.groupby("cluster")[["area", "price", "unit_price", "rooms"]].mean().round(2))

fig = plt.figure(figsize=(11, 8))
ax = fig.add_subplot(111, projection="3d")
colors = sns.color_palette("Set1", n_colors=best_k)
for cid, color in zip(sorted(df_clean["cluster"].unique()), colors):
    sub = df_clean[df_clean["cluster"] == cid]
    ax.scatter(sub["PC1"], sub["PC2"], sub["PC3"], c=[color], label=f"簇 {cid}", s=60, alpha=0.85)
ax.set_title("杭州租房 KMeans 聚类 PCA 三维可视化", fontsize=14)
ax.set_xlabel(f"PC1（{explained_ratio[0]:.2%}）")
ax.set_ylabel(f"PC2（{explained_ratio[1]:.2%}）")
ax.set_zlabel(f"PC3（{explained_ratio[2]:.2%}）")
cluster_handles, _ = ax.get_legend_handles_labels()
pca_handles = [
    mpatches.Patch(color="none", label=f"PC1 解释方差: {explained_ratio[0]:.2%}"),
    mpatches.Patch(color="none", label=f"PC2 解释方差: {explained_ratio[1]:.2%}"),
    mpatches.Patch(color="none", label=f"PC3 解释方差: {explained_ratio[2]:.2%}"),
]
ax.legend(handles=cluster_handles + pca_handles, title="聚类簇 / 主成分方差", loc="upper left")
plt.tight_layout()
plt.savefig(CLUSTER_3D, dpi=120)
plt.close()
print(f"PCA 3D 聚类图已保存: {CLUSTER_3D}")

print("\n" + "=" * 55)
print("5. 地图热力图")
print("=" * 55)
df_map = df_clean.copy()
df_map["district_norm"] = df_map["district"].apply(normalize_district)
map_stats = df_map.groupby("district_norm")["unit_price"].mean().round(2)
map_data = list(map_stats.items())
print(map_stats.to_string())

hangzhou_map = (
    Map(init_opts=opts.InitOpts(width="1200px", height="800px"))
    .add("平均租金单价", map_data, "杭州", is_map_symbol_show=False, label_opts=opts.LabelOpts(is_show=True))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="杭州市各行政区租金单价热力图"),
        visualmap_opts=opts.VisualMapOpts(min_=float(map_stats.min()), max_=float(map_stats.max()), is_calculable=True),
        tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}<br/>平均单价: {c} 元/㎡"),
    )
)
hangzhou_map.render(MAP_FILE)
print(f"地图已保存: {MAP_FILE}")

print("\n" + "=" * 55)
print("全部流程运行完成！")
print("=" * 55)
print("输出文件:")
print(f"  - {CLEAN_FILE}")
print(f"  - {MAP_FILE}")
print(f"  - {BOX_PLOT}")
print(f"  - {SCATTER_PLOT}")
print(f"  - {CLUSTER_3D}")
