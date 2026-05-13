import pandas as pd
from scholarly import scholarly
import os
import time
import random

# ================= 配置区 =================
SCHOLAR_ID = "0VfMvLsAAAAJ" 
# 关键词列表
KEYWORDS = [
    "robot", "hri", "hrc", "interaction", "healthcare", 
    "clinical", "design", "collaboration", "human-centred", "computing",
    "social robot", "embedded", "workflow"
]
OUTPUT_PATH = r'D:\PHD\find\Projects\HCC\hcc.xlsx'

# 如果需要代理，请在这里设置（例如使用 Clash 默认端口 7890）
# os.environ['https_proxy'] = 'http://127.0.0.1:7890'
# ==========================================

def run():
    try:
        print(f"正在定位学者 ID: {SCHOLAR_ID} ...")
        author = scholarly.search_author_id(SCHOLAR_ID)
        
        # 第一步：只获取基础文献列表（包含标题和 ID）
        print("正在拉取文献列表...")
        author = scholarly.fill(author, sections=['publications'])
        all_pubs = author['publications']
        total = len(all_pubs)
        print(f"总计找到 {total} 篇文献。开始逐篇深度扫描并抓取摘要...")

        results = []
        
        for i, pub in enumerate(all_pubs):
            title = pub['bib'].get('title', '')
            title_lower = title.lower()
            
            # 检查标题是否命中
            matched_in_title = [k for k in KEYWORDS if k.lower() in title_lower]
            
            # 为了获取摘要，必须执行 fill(pub)
            # 警告：这是最容易触发验证码的操作。我们只对标题命中的或全部进行操作？
            # 既然你需要摘要，我们这里对标题命中的文献进行深度抓取：
            
            if matched_in_title:
                print(f"[{i+1}/{total}] 发现相关文献: {title[:50]}...")
                
                try:
                    # 关键动作：请求 Google 获取该文章的详情（含摘要）
                    full_pub = scholarly.fill(pub)
                    abstract = full_pub['bib'].get('abstract', 'No abstract available')
                    
                    results.append({
                        'Title': title,
                        'Year': full_pub['bib'].get('pub_year', 'N/A'),
                        'Venue': full_pub['bib'].get('venue', 'N/A'),
                        'Matched Keywords': ", ".join(matched_in_title),
                        'Link': full_pub.get('pub_url', f"https://scholar.google.com/scholar?oi=bibs&cluster={full_pub.get('author_pub_id')}"),
                        'Abstract': abstract
                    })
                    
                    # 重点：每次抓取摘要后必须休息，否则会被封
                    wait_time = random.uniform(2, 5) # 随机休息 2-5 秒
                    time.sleep(wait_time)
                    
                except Exception as e:
                    print(f"抓取摘要失败: {e}")
                    continue
            else:
                # 如果标题没命中，可以选择跳过，或者也抓摘要看看（但这样极易被封）
                pass

        # 保存数据
        if results:
            df = pd.DataFrame(results)
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            # 使用 xlsxwriter 作为引擎可以更好地处理长文本（摘要）
            df.to_excel(OUTPUT_PATH, index=False, engine='openpyxl')
            print(f"\n任务完成！")
            print(f"筛选出 {len(results)} 篇带摘要的文献，已保存至: {OUTPUT_PATH}")
        else:
            print("\n未发现匹配关键词的文献。")

    except Exception as e:
        print(f"程序运行崩溃: {e}")

if __name__ == "__main__":
    run()