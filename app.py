import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import re
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="Arca Prompt Extractor", page_icon="🔍")

# 2. Cloudflare 우회를 위한 scraper 객체 생성
scraper = cloudscraper.create_scraper()

# 3. 헤더 설정
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://arca.live/"
}

# --- 기능 함수 정의 ---

def get_latest_post_ids():
    """최신 게시글 번호 목록을 가져옵니다."""
    try:
        list_url = "https://arca.live/b/breaking"
        response = scraper.get(list_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 게시글 링크 추출 (/b/breaking/12345678 형태)
        links = soup.find_all('a', href=re.compile(r'/b/breaking/\d+'))
        post_ids = []
        for link in links:
            match = re.search(r'/b/breaking/(\d+)', link.get('href'))
            if match:
                post_ids.append(match.group(1))
        
        # 중복 제거 및 리스트 반환
        return list(dict.fromkeys(post_ids))
    except:
        return []

def extract_prompt(post_id):
    """특정 게시글에서 프롬프트를 추출합니다."""
    try:
        url = f"https://arca.live/b/breaking/{post_id}"
        response = scraper.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 아카라이브 본문 영역 선택자 (클래스명 기준)
        article = soup.select_one('.article-content') or soup.select_one('.content')
        if not article:
            return None
        
        # 텍스트 추출 및 한 줄씩 분리
        lines = article.get_text(separator='\n').split('\n')
        
        # 프롬프트 필터링 로직 (사용자 기존 설정 유지)
        # 1. 길이 50자 이상
        # 2. 영문/숫자/특수문자 비중 80% 이상
        extracted = [
            l.strip() for l in lines 
            if len(l.strip()) > 50 and (len(re.findall(r'[a-zA-Z0-9\s\(\)\,\.\:\/]', l)) / len(l.strip()) > 0.8)
        ]
        return "\n\n".join(filter(None, extracted))
    except Exception as e:
        return f"Error: {e}"

# --- UI 레이아웃 ---

st.title("🔍 Arca Prompt Extractor")

# 최신 글 번호 자동 로드
latest_ids = get_latest_post_ids()
default_id = latest_ids[0] if latest_ids else "162476331"

# 입력 영역
col1, col2 = st.columns([3, 1])
with col1:
    st.info(f"✅ 현재 채널의 최신 글 번호: **{default_id}**")
with col2:
    post_number = st.text_input("글 번호 입력", value=default_id)

# 실행 버튼
if st.button("프롬프트 추출하기", use_container_width=True):
    with st.spinner("게시글을 분석하는 중..."):
        result = extract_prompt(post_number)
        if result:
            st.session_state['result'] = result
        else:
            st.warning("조건(영문 비중 80% 이상)에 맞는 프롬프트를 찾지 못했습니다.")

# 결과 출력 및 복사 기능
if 'result' in st.session_state:
    st.divider()
    res_col1, res_col2 = st.columns([4, 1])
    
    with res_col1:
        st.subheader("✅ 추출 결과")
    
    with res_col2:
        # f-string 에러 해결을 위해 중괄호를 {{ }}로 처리
        safe_res = st.session_state['result'].replace("`", "\\`").replace("$", "\\$")
        copy_html = f"""
            <button id="cBtn" style="
                background-color: #ff4b4b; color: white; border: none; 
                padding: 8px 16px; border-radius: 5px; cursor: pointer;
                font-weight: bold; width: 100%;">Copy!</button>
            <script>
            document.getElementById('cBtn').onclick = function() {{
                const text = `{safe_res}`;
                navigator.clipboard.writeText(text).then(() => {{
                    window.parent.postMessage({{type: 'streamlit:toast', data: '복사 완료! ✅'}}, '*');
                }});
            }}
            </script>
        """
        components.html(copy_html, height=45)
    
    # 추출된 텍스트 표시
    st.text_area("Content", value=st.session_state['result'], height=400, label_visibility="collapsed")
    
