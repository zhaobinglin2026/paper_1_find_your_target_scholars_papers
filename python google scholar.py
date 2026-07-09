import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

# ==================== 配置 ====================
PROFILE_URL = "https://scholar.google.com/citations?hl=zh-CN&user=NLWSjCIAAAAJ&view_op=list_works&sortby=pubdate"
OUTPUT_FILE = r"D:\PHD\find\Projects\Alex\maedche_all_papers.json"
MAX_WAIT = 20   # 最大等待时间（秒）
MIN_DELAY = 3   # 最小延迟（秒）
MAX_DELAY = 7   # 最大延迟（秒）

# ==================== 初始化浏览器（有界面 + 反检测） ====================
def init_driver():
    chrome_options = Options()

    # 去掉 headless，使用有界面浏览器
    # chrome_options.add_argument("--headless")

    # 反检测关键参数
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)

    # 执行 CDP 命令，进一步隐藏 webdriver 痕迹
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined}); Object.defineProperty(navigator, "plugins", {get: () => [1, 2, 3, 4, 5]}); window.chrome = { runtime: {} };'
    })

    return driver

# ==================== 随机延迟 ====================
def random_delay():
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)

# ==================== 展开所有论文 ====================
def expand_all_papers(driver):
    print("开始加载论文列表...")
    driver.get(PROFILE_URL)
    random_delay()

    # 等待页面加载完成
    try:
        WebDriverWait(driver, MAX_WAIT).until(
            EC.presence_of_element_located((By.ID, "gsc_a_b"))
        )
        print("页面加载成功！")
    except TimeoutException:
        print("页面加载超时，可能是需要人工验证")
        print("请在浏览器中完成验证，完成后按 Enter 键继续...")
        input()
        # 验证后再检查一次页面是否加载成功
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "gsc_a_b"))
            )
            print("页面加载成功！")
        except:
            print("页面仍未加载，程序退出")
            return False

    # 循环点击"展开"按钮，直到没有更多内容
    expand_count = 0
    max_expands = 100  # 安全上限

    while expand_count < max_expands:
        try:
            # 查找"展开"按钮
            more_btn = driver.find_element(By.ID, "gsc_bpf_more")

            # 检查按钮是否可用（未禁用）
            if more_btn.get_attribute("disabled"):
                print(f"已到达最后一页，共展开 {expand_count} 次")
                break

            # 滚动到按钮位置再点击
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", more_btn)
            time.sleep(1)

            # 使用 JavaScript 点击，更稳定
            driver.execute_script("arguments[0].click();", more_btn)
            expand_count += 1
            print(f"第 {expand_count} 次展开...")

            # 等待新内容加载
            time.sleep(3)
            random_delay()

        except NoSuchElementException:
            print("没有找到展开按钮，可能已加载全部内容")
            break
        except ElementNotInteractableException:
            print("展开按钮不可交互，可能已到达底部")
            break
        except Exception as e:
            print(f"展开时出错: {e}")
            break

    if expand_count >= max_expands:
        print(f"已达到安全上限 {max_expands} 次展开")

    return True

# ==================== 提取所有论文标题 ====================
def extract_all_titles(driver):
    print("提取所有论文标题...")
    papers = []

    rows = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
    print(f"共找到 {len(rows)} 篇论文")

    for idx, row in enumerate(rows):
        try:
            title_elem = row.find_element(By.CLASS_NAME, "gsc_a_at")
            title = title_elem.text.strip()

            # 年份
            year = None
            try:
                year_elem = row.find_element(By.CSS_SELECTOR, "td.gsc_a_y .gsc_a_h")
                year_text = year_elem.text.strip()
                if year_text and year_text.isdigit():
                    year = int(year_text)
            except:
                pass

            papers.append({
                "title": title,
                "year": year
            })

        except Exception as e:
            print(f"提取第 {idx+1} 篇论文标题时出错: {e}")
            continue

    return papers

# ==================== 主程序 ====================
def main():
    print("=" * 50)
    print("Google Scholar 论文标题爬虫")
    print("作者: Alexander Maedche")
    print("=" * 50)

    driver = init_driver()

    try:
        success = expand_all_papers(driver)
        if not success:
            print("加载论文列表失败，程序退出")
            return

        papers = extract_all_titles(driver)
        total = len(papers)
        print(f"\n共提取 {total} 篇论文标题")

        if total == 0:
            print("未提取到任何论文，请检查页面是否正常加载")
            return

        # 保存为 JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 完成！数据已保存至: {OUTPUT_FILE}")

        # 显示前10条预览
        print("\n预览前10条：")
        for i, p in enumerate(papers[:10]):
            year_str = str(p['year']) if p['year'] else "N/A"
            title_display = p['title'][:70] + "..." if len(p['title']) > 70 else p['title']
            print(f"  {i+1}. [{year_str}] {title_display}")

        # 年份分布统计
        print("\n年份分布：")
        year_counts = {}
        unknown_count = 0
        for p in papers:
            y = p['year']
            if y is None:
                unknown_count += 1
            else:
                year_counts[y] = year_counts.get(y, 0) + 1
        for y in sorted(year_counts.keys(), reverse=True)[:10]:
            print(f"  {y}: {year_counts[y]} 篇")
        if unknown_count > 0:
            print(f"  未知年份: {unknown_count} 篇")

    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按 Enter 键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    main()
