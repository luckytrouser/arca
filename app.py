import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import re
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="Arca Prompt Extractor", page_icon="🔍")

# Cloudflare 우회를 위한 scraper 객체 생성
scraper = cloudscraper.create_scraper()

# 헤더 설정
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://arca.live/"
}

def get_latest_post_ids():
    try:
        # 아카라이브 정보 게시판(breaking) 리스트
        list_url = "https://arca.live/b/breaking"
        response = scraper.get(list_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 게시글 번호 추출 패턴
        links = soup.find_all('a', href=re.compile(r'/b/breaking/\d+'))
        post_ids = []
        for link in links:
            match = re.search(r'/b/breaking/(\d+)', link.get('href'))
            if match: post_ids.append(match.group(1))
        
        return list(dict.fromkeys(post_ids))
    except:
        return []

def extract_prompt(post_id):
    try:
        url = f"https://arca.live/b/breaking/{post_id}"
        response = scraper.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 아카라이브 본문 영역 선택자
        article = soup.select_one('.article-content') or soup.select_one('.content')
        if not article: return None
        
        lines = article.get_text(separator='\n').split('\n')
        
        # 사용자 정의 프롬프트 필터링 (영문/숫자 비중 80% 이상, 50자 이상)
        extracted = [
            l.strip() for l in lines 
            if len(l.strip()) > 50 and (len(re.findall(r'[a-zA-Z0-9\s\(\)\,\.\:\/]', l)) / len(l.strip()) > 0.8)
        ]
        return "\n\n".join(filter(None, extracted))
    except Exception as e:
        return f"Error: {e}"

# --- UI ---
st.title("🔍 Arca Prompt Extractor")

latest_ids = get_latest_post_ids()
default_id = latest_ids[0] if latest_ids else "162476331"

col1, col2 = st.columns([3, 1])
with col1:
    st.info(f"✅ 최신 탐색 번호: {default_id}")
with col2:
    post_number = st.text_input("글 번호", value=default_id)

if st.button("추출 시작", use_container_width=True):
    result = extract_prompt(post_number)
    if result:
        st.session_state['result'] = result
    else:
        st.warning("조건에 맞는 프롬프트를 찾지 못했습니다.")

if 'result' in st.session_state:
    st.divider()
    res_col1, res_col2 = st.columns([4, 1])
    with res_col1: st.subheader("추출 결과")
    with res_col2:
        # 복사 버튼 스크립트
        safe_res = st.session_state['result'].replace("`", "\\`").replace("$", "\\$")
        copy_html = f"""
            <button id="cBtn" style="background:#ff4b4b;color:white;border:none;padding:8px;border-radius:5px;width:100%;cursor:pointer;">Copy</button>
            <script>
            document.getElementById('cBtn').onclick = function() {{
                navigator.clipboard.writeText(`{safe_res}`).then(() => {{
                    window.parent.postMessage({{type: 'streamlit:toast', data: '복사 완료!'}, '*');
                }});
            }}
            </script>
        """
        components.html(copy_html, height=45)
    
    st.text_area("Content", value=st.session_state['result'], height=400, label_visibility="collapsed")
