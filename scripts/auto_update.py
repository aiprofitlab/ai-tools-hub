#!/usr/bin/env python3
"""
AINAV Auto-Update Script
每週自動從多個來源抓取最新 AI 工具，更新 tools.json
"""
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

TOOLS_FILE = os.path.join(os.path.dirname(__file__), '../data/tools.json')

# ═══════════════════════════════════════════════
# 來源 1：Product Hunt AI 分類（免費，無需 API key）
# ═══════════════════════════════════════════════
def fetch_producthunt():
    """抓 Product Hunt AI 標籤近期熱門產品"""
    tools = []
    try:
        url = "https://www.producthunt.com/topics/artificial-intelligence"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; AINAV-Bot/1.0)'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # 抓取產品名稱和連結
        pattern = r'"name":"([^"]{3,50})","tagline":"([^"]{10,150})","url":"(https://www\.producthunt\.com/posts/[^"]+)"'
        matches = re.findall(pattern, html)

        for name, tagline, ph_url in matches[:10]:
            if any(kw in tagline.lower() for kw in ['ai', 'gpt', 'llm', 'ml', 'neural', 'chat', 'image', 'video', 'voice']):
                tools.append({
                    'name': name,
                    'desc_en': tagline,
                    'url': ph_url,
                    'source': 'producthunt'
                })
        print(f"ProductHunt: found {len(tools)} AI tools")
    except Exception as e:
        print(f"ProductHunt fetch failed: {e}")
    return tools


# ═══════════════════════════════════════════════
# 來源 2：There's An AI For That (theresanaiforthat.com)
# ═══════════════════════════════════════════════
def fetch_theresanai():
    """抓 There's An AI For That 最新工具"""
    tools = []
    try:
        url = "https://theresanaiforthat.com/most-saved/"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; AINAV-Bot/1.0)'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # 抓取工具名稱
        name_pattern = r'<h2[^>]*class="[^"]*ai-title[^"]*"[^>]*>([^<]+)</h2>'
        desc_pattern = r'<p[^>]*class="[^"]*description[^"]*"[^>]*>([^<]+)</p>'

        names = re.findall(name_pattern, html)[:10]
        descs = re.findall(desc_pattern, html)[:10]

        for i, name in enumerate(names):
            desc = descs[i] if i < len(descs) else ''
            tools.append({
                'name': name.strip(),
                'desc_en': desc.strip()[:150],
                'url': f"https://theresanaiforthat.com/",
                'source': 'theresanai'
            })
        print(f"TheresAnAI: found {len(tools)} tools")
    except Exception as e:
        print(f"TheresAnAI fetch failed: {e}")
    return tools


# ═══════════════════════════════════════════════
# 來源 3：GitHub Trending AI repos
# ═══════════════════════════════════════════════
def fetch_github_trending():
    """抓 GitHub Trending AI 相關 repo"""
    tools = []
    try:
        url = "https://api.github.com/search/repositories?q=topic:artificial-intelligence+topic:llm&sort=stars&order=desc&per_page=10&created:>2025-01-01"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'AINAV-Bot/1.0',
            'Accept': 'application/vnd.github.v3+json'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        for repo in data.get('items', [])[:8]:
            if repo.get('stargazers_count', 0) > 1000:
                tools.append({
                    'name': repo['name'],
                    'desc_en': repo.get('description', '')[:150] or f"GitHub: {repo['full_name']}",
                    'url': repo['html_url'],
                    'stars': repo['stargazers_count'],
                    'source': 'github'
                })
        print(f"GitHub: found {len(tools)} trending AI repos")
    except Exception as e:
        print(f"GitHub fetch failed: {e}")
    return tools


