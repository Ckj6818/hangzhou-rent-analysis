"""非交互式执行 hangzhou_rent_scraper.ipynb（跳过 input 挂起）"""
import json
import os
import sys
import traceback

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

NOTEBOOK = "hangzhou_rent_scraper.ipynb"
OUTPUT = "hangzhou_rent_scraper_executed.ipynb"
RAW_FILE = "hangzhou_rent_raw.csv"

# 替换 Cell 3：不调用 input()，优先读取已有 raw 数据
SCRAPER_CELL_OVERRIDE = f'''
import os
from IPython.display import clear_output

session = requests.Session()
session.headers.update(build_headers())

active_cookies = get_active_cookies()
if active_cookies:
    apply_cookie(session, random.choice(active_cookies))

session.get(BASE_URL + "/", headers=build_headers(), timeout=20)
time.sleep(random.uniform(1.5, 2.5))

all_records: list[dict] = []
last_url = f"{{BASE_URL}}/"

# 若已有 raw 文件且非空，直接加载（避免无 Cookie 时卡在 input）
if os.path.exists(RAW_FILE) and os.path.getsize(RAW_FILE) > 100:
    _df_existing = pd.read_csv(RAW_FILE, encoding="utf-8-sig")
    all_records = _df_existing.to_dict("records")
    print(f"已加载现有 {{RAW_FILE}}，共 {{len(all_records)}} 条（跳过在线爬虫）")
else:
    page = 1
    while page <= MAX_PAGES:
        print(f"正在抓取第 {{page}}/{{MAX_PAGES}} 页 ...")
        html = fetch_page(session, page, referer=last_url, cookies_pool=get_active_cookies())
        if html is None:
            print(f"  !! 第 {{page}} 页被风控拦截，停止翻页（已保留 {{len(all_records)}} 条）")
            break
        page_records = parse_page(html)
        print(f"  -> 本页解析到 {{len(page_records)}} 条房源")
        all_records.extend(page_records)
        save_raw_records(all_records)
        last_url = build_page_url(page)
        if page < MAX_PAGES:
            time.sleep(random.uniform(3.0, 6.0))
        page += 1

print(f"\\n共抓取 {{len(all_records)}} 条记录")
if all_records:
    print(f"已自动保存至 {{RAW_FILE}}")
'''


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with open(NOTEBOOK, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    code_idx = 0
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        # 第 4 个 code cell 是爬虫主循环（Cell 3 in notebook）
        if code_idx == 2:  # 第 3 个 code cell = 爬虫主循环
            cell.source = SCRAPER_CELL_OVERRIDE
        code_idx += 1

    ep = ExecutePreprocessor(timeout=300, kernel_name="python3", allow_errors=False)
    print(f"开始执行 Notebook: {NOTEBOOK}")
    print("=" * 55)

    try:
        ep.preprocess(nb, {"metadata": {"path": os.getcwd()}})
        status = "success"
    except Exception as e:
        status = "failed"
        print(f"\n执行失败: {e}")
        traceback.print_exc()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print("=" * 55)
    print(f"执行状态: {status}")
    print(f"输出 Notebook: {OUTPUT}")

    # 打印各 cell 输出摘要
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        outputs = cell.get("outputs", [])
        if outputs:
            print(f"\n--- Code Cell {i} 输出 ---")
            for out in outputs[:3]:
                if out.get("output_type") == "stream":
                    text = out.get("text", "")
                    if isinstance(text, list):
                        text = "".join(text)
                    print(text[:800])
                elif out.get("output_type") == "error":
                    print("ERROR:", out.get("ename"), out.get("evalue"))

    return 0 if status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
