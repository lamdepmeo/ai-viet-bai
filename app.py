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
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

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
    return response.json().get('results', "No research found.")

# --- TAB 1: WRITER ---
with tab1:
    st.header("Trình tạo nội dung SEO")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        manual_keywords = st.text_area("Nhập danh sách từ khóa (mỗi dòng 1 từ)", height=150)
    with col2:
        uploaded_file = st.file_uploader("Hoặc tải lên file CSV/XLSX", type=["csv", "xlsx"])

    keywords = []
    if manual_keywords:
        keywords = [k.strip() for k in manual_keywords.split('\n') if k.strip()]
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        # Try to find 'Keyword' or 'Từ khóa' column
        target_col = next((c for c in df.columns if c.lower() in ['keyword', 'từ khóa', 'tu khoa']), df.columns[0])
        keywords.extend(df[target_col].tolist())

    if st.button("🚀 Bắt đầu Viết bài"):
        if not all(st.session_state.api_keys.values()):
            st.error("Vui lòng điền đầy đủ API Key trong Sidebar.")
        elif not keywords:
            st.warning("Vui lòng nhập từ khóa.")
        else:
            for kw in keywords:
                with st.expander(f"⚙️ Đang xử lý: {kw}", expanded=True):
                    status = st.status(f"Bắt đầu xử lý: {kw}")
                    
                    # 1. SERP
                    status.update(label="🔍 Đang tìm kiếm SERP...")
                    serp_results = get_serp_results(kw)
                    urls = [r['link'] for r in serp_results[:3]] # Process top 3 for speed
                    
                    # 2. Scraping
                    status.update(label="📄 Đang cào dữ liệu đối thủ...")
                    competitor_content = ""
                    for url in urls:
                        competitor_content += f"\n--- Source: {url} ---\n" + scrape_url(url)
                    
                    # 3. Research
                    status.update(label="🧬 Đang nghiên cứu Linkup (Scientific)...")
                    research_data = linkup_research(kw)
                    
                    # 4. Analysis & Outline
                    status.update(label="📝 Đang lập dàn ý (Outline)...")
                    with open(rules_path, "r", encoding="utf-8") as f:
                        rules = f.read()
                    
                    outline_prompt = f"Rules: {rules}\n\nResearch Data: {research_data}\n\nCompetitor Ideas: {competitor_content[:2000]}\n\nKeyword: {kw}\n\nGenerate article outline in JSON format: {{'outline': [{{'title': '...', 'points': [...]}}]}}"
                    outline_json_str = call_ai(outline_prompt)
                    # Simple cleanup if AI returns extra text
                    outline_data = json.loads(outline_json_str[outline_json_str.find('{'):outline_json_str.rfind('}')+1])
                    
                    # 5. Writing (Chunking)
                    status.update(label="✍️ Đang viết bài (Chunking mode)...")
                    full_content = ""
                    for i, heading in enumerate(outline_data['outline']):
                        status.update(label=f"✍️ Đang viết phần {i+1}: {heading['title']}")
                        write_prompt = f"Rules: {rules}\n\nHeading: {heading['title']}\n\nContext: {heading['points']}\n\nPrevious Content for flow: {full_content[-500:]}\n\nWrite extensive HTML content for this heading."
                        chunk = call_ai(write_prompt)
                        full_content += f"\n\n{chunk}"
                    
                    status.update(label="✅ Hoàn thành!", state="complete")
                    
                    # Display Preview
                    st.markdown("### Preview Content")
                    st.html(full_content)
                    
                    # Export Buttons
                    col_ex1, col_ex2 = st.columns(2)
                    
                    # WORD EXPORT
                    doc = Document()
                    doc.add_heading(kw, 0)
                    # Simple HTML to Word (very basic conversion)
                    doc.add_paragraph(full_content)
                    bio = BytesIO()
                    doc.save(bio)
                    col_ex1.download_button(label="📥 Tải file .docx", data=bio.getvalue(), file_name=f"{kw}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    
                    # HTML EXPORT
                    col_ex2.download_button(label="📥 Tải file .html", data=full_content, file_name=f"{kw}.html", mime="text/html")

# --- TAB 3: HISTORY ---
with tab3:
    st.header("Lịch sử bài viết")
    st.write("Dữ liệu sẽ được lưu tại đây trong các phiên tiếp theo.")