# ═══════════════════════════════════════════════
# 核心：對比新工具與現有 JSON，新增不重複的
# ═══════════════════════════════════════════════
def load_tools():
    with open(TOOLS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tools(data):
    with open(TOOLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_name(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())

def is_ai_related(name, desc):
    keywords = ['ai', 'gpt', 'llm', 'ml', 'neural', 'chat', 'image gen',
                 'video', 'voice', 'copilot', 'assistant', 'model', 'diffusion',
                 'stable', 'midjourney', 'claude', 'gemini', 'deepseek', 'agent']
    text = (name + ' ' + desc).lower()
    return any(kw in text for kw in keywords)

def categorize(name, desc):
    text = (name + ' ' + desc).lower()
    if any(kw in text for kw in ['image', 'photo', 'picture', 'art', 'draw', 'diffusion', 'midjourney', 'stable']):
        return 'AI繪圖', 'AI Image'
    if any(kw in text for kw in ['video', 'film', 'animation', 'clip']):
        return '視頻生成', 'AI Video'
    if any(kw in text for kw in ['code', 'coding', 'developer', 'program', 'ide', 'github', 'copilot']):
        return 'AI編程', 'AI Coding'
    if any(kw in text for kw in ['voice', 'speech', 'audio', 'music', 'sound', 'sing']):
        return '語音音頻', 'Audio & Voice'
    if any(kw in text for kw in ['write', 'writing', 'content', 'copy', 'translate', 'grammar']):
        return 'AI寫作', 'AI Writing'
    if any(kw in text for kw in ['meeting', 'workflow', 'automat', 'office', 'slide', 'presentation']):
        return '辦公效率', 'Productivity'
    return '大語言模型', 'Language Models'

def update_tools():
    print(f"\n{'='*50}")
    print(f"AINAV Auto-Update — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    data = load_tools()
    existing_names = {normalize_name(t['name']) for t in data['tools']}
    existing_ids = {t['id'] for t in data['tools']}
    today = datetime.now().strftime('%Y-%m-%d')
    added_count = 0

    # 抓取各來源
    new_candidates = []
    new_candidates += fetch_producthunt()
    new_candidates += fetch_github_trending()
    # new_candidates += fetch_theresanai()  # 備用

    for candidate in new_candidates:
        name = candidate.get('name', '').strip()
        desc = candidate.get('desc_en', '').strip()

        if not name or len(name) < 2:
            continue
        if not is_ai_related(name, desc):
            continue
        if normalize_name(name) in existing_names:
            print(f"  Skip (exists): {name}")
            continue

        # 生成 ID
        tool_id = re.sub(r'[^a-z0-9]', '', name.lower())[:20]
        if tool_id in existing_ids:
            tool_id += str(len(existing_ids))

        cat_zh, cat_en = categorize(name, desc)

        new_tool = {
            "id": tool_id,
            "name": name,
            "name_en": name,
            "url": candidate.get('url', '#'),
            "domain": urllib.parse.urlparse(candidate.get('url', '')).netloc or f"{tool_id}.com",
            "cat": cat_zh,
            "cat_en": cat_en,
            "desc": f"🆕 {desc[:80]}",
            "desc_en": desc[:150],
            "tags": ["new", "hot"],
            "badge": "NEW",
            "free": True,
            "zh": False,
            "added": today,
            "source": candidate.get('source', 'auto')
        }

        data['tools'].append(new_tool)
        existing_names.add(normalize_name(name))
        existing_ids.add(tool_id)
        added_count += 1
        print(f"  ✓ Added: {name} ({cat_zh})")

    # 更新時間戳
    data['last_updated'] = today

    # 標記最近7天加入的工具為 NEW
    cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    for tool in data['tools']:
        if tool.get('added', '') >= cutoff:
            if 'new' not in tool.get('tags', []):
                tool['tags'] = ['new'] + tool.get('tags', [])
            tool['badge'] = 'NEW'

    save_tools(data)
    print(f"\n✅ Done: +{added_count} new tools, total {len(data['tools'])} tools")
    print(f"📅 Last updated: {today}")

    # 輸出更新摘要供 GitHub Actions 使用
    summary_path = os.path.join(os.path.dirname(__file__), '../data/update_summary.txt')
    with open(summary_path, 'w') as f:
        f.write(f"Added {added_count} new tools on {today}\n")
        f.write(f"Total: {len(data['tools'])} tools\n")

if __name__ == '__main__':
    update_tools()
