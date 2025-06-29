import gradio as gr
from llm_functions import generate_context_report

# 예제 데이터
example_companies = ["토스", "삼성전자", "CJ제일제당", "하이브", "현대건설", "신한은행", "카카오", "네이버", "LG전자", "SK하이닉스"]
example_jobs = ["백엔드 개발", "경영기획", "식품마케팅", "A&R", "HRM(인사운영)", "해외영업", "데이터 분석", "온라인마케팅", "기획", "개발"]
experience_levels = ["신입", "경력", "인턴", "기타"]

def create_info_cards(report_data):
    """
    리포트 데이터를 카드 형태로 표시하는 HTML 생성
    """
    if not report_data or 'company_profile' not in report_data:
        return "<div style='text-align: center; color: #6B7280; padding: 20px;'>리포트를 생성해주세요</div>"
    
    # 기업 프로필 카드
    company_card = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <h3 style="margin: 0 0 15px 0; font-size: 18px;">🏢 기업 프로필</h3>
        <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px;">
            <strong>🎯 비전/미션:</strong><br>
            {report_data['company_profile']['vision_mission']}<br><br>
            <strong>💎 핵심 가치:</strong><br>
            {' • '.join(report_data['company_profile']['core_values'])}<br><br>
            <strong>👥 인재상:</strong><br>
            {report_data['company_profile']['talent_philosophy']}
        </div>
    </div>
    """
    
    # 직무 분석 카드
    position_card = f"""
    <div style="
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <h3 style="margin: 0 0 15px 0; font-size: 18px;">💼 직무 분석</h3>
        <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px;">
            <strong>📋 역할:</strong><br>
            {report_data['position_analysis']['role_summary']}<br><br>
            <strong>🔧 하드 스킬:</strong><br>
            {' • '.join(report_data['position_analysis']['required_skills']['hard'])}<br><br>
            <strong>💡 소프트 스킬:</strong><br>
            {' • '.join(report_data['position_analysis']['required_skills']['soft'])}
        </div>
    </div>
    """
    
    # 산업 맥락 카드
    industry_card = f"""
    <div style="
        background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
        color: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <h3 style="margin: 0 0 15px 0; font-size: 18px;">🌐 산업 맥락</h3>
        <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px;">
            <strong>📈 주요 트렌드:</strong><br>
            {' • '.join(report_data['industry_context']['trends'])}<br><br>
            <strong>🏆 주요 경쟁사:</strong><br>
            {' • '.join(report_data['industry_context']['competitors'])}
        </div>
    </div>
    """
    
    # 키워드 카드
    keywords_html = ""
    if 'keywords' in report_data['position_analysis']:
        keywords_html = "<div style='margin-top: 15px;'><strong>🏷️ 핵심 키워드:</strong><br>"
        for keyword in report_data['position_analysis']['keywords']:
            keywords_html += f"<span style='background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 15px; margin: 2px; display: inline-block; font-size: 12px;'>{keyword}</span>"
        keywords_html += "</div>"
    
    return f"""
    <div style="display: flex; flex-direction: column; gap: 10px;">
        {company_card}
        {position_card}
        {industry_card}
        <div style="
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            color: #333;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0 0 15px 0; font-size: 18px;">🏷️ 핵심 키워드</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                {''.join([f'<span style="background: #667eea; color: white; padding: 8px 15px; border-radius: 20px; font-size: 14px; font-weight: bold;">{keyword}</span>' for keyword in report_data['position_analysis']['keywords']])}
            </div>
        </div>
    </div>
    """

def process_report_generation(job_title, company_name, experience_level):
    """
    리포트 생성 결과를 처리하고 UI에 표시할 형태로 변환하는 함수
    """
    try:
        content, report_data = generate_context_report(job_title, company_name, experience_level)
        info_cards = create_info_cards(report_data)
        return content, info_cards
    except Exception as e:
        error_content = f"""## ❌ 오류 발생

컨텍스트 리포트 생성 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주세요.
"""
        error_cards = create_info_cards({})
        return error_content, error_cards

def create_interface():
    """
    Gradio 인터페이스 생성
    """
    with gr.Blocks(
        title="📊 자소서 컨텍스트 리포트",
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
            <h1>📊 자소서 컨텍스트 리포트</h1>
            <p>기업과 직무에 대한 종합적인 분석으로 완벽한 자기소개서를 준비하세요</p>
        </div>
        """)
        
        # 설명
        gr.Markdown("""
        ### 🚀 **사용 방법**
        1. **직무**: 지원하고자 하는 직무를 입력하세요
        2. **회사명**: 지원 회사명을 입력하세요
        3. **경력 수준**: 신입/경력/인턴/기타 중 선택하세요
        4. **생성**: '리포트 생성' 버튼을 클릭하여 결과를 확인하세요
        
        ✨ **특징**: 기업 프로필, 직무 분석, 산업 맥락을 종합적으로 분석하여 자소서 작성에 필요한 핵심 정보를 제공합니다.
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # 입력 섹션
                gr.HTML('<div class="input-section">')
                gr.Markdown("### 📝 **기본 정보 입력**")
                
                with gr.Row():
                    job_input = gr.Textbox(
                        label="💼 직무",
                        placeholder="예: 백엔드 개발, 경영기획, 마케팅 등",
                        value="",
                        scale=1
                    )
                    
                    company_input = gr.Textbox(
                        label="🏢 회사명",
                        placeholder="예: 토스, 삼성전자, 카카오 등",
                        value="",
                        scale=1
                    )
                
                experience_input = gr.Dropdown(
                    label="📈 경력 수준",
                    choices=experience_levels,
                    value="신입",
                    interactive=True
                )
                
                generate_btn = gr.Button(
                    "📊 리포트 생성", 
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
                
                gr.Markdown("### 📈 **경력 수준**")
                with gr.Row():
                    for level in experience_levels:
                        level_btn = gr.Button(
                            level, 
                            size="sm", 
                            variant="secondary",
                            scale=1
                        )
                        level_btn.click(
                            fn=lambda x=level: x,
                            outputs=experience_input
                        )
                
                gr.HTML('</div>')
        
        # 결과 출력 섹션
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📋 **상세 리포트**")
                result_output = gr.Markdown(
                    value="직무, 회사명, 경력 수준을 입력하고 '리포트 생성' 버튼을 클릭하세요.",
                    elem_classes=["result-output"]
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 📊 **핵심 정보**")
                info_cards = gr.HTML(
                    value="<div style='text-align: center; color: #6B7280; padding: 20px;'>리포트를 생성해주세요</div>",
                    elem_classes=["info-cards"]
                )
        
        # 생성 버튼 클릭 이벤트
        generate_btn.click(
            fn=process_report_generation,
            inputs=[job_input, company_input, experience_input],
            outputs=[result_output, info_cards],
            api_name="generate_context_report"
        )
        
        # 푸터
        gr.Markdown("""
        ---
        **📊 리포트 구성**:
        - **🏢 기업 프로필**: 비전/미션, 핵심가치, 인재상, 최근동향, 주요제품/서비스
        - **💼 직무 분석**: 역할요약, 필요스킬(하드/소프트), 핵심키워드
        - **🌐 산업 맥락**: 주요트렌드, 경쟁사 정보
        
        💡 **활용 팁**: 생성된 키워드와 정보를 자소서 작성 시 적극 활용하여 맞춤형 자기소개서를 작성하세요.
        
        🤖 **Powered by**: OpenAI GPT-4o
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