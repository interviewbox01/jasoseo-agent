import gradio as gr
from llm_functions import classify_industry

# 예제 데이터
example_companies = ["삼성전자", "신한은행", "쿠팡", "아모레퍼시픽", "현대건설", "하이브", "토스", "넥슨", "삼성바이오로직스", "HMM"]
example_jobs = ["경영기획", "온라인마케팅", "HRM(인사운영)", "백엔드 개발", "해외영업", "데이터 분석", "영업", "마케팅", "기획", "개발"]

def create_tag_cards(tags):
    """
    분류된 태그들을 카드 형태로 표시하는 HTML 생성
    """
    if not tags:
        return "<div style='text-align: center; color: #6B7280; padding: 20px;'>분류를 실행해주세요</div>"
    
    # 태그명 매핑
    tag_mapping = {
        "platform-portal": "플랫폼/포털",
        "e-commerce": "이커머스",
        "game": "게임",
        "it-solution-si": "IT솔루션/SI",
        "o2o-vertical": "O2O/버티컬",
        "ai-data": "AI/데이터",
        "cloud-saas": "클라우드/SaaS",
        "fintech": "핀테크",
        "semiconductor": "반도체",
        "electronics-home": "가전/전자제품",
        "automotive-mobility": "자동차/모빌리티",
        "battery": "2차전지",
        "display": "디스플레이",
        "heavy-industry-shipbuilding": "중공업/조선",
        "steel-metal": "철강/금속",
        "bank": "은행",
        "securities": "증권",
        "insurance": "보험",
        "card": "카드",
        "asset-management": "자산운용",
        "dept-store-mart": "백화점/마트",
        "convenience-store": "편의점",
        "fmcg-beverage": "FMCG/식음료",
        "fashion-beauty": "패션/뷰티",
        "duty-free": "면세점",
        "pharma-new-drug": "제약/신약개발",
        "bio-cmo": "바이오/CMO",
        "medical-device": "의료기기",
        "digital-healthcare": "디지털헬스케어",
        "entertainment": "엔터테인먼트",
        "contents-video": "콘텐츠/영상제작",
        "ad-agency": "광고대행사",
        "webtoon-webnovel": "웹툰/웹소설",
        "broadcasting-press": "방송/언론",
        "construction-engineering": "건설/엔지니어링",
        "realestate-development": "부동산개발",
        "plant": "플랜트",
        "interior": "인테리어",
        "public-soc": "SOC (공항,도로,철도)",
        "public-energy": "에너지 공기업",
        "public-finance": "금융 공기업",
        "public-admin": "일반행정",
        "mpe-semiconductor": "반도체 소부장",
        "mpe-display": "디스플레이 소부장",
        "mpe-battery": "2차전지 소부장",
        "auto-parts": "자동차 부품",
        "chemical-materials": "화학/소재",
        "hotel": "호텔",
        "travel-agency": "여행사",
        "airline": "항공사",
        "leisure-resort": "레저/리조트",
        "consulting": "컨설팅",
        "accounting-tax": "회계/세무",
        "law-firm": "법률 (로펌)",
        "market-research": "리서치",
        "logistics-delivery": "물류/택배",
        "shipping": "해운",
        "forwarding": "포워딩",
        "land-transport": "육상운송",
        "edutech": "에듀테크",
        "private-academy": "입시/보습학원",
        "edu-publishing": "교육출판",
        "language-edu": "외국어교육",
        "ngo-npo": "NGO/NPO",
        "social-enterprise": "사회적기업",
        "foundation": "재단"
    }
    
    cards_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;'>"
    
    colors = ["#EBF8FF", "#ECFDF5", "#FEF2F2", "#F5F3FF", "#FFF7ED", "#F0FDFA", "#FDF2F8"]
    border_colors = ["#1E40AF", "#059669", "#DC2626", "#7C3AED", "#EA580C", "#0F766E", "#BE185D"]
    
    for i, tag in enumerate(tags):
        color = colors[i % len(colors)]
        border_color = border_colors[i % len(border_colors)]
        tag_name = tag_mapping.get(tag, tag)
        
        cards_html += f"""
        <div style="
            background-color: {color};
            border: 2px solid {border_color};
            border-radius: 12px;
            padding: 15px;
            margin: 5px;
            min-width: 150px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <div style="
                font-weight: bold; 
                color: {border_color}; 
                font-size: 14px;
                margin-bottom: 5px;
            ">#{tag_name}</div>
            <div style="
                color: #6B7280; 
                font-size: 12px;
                font-family: monospace;
            ">{tag}</div>
        </div>
        """
    
    cards_html += "</div>"
    return cards_html

