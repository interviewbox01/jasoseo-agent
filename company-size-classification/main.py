import gradio as gr
from llm_functions import analyze_company_size

# LLM 관련 함수들은 llm_functions.py로 이동됨

example_company_name = ["삼성전자", "현대자동차", "LG전자", "SK하이닉스", "포스코홀딩스", "한화", "롯데케미칼", "CJ제일제당", "두산에너빌리티", "KT", "셀트리온헬스케어", "에스에프에이", "하림지주", "이녹스첨단소재", "코웨이", "한솔케미칼", "덴티움", "에코프로에이치엔", "다우기술", "제넥신", "오스템임플란트", "비츠로셀", "바디프랜드", "씨아이에스", "아이센스", "이루다", "나노신소재", "위메이드맥스", "에이치엘사이언스", "더네이쳐홀딩스", "피에스케이", "뉴파워프라즈마", "지누스", "원익IPS", "지아이이노베이션", "뤼이드", "센드버드", "직방", "리디", "버즈빌", "당근마켓", "컬리", "왓챠", "루닛", "플라네타리움", "크래프톤 벤처스", "뱅크샐러드", "직토", "트레바리", "메스프레소"]
    
# analyze_company_size 함수는 llm_functions.py로 이동됨

def get_category_button_style(category):
    """
    카테고리별 색깔과 스타일을 반환하는 함수
    """
    category_styles = {
        "대기업": {"color": "#1E40AF", "bg_color": "#EBF8FF", "emoji": "🏢"},
        "중견기업": {"color": "#059669", "bg_color": "#ECFDF5", "emoji": "🏭"},
        "중소기업": {"color": "#DC2626", "bg_color": "#FEF2F2", "emoji": "🏪"},
        "스타트업": {"color": "#7C3AED", "bg_color": "#F5F3FF", "emoji": "🚀"},
        "외국계기업": {"color": "#EA580C", "bg_color": "#FFF7ED", "emoji": "🌏"},
        "공공기관 및 공기업": {"color": "#0F766E", "bg_color": "#F0FDFA", "emoji": "🏛️"},
        "비영리단체 및 협회재단": {"color": "#BE185D", "bg_color": "#FDF2F8", "emoji": "🤝"},
        "금융업": {"color": "#7C2D12", "bg_color": "#FEF7ED", "emoji": "🏦"},
        "분류 불가": {"color": "#6B7280", "bg_color": "#F9FAFB", "emoji": "❓"},
        "오류 발생": {"color": "#B91C1C", "bg_color": "#FEF2F2", "emoji": "⚠️"}
    }
    
    return category_styles.get(category, category_styles["분류 불가"])

def create_category_html(category):
    """
    카테고리를 위한 HTML 버튼을 생성하는 함수
    """
    style = get_category_button_style(category)
    
    html = f"""
    <div style="text-align: center; padding: 10px;">
        <div style="
            background-color: {style['bg_color']};
            border: 2px solid {style['color']};
            border-radius: 15px;
            padding: 15px 20px;
            margin: 10px 0;
            font-weight: bold;
            font-size: 16px;
            color: {style['color']};
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <div style="font-size: 24px; margin-bottom: 5px;">{style['emoji']}</div>
            <div>{category}</div>
        </div>
    </div>
    """
    return html

def process_analysis_result(company_name):
    """
    분석 결과를 처리하고 UI에 표시할 형태로 변환하는 함수
    """
    try:
        content, category = analyze_company_size(company_name)
        category_html = create_category_html(category)
        return content, category_html
    except Exception as e:
        error_content = f"""## ❌ 오류 발생

죄송합니다. {company_name}의 기업 규모 분석 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주시거나 다른 기업명을 입력해주세요.
"""
        error_html = create_category_html("오류 발생")
        return error_content, error_html

def create_interface():
    """
    Gradio 인터페이스 생성
    """
    with gr.Blocks(
        title="🏢 AI 기업 규모 예측기",
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
        .example-section {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        """
    ) as demo:
        
        # 헤더
        gr.HTML("""
        <div class="main-header">
            <h1>🏢 AI 기업 규모 예측기</h1>
            <p>OpenAI Search API를 활용한 실시간 기업 정보 분석</p>
        </div>
        """)
        
        # 설명
        gr.Markdown("""
        ### 🚀 **사용 방법**
        1. **직접 입력**: 분석하고 싶은 기업명을 입력창에 직접 작성
        2. **예제 선택**: 아래 예제 기업 중 하나를 클릭하여 자동 입력
        3. **분석 실행**: '기업 규모 분석' 버튼을 클릭하여 결과 확인
        
        ✨ **특징**: 최신 웹 정보를 실시간으로 검색하여 정확한 기업 규모를 분류합니다.
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # 입력 섹션
                company_input = gr.Textbox(
                    label="🏢 기업명 입력",
                    placeholder="분석하고 싶은 기업명을 입력하세요 (예: 삼성전자, 카카오, 배달의민족 등)",
                    value="",
                    lines=1
                )
                
                analyze_btn = gr.Button(
                    "🔍 기업 규모 분석", 
                    variant="primary", 
                    size="lg"
                )
                
            with gr.Column(scale=1):
                # 정보 박스
                gr.Markdown("""
                ### ℹ️ **분류 기준**
                - **대기업**: 매출 1조원 이상
                - **중견기업**: 매출 1000억-1조원  
                - **중소기업**: 매출 1000억원 미만
                - **스타트업**: 설립 10년 이내
                - **외국계기업**: 해외 본사 기업
                - **공공기관**: 정부 출자/출연
                - **비영리단체**: 비영리 목적
                - **금융업**: 금융 서비스업
                """)
        
        # 예제 기업 섹션
        gr.HTML('<div class="example-section">')
        gr.Markdown("### 💼 **예제 기업 선택** (클릭하면 자동 입력됩니다)")
        
        # 예제 버튼들을 행별로 배치
        example_rows = [example_company_name[i:i+10] for i in range(0, len(example_company_name), 10)]
        
        for row in example_rows:
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
        
        gr.HTML('</div>')
        
        # 결과 출력 섹션
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("### 📋 **분석 결과**")
                result_output = gr.Markdown(
                    label="분석 결과",
                    value="기업명을 입력하고 '기업 규모 분석' 버튼을 클릭하세요.",
                    elem_classes=["result-output"]
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 📊 **분류 결과**")
                # 카테고리 표시용 HTML 컴포넌트
                category_display = gr.HTML(
                    value="""<div style="text-align: center; padding: 20px;">
                    <div style="color: #6B7280; font-size: 14px;">분석을 실행해주세요</div>
                    </div>""",
                    elem_classes=["category-display"]
                )
        
        # 분석 버튼 클릭 이벤트
        analyze_btn.click(
            fn=process_analysis_result,
            inputs=[company_input],
            outputs=[result_output, category_display],
            api_name="analyze_company"
        )
        
        # 엔터키로도 분석 실행 가능
        company_input.submit(
            fn=process_analysis_result,
            inputs=[company_input],
            outputs=[result_output, category_display]
        )
        
        # 푸터
        gr.Markdown("""
        ---
        **💡 팁**: 
        - 한국 기업명뿐만 아니라 글로벌 기업도 분석 가능합니다
        - 분석 결과에는 실시간 웹 검색을 통한 최신 정보가 반영됩니다
        - 참고 자료 링크를 통해 상세 정보를 확인할 수 있습니다
        
        🔍 **Powered by**: OpenAI Search API (gpt-4o-mini-search-preview)
        """)
    
    return demo

if __name__ == "__main__":
    # Gradio 앱 실행
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7859,
        share=True,
        show_error=True
    )
