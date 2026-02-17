import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="Arca Prompt Extractor", page_icon="🔍")

# 1. Scraper 설정 (브라우저처럼 보이도록 더 정교하게 설정)
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://arca.live/"
}

def extract_prompt(post_id):
    try:
        url = f"https://arca.live/b/breaking/{post_id}"
        response = scraper.get(url, headers=headers, timeout=10)
        
        # [디버깅] 상태 코드 확인
        if response.status_code != 200:
            return f"Error: 접속 실패 (상태코드 {response.status_code}). 보안 차단 가능성이 높습니다."
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 아카라이브 본문 및 코드블록 선택자 강화
        # .article-content 내부의 모든 텍스트와 pre/code 태그를 확인
        article = soup.select_one('.article-content')
        if not article:
            return "Error: 게시글 본문 영역을 찾을 수 없습니다."
        
        # 본문 내 모든 줄 가져오기
        lines = article.get_text(separator='\n').split('\n')
        
        extracted = []
        for l in lines:
            line = l.strip()
            if len(line) < 30: continue # 너무 짧은 줄 제외
            
            # 영문/숫자/특수문자 비율 계산
            total_char = len(line)
            eng_char = len(re.findall(r'[a-zA-Z0-9\s\(\)\,\.\:\/\[\]\_\-\<\>]', line))
            ratio = eng_char / total_char
            
            # 기준 충족 시 추가 (디버깅을 위해 비중을 70%로 살짝 낮춤)
            if ratio > 0.7:
                extracted.append(line)
        
        return "\n\n".join(extracted) if extracted else "조건에 맞는 텍스트가 없습니다."
        
    except Exception as e:
        return f"Error: {str(e)}"

# --- UI ---
st.title("🔍 Arca Prompt Extractor (Debug Mode)")

post_number = st.text_input("글 번호 입력", value="162476331")

if st.button("프롬프트 추출하기"):
    with st.spinner("분석 중..."):
        result = extract_prompt(post_number)
        
        if result.startswith("Error:"):
            st.error(result)
            st.warning("⚠️ 원인: 서버 IP 차단(403) 또는 사이트 구조 변경")
        elif result == "조건에 맞는 텍스트가 없습니다.":
            st.warning(result)
            st.info("💡 팁: 해당 글에 영문 중심의 긴 텍스트(프롬프트)가 실제 존재하는지 확인해 보세요.")
        else:
            st.session_state['result'] = result

if 'result' in st.session_state:
    st.divider()
    res_col1, res_col2 = st.columns([4, 1])
    with res_col1: st.subheader("✅ 추출 결과")
    with res_col2:
        safe_res = st.session_state['result'].replace("`", "\\`").replace("$", "\\$")
        copy_html = f"""
            <button id="cBtn" style="background:#ff4b4b;color:white;border:none;padding:8px;border-radius:5px;width:100%;cursor:pointer;font-weight:bold;">Copy</button>
            <script>
            document.getElementById('cBtn').onclick = function() {{
                navigator.clipboard.writeText(`{safe_res}`).then(() => {{
                    window.parent.postMessage({{type: 'streamlit:toast', data: '복사 완료! ✅'}}, '*');
                }});
            }}
            </script>
        """
        components.html(copy_html, height=45)
    
    st.text_area("Content", value=st.session_state['result'], height=400, label_visibility="collapsed")