def process_classification(job_title, company_name):
    """
    분류 결과를 처리하고 UI에 표시할 형태로 변환하는 함수
    """
    try:
        content, tags = classify_industry(job_title, company_name)
        tag_cards = create_tag_cards(tags)
        return content, tag_cards
    except Exception as e:
        error_content = f"""## ❌ 오류 발생

산업 분류 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주세요.
"""
        error_cards = create_tag_cards([])
        return error_content, error_cards

def create_interface():
    """
    Gradio 인터페이스 생성
    """
    with gr.Blocks(
        title="🏷️ AI 산업 분류기",
        theme=gr.themes.Soft(),
        css="""
        .main-header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .input-section {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .example-section {
            background-color: #f0f9ff;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        """
    ) as demo:
        
        # 헤더
        gr.HTML("""
        <div class="main-header">
            <h1>🏷️ AI 산업 분류기</h1>
            <p>직무와 회사명을 바탕으로 정확한 산업 분야를 분류합니다</p>
        </div>
        """)
        
        # 설명
        gr.Markdown("""
        ### 🚀 **사용 방법**
        1. **직무**: 분류하고 싶은 직무를 입력하세요
        2. **회사명**: 해당 회사명을 입력하세요
        3. **분류**: '산업 분류' 버튼을 클릭하여 결과를 확인하세요
        
        ✨ **특징**: 회사의 사업 영역과 직무 특성을 종합적으로 고려하여 정확한 산업 태그를 제공합니다.
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # 입력 섹션
                gr.HTML('<div class="input-section">')
                gr.Markdown("### 📝 **기본 정보 입력**")
                
                with gr.Row():
                    job_input = gr.Textbox(
                        label="💼 직무",
                        placeholder="예: 경영기획, 백엔드 개발, 온라인마케팅 등",
                        value="",
                        scale=1
                    )
                    
                    company_input = gr.Textbox(
                        label="🏢 회사명",
                        placeholder="예: 삼성전자, 토스, 카카오 등",
                        value="",
                        scale=1
                    )
                
                classify_btn = gr.Button(
                    "🏷️ 산업 분류", 
                    variant="primary", 
                    size="lg"
                )
                gr.HTML('</div>')
                
            with gr.Column(scale=1):
                # 예제 및 가이드
                gr.HTML('<div class="example-section">')
                gr.Markdown("### 💡 **예제 회사**")
                
                company_rows = [example_companies[i:i+2] for i in range(0, len(example_companies), 2)]
                for row in company_rows:
                    with gr.Row():
                        for company in row:
                            example_btn = gr.Button(
                                company, 
                                size="sm", 
                                variant="secondary",
                                scale=1
                            )
                            example_btn.click(
                                fn=lambda x=company: x,
                                outputs=company_input
                            )
                
                gr.Markdown("### 💼 **예제 직무**")
                
                job_rows = [example_jobs[i:i+2] for i in range(0, len(example_jobs), 2)]
                for row in job_rows:
                    with gr.Row():
                        for job in row:
                            job_btn = gr.Button(
                                job, 
                                size="sm", 
                                variant="secondary",
                                scale=1
                            )
                            job_btn.click(
                                fn=lambda x=job: x,
                                outputs=job_input
                            )
                gr.HTML('</div>')
        
        # 결과 출력 섹션
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📋 **분류 결과**")
                result_output = gr.Markdown(
                    value="직무와 회사명을 입력하고 '산업 분류' 버튼을 클릭하세요.",
                    elem_classes=["result-output"]
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 🏷️ **산업 태그**")
                tag_cards = gr.HTML(
                    value="<div style='text-align: center; color: #6B7280; padding: 20px;'>분류를 실행해주세요</div>",
                    elem_classes=["tag-cards"]
                )
        
        # 분류 버튼 클릭 이벤트
        classify_btn.click(
            fn=process_classification,
            inputs=[job_input, company_input],
            outputs=[result_output, tag_cards],
            api_name="classify_industry"
        )
        
        # 푸터
        gr.Markdown("""
        ---
        **💡 분류 기준**:
        - **IT·플랫폼·게임**: 플랫폼, 이커머스, 게임, IT솔루션, 핀테크 등
        - **제조·하드웨어**: 반도체, 가전, 자동차, 2차전지, 디스플레이 등
        - **금융**: 은행, 증권, 보험, 카드, 자산운용 등
        - **유통·소비재**: 백화점, 편의점, FMCG, 패션뷰티 등
        - **기타**: 바이오제약, 미디어콘텐츠, 건설부동산, 공기업 등
        
        🤖 **Powered by**: OpenAI GPT-4o-mini with Web Search
        """)
    
    return demo

if __name__ == "__main__":
    # Gradio 앱 실행
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        # server_port=7862,
        share=True,
        show_error=True
    ) 