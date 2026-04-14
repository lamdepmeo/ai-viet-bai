import streamlit as st
import pandas as pd
import requests
import time
import json
import os
from bs4 import BeautifulSoup
from docx import Document
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="SEO & GEO Content Engineer", layout="wide", page_icon="✍️")

# --- CUSTOM CSS (Premium Dark Mode & Glassmorphism) ---
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #ffffff;
    }
    .stApp {
        background: transparent;
    }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button {
        background: linear-gradient(45deg, #00c6ff, #0072ff);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 198, 255, 0.4);
    }
    .status-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    h1, h2, h3 {
        background: linear-gradient(to right, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {
        'AI': '',
        'SERP': '',
        'Linkup': ''
    }

if 'articles' not in st.session_state:
    st.session_state.articles = {}

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.title("⚙️ Cấu hình")
    st.session_state.api_keys['AI'] = st.text_input("AI API Key (chiasegpu)", type="password")
    st.session_state.api_keys['SERP'] = st.text_input("Serp API Key (serper.dev)", type="password")
    st.session_state.api_keys['Linkup'] = st.text_input("Linkup API Key", type="password")
    
    st.divider()
    st.info("💡 Mẹo: Nhập đầy đủ API Key để bắt đầu chạy workflow.")

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🚀 Writer", "📜 Rules Editor", "📁 History"])

# --- TAB 2: RULES EDITOR ---
with tab2:
    st.header("Chỉnh sửa Quy tắc SEO & GEO")
    rules_path = "seo_geo_rules.md"
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_content = f.read()
    else:
        rules_content = "# SEO & GEO Rules\n\n(Tạo quy tắc của bạn tại đây)"
    
    updated_rules = st.text_area("Nội dung Markdown", value=rules_content, height=500)
    if st.button("Lưu quy tắc"):
        with open(rules_path, "w", encoding="utf-8") as f:
            f.write(updated_rules)
        st.success("Đã cập nhật quy tắc!")

# --- CORE FUNCTIONS ---

def truncate_text(text, max_chars=4000):
    if not isinstance(text, str):
        text = str(text)
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[Nội dung đã bị cắt bớt để bảo toàn token]..."
    return text

def extract_json(text):
    try:
        # Xử lý Markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        # Tìm dấu ngoặc nhọn đầu và cuối
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        return text.strip()
    except:
        return text.strip()

def repair_json(broken_json):
    if not broken_json:
        return ""
    stack = []
    in_string = False
    escaped = False
    
    # Dọn dẹp sơ bộ
    broken_json = broken_json.strip()
    
    for char in broken_json:
        if char == '\\' and in_string:
            escaped = not escaped
            continue
        if char == '"' and not escaped:
            in_string = not in_string
        if not in_string:
            if char in '{[':
                stack.append(char)
            elif char in '}]':
                if stack:
                    if (char == '}' and stack[-1] == '{') or (char == ']' and stack[-1] == '['):
                        stack.pop()
        escaped = False
    
    if in_string:
        broken_json += '"'
    
    while stack:
        opener = stack.pop()
        broken_json += '}' if opener == '{' else ']'
    return broken_json


def get_serp_results(keyword):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": st.session_state.api_keys['SERP'], "Content-Type": "application/json"}
    data = json.dumps({"q": keyword, "num": 10})
    response = requests.post(url, headers=headers, data=data)
    return response.json().get('organic', [])

def scrape_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract from main/article or fallback to body
        content = soup.find('main') or soup.find('article') or soup.find('body')
        return content.get_text(separator=' ', strip=True)[:5000] # Limit to 5000 chars
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

def call_ai(prompt, system_prompt="You are an expert SEO Content Engineer."):
    url = "https://llm.chiasegpu.vn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.session_state.api_keys['AI']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-sonnet-4.6",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4000
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90)
        if response.status_code != 200:
            st.error(f"⚠️ API Error ({response.status_code}): {response.text[:300]}")
            return f"Error: {response.text[:200]}"
        
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        st.error("⚠️ Lỗi: Thời gian phản hồi từ AI quá lâu (Timeout).")
        return "Error: Timeout"
    except requests.exceptions.HTTPError as e:
        if response.status_code in [502, 504]:
            st.error("⚠️ Lỗi Gateway (502/504): Có thể Payload quá lớn hoặc Server AI đang bảo trì.")
        return f"Error: {str(e)}"
    except Exception as e:
        st.error(f"⚠️ Lỗi hệ thống: {str(e)}")
        return f"Error: {str(e)}"

def call_ai_stream(prompt, system_prompt="You are an expert SEO Content Engineer."):
    url = "https://llm.chiasegpu.vn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.session_state.api_keys['AI']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-sonnet-4.6",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": True,
        "max_tokens": 4000
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90, stream=True)
        if response.status_code != 200:
            st.error(f"⚠️ API Error ({response.status_code}): {response.text[:300]}")
            yield f"Error: {response.text[:200]}"
            return

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    content = decoded_line[6:]
                    if content == "[DONE]":
                        break
                    try:
                        json_data = json.loads(content)
                        chunk = json_data['choices'][0]['delta'].get('content')
                        if chunk:
                            yield chunk
                    except:
                        continue
    except Exception as e:
        st.error(f"⚠️ Stream Error: {str(e)}")
        yield f"Error: {str(e)}"

def linkup_research(keyword):
    url = "https://api.linkup.so/v1/search"
    headers = {
        "Authorization": f"Bearer {st.session_state.api_keys['Linkup']}",
        "Content-Type": "application/json"
    }
    data = {
        "q": f"scientific evidence for {keyword}",
        "depth": "standard",
        "outputType": "sourcedAnswer"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# --- TAB 1: WRITER ---
with tab1:
    st.header("Trình tạo nội dung SEO")
    
    mode = st.radio("Chế độ vận hành:", ["🚀 Tự động (Full Workflow)", "✍️ Thủ công (Dán dữ liệu)"], horizontal=True)

    keywords = []
    
    if mode == "🚀 Tự động (Full Workflow)":
        col1, col2 = st.columns([1, 1])
        with col1:
            manual_keywords = st.text_area("Nhập danh sách từ khóa (mỗi dòng 1 từ)", height=150)
        with col2:
            uploaded_file = st.file_uploader("Hoặc tải lên file CSV/XLSX", type=["csv", "xlsx"])

        if manual_keywords:
            keywords = [k.strip() for k in manual_keywords.split('\n') if k.strip()]
        if uploaded_file:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            target_col = next((c for c in df.columns if c.lower() in ['keyword', 'từ khóa', 'tu khoa']), df.columns[0])
            keywords.extend(df[target_col].tolist())
    else:
        # MANUAL MODE INPUTS
        kw_manual = st.text_input("Từ khóa chính (Keyword)")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            research_manual = st.text_area("Dữ liệu nghiên cứu (Linkup/Scientific Data)", height=250, placeholder="Dán dữ liệu nghiên cứu khoa học tại đây...")
        with col_m2:
            competitor_manual = st.text_area("Nội dung đối thủ (Competitor Content)", height=250, placeholder="Dán nội dung đối thủ hoặc ý tưởng tại đây...")
        
        if kw_manual:
            keywords = [kw_manual.strip()]

    if st.button("🚀 Bắt đầu Viết bài"):
        if not all(st.session_state.api_keys.values()):
            st.error("Vui lòng điền đầy đủ API Key trong Sidebar.")
        elif not keywords:
            st.warning("Vui lòng nhập từ khóa.")
        else:
            for kw in keywords:
                if kw not in st.session_state.articles:
                    st.session_state.articles[kw] = {
                        "status": "processing", 
                        "research": {}, 
                        "outline": [], 
                        "content": "", 
                        "metrics": "", 
                        "meta_title": "", 
                        "meta_description": ""
                    }
                
                with st.expander(f"⚙️ Đang xử lý: {kw}", expanded=True):
                    status_ui = st.status(f"Bắt đầu xử lý: {kw}")
                    
                    if mode == "🚀 Tự động (Full Workflow)":
                        # 1. SERP
                        status_ui.update(label="🔍 Đang tìm kiếm SERP...")
                        serp_results = get_serp_results(kw)
                        urls = [r['link'] for r in serp_results[:3]]
                        
                        # 2. Scraping
                        status_ui.update(label="📄 Đang cào dữ liệu đối thủ...")
                        comp_content = ""
                        for url in urls:
                            scraped = scrape_url(url)
                            comp_content += f"\n--- Source: {url} ---\n" + truncate_text(scraped, 500)
                        comp_content = truncate_text(comp_content, 1500)
                        
                        # 3. Research
                        status_ui.update(label="🧬 Đang nghiên cứu Linkup (Scientific)...")
                        linkup_json = linkup_research(kw)
                        answer = linkup_json.get('answer', '')
                        sources = linkup_json.get('sources', [])
                        source_text = "\n".join([f"- {s.get('name')}: {s.get('snippet','')}" for s in sources[:5]])
                        raw_linkup = f"Tóm tắt: {answer}\n\nChi tiết: {source_text}"
                        
                        st.session_state.articles[kw]['research'] = {
                            "urls": urls,
                            "answer": answer,
                            "raw": linkup_json
                        }
                        research_data = truncate_text(raw_linkup, 2000)
                        competitor_content = comp_content
                        
                        # HIỂN THỊ DỮ LIỆU NGHIÊN CỨU NGAY LẬP TỨC
                        with st.expander("🔍 Dữ liệu nghiên cứu (SERP & Linkup)", expanded=False):
                            st.markdown("**🔗 Nguồn đối thủ (SERP):**")
                            for url in urls:
                                st.write(f"- {url}")
                            st.divider()
                            st.markdown("**🧬 Tóm tắt nghiên cứu Linkup:**")
                            st.write(answer if answer else "Không có tóm tắt.")
                            st.divider()
                            st.markdown("**🛠️ Raw Linkup JSON (Debug):**")
                            st.json(linkup_json)
                    else:
                        status_ui.update(label="📝 Đang chuẩn bị dữ liệu thủ công...")
                        research_data = truncate_text(research_manual, 3000)
                        competitor_content = truncate_text(competitor_manual, 3000)
                        st.session_state.articles[kw]['research'] = {"answer": "Nhập thủ công", "raw": research_manual}

                    # 4. Analysis & Outline
                    status_ui.update(label="📝 Đang lập dàn ý (Outline)...")
                    with open(rules_path, "r", encoding="utf-8") as f:
                        raw_rules = f.read()
                        rules = truncate_text(raw_rules, 3000)
                    
                    mini_rules = "SEO Standards: Use HTML, direct answers, Entity-first, chunking (200-500 words per section)."
                    if "## 6. Quick Reference Card" in raw_rules:
                        mini_rules = raw_rules[raw_rules.find("## 6. Quick Reference Card"):]
                    mini_rules = truncate_text(mini_rules, 800)

                    st.session_state.articles[kw]['metrics'] = f"Rules({len(rules)}), Research({len(research_data)}), Competitors({len(competitor_content)})"
                    
                    outline_prompt = f"Rules: {rules}\n\nResearch Data: {research_data}\n\nCompetitor Ideas: {competitor_content}\n\nKeyword: {kw}\n\nGenerate a CONCISE article outline and SEO metadata in JSON format: {{'meta_title': 'SEO Meta Title (<60 chars)', 'meta_description': 'SEO Meta Description (<160 chars)', 'outline': [{{'title': '...', 'points': [...]}}]}}"
                    outline_json_str = st.write_stream(call_ai_stream(truncate_text(outline_prompt, 10000)))
                    
                    try:
                        clean_json = extract_json(outline_json_str)
                        repaired_json = repair_json(clean_json)
                        outline_data = json.loads(repaired_json)
                        st.session_state.articles[kw]['outline'] = outline_data.get('outline', [])
                        st.session_state.articles[kw]['meta_title'] = outline_data.get('meta_title', '')
                        st.session_state.articles[kw]['meta_description'] = outline_data.get('meta_description', '')
                    except Exception as e:
                        st.error(f"Lỗi dàn ý cho {kw}. Vui lòng thử lại.")
                        continue
                    
                    # 5. Writing (Chunking)
                    status_ui.update(label="✍️ Đang viết bài...")
                    for i, heading in enumerate(st.session_state.articles[kw]['outline']):
                        status_ui.update(label=f"✍️ Đang viết phần {i+1}: {heading['title']}")
                        write_prompt = f"SEO Rules: {mini_rules}\n\nHeading: {heading['title']}\n\nPoints: {heading['points']}\n\nPrev: {st.session_state.articles[kw]['content'][-300:]}\n\nTASK: Write a deeply insightful SEO section in HTML (target 600-800 words). Finish all tags."
                        
                        chunk = st.write_stream(call_ai_stream(truncate_text(write_prompt, 4000)))
                        st.session_state.articles[kw]['content'] += f"\n\n{chunk}"
                    
                    st.session_state.articles[kw]['status'] = "complete"
                    status_ui.update(label="✅ Hoàn thành!", state="complete")

    # --- DISPLAY PERSISTENT RESULTS ---
    if st.session_state.articles:
        st.divider()
        st.header("📝 Kết quả đã tạo")
        if st.button("🧹 Xóa tất cả kết quả"):
            st.session_state.articles = {}
            st.rerun()

        for kw, data in st.session_state.articles.items():
            with st.expander(f"📄 Bài viết: {kw} ({data['status']})", expanded=(data['status'] == "complete")):
                if data['research']:
                    st.info(f"📊 Debug Metrics: {data['metrics']}")
                    with st.expander("🔍 Chi tiết nghiên cứu"):
                        st.write(data['research'].get('answer', "N/A"))
                        if 'raw' in data['research']:
                            st.json(data['research']['raw'])
                
                if data['meta_title']:
                    st.success(f"**SEO Meta Title:** {data['meta_title']}")
                    st.info(f"**SEO Meta Description:** {data['meta_description']}")
                
                st.markdown("### Nội dung bài viết")
                st.html(data['content'])
                
                if data['status'] == "complete":
                    col_ex1, col_ex2 = st.columns(2)
                    # Word Export
                    doc = Document()
                    doc.add_heading(data['meta_title'] if data['meta_title'] else kw, 0)
                    doc.add_paragraph(f"Meta Description: {data['meta_description']}")
                    doc.add_paragraph("-" * 20)
                    doc.add_paragraph(data['content'])
                    bio = BytesIO()
                    doc.save(bio)
                    col_ex1.download_button(label=f"📥 Tải .docx ({kw})", data=bio.getvalue(), file_name=f"{kw}.docx")
                    # HTML Export
                    html_full = f"<html><head><title>{data['meta_title']}</title><meta name='description' content='{data['meta_description']}'></head><body>{data['content']}</body></html>"
                    col_ex2.download_button(label=f"📥 Tải .html ({kw})", data=html_full, file_name=f"{kw}.html")

# --- TAB 3: HISTORY ---
with tab3:
    st.header("Lịch sử bài viết")
    st.write("Dữ liệu sẽ được lưu tại đây trong các phiên tiếp theo.")
