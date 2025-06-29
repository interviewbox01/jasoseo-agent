import gradio as gr
from llm_functions import generate_jd_recommendation

# 예제 데이터
example_companies = ["삼성전자", "쿠팡", "하이브", "토스", "현대건설", "신한은행", "넥슨", "아모레퍼시픽", "삼성바이오로직스", "HMM"]
example_jobs = ["경영기획", "온라인마케팅", "HRM(인사운영)", "백엔드 개발", "해외영업", "데이터 분석", "영업", "마케팅", "기획", "개발"]
experience_levels = ["신입", "경력", "인턴", "기타"]

def create_jd_card(jd_content):
    """
    직무기술서를 카드 형태로 표시하는 HTML 생성
    """
    if not jd_content:
        return "<div style='text-align: center; color: #6B7280; padding: 20px;'>직무기술서를 생성해주세요</div>"
    
    # 문장 단위로 분리하여 더 읽기 쉽게 표시
    sentences = jd_content.split('. ')
    formatted_content = ""
    
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            # 마지막 문장이 아니면 마침표 추가
            if i < len(sentences) - 1 and not sentence.endswith('.'):
                sentence += '.'
            formatted_content += f"<p style='margin: 10px 0; line-height: 1.6;'>{sentence.strip()}</p>"
    
    return f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.1);
    ">
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        ">
            <div style="
                background: rgba(255,255,255,0.2);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 15px;
                font-size: 18px;
            ">📋</div>
            <h3 style="margin: 0; font-size: 20px; font-weight: bold;">추천 직무기술서</h3>
        </div>
        
        <div style="
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
        ">
            {formatted_content}
        </div>
        
        <div style="
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.2);
            font-size: 14px;
            opacity: 0.8;
            text-align: center;
        ">
            💡 이 직무기술서를 참고하여 맞춤형 자기소개서를 작성해보세요
        </div>
    </div>
    """

def create_tips_card():
    """
    자소서 작성 팁 카드 생성
    """
    return """
    <div style="
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    ">
        <h3 style="margin: 0 0 20px 0; font-size: 18px; display: flex; align-items: center;">
            <span style="margin-right: 10px;">💡</span>
            자소서 작성 팁
        </h3>
        
        <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 20px;">
            <div style="margin-bottom: 15px;">
                <strong>1. 핵심 업무 매칭</strong><br>
                <span style="font-size: 14px; opacity: 0.9;">직무기술서의 주요 업무와 관련된 경험을 구체적으로 서술</span>
            </div>
            
            <div style="margin-bottom: 15px;">
                <strong>2. 요구 역량 어필</strong><br>
                <span style="font-size: 14px; opacity: 0.9;">언급된 스킬과 역량에 대한 본인의 준비도를 증명</span>
            </div>
            
            <div style="margin-bottom: 15px;">
                <strong>3. 회사 특성 반영</strong><br>
                <span style="font-size: 14px; opacity: 0.9;">해당 회사의 사업 영역과 연관된 관심사나 경험을 포함</span>
            </div>
            
            <div>
                <strong>4. 성장 의지 표현</strong><br>
                <span style="font-size: 14px; opacity: 0.9;">직무에서 요구하는 성장 가능성과 학습 의지를 강조</span>
            </div>
        </div>
    </div>
    """

def process_jd_generation(job_title, company_name, experience_level):
    """
    직무기술서 생성 결과를 처리하고 UI에 표시할 형태로 변환하는 함수
    """
    try:
        content, jd_content = generate_jd_recommendation(job_title, company_name, experience_level)
        jd_card = create_jd_card(jd_content)
        tips_card = create_tips_card()
        return content, jd_card + tips_card
    except Exception as e:
        error_content = f"""## ❌ 오류 발생

직무기술서 생성 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주세요.
"""
        error_card = create_jd_card("")
        return error_content, error_card

def create_interface():
    """
    Gradio 인터페이스 생성
    """
    with gr.Blocks(
        title="📋 AI 직무기술서 생성기",
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
            <h1>📋 AI 직무기술서 생성기</h1>
            <p>맞춤형 직무기술서로 완벽한 자기소개서를 준비하세요</p>
        </div>
        """)
        
        # 설명
        gr.Markdown("""
        ### 🚀 **사용 방법**
        1. **직무**: 지원하고자 하는 직무를 입력하세요
        2. **회사명**: 지원 회사명을 입력하세요
        3. **경력 수준**: 신입/경력/인턴/기타 중 선택하세요
        4. **생성**: '직무기술서 생성' 버튼을 클릭하여 결과를 확인하세요
        
        ✨ **특징**: 실제 채용공고 스타일의 직무기술서를 생성하여 자소서 작성에 필요한 핵심 정보를 제공합니다.
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
                
                experience_input = gr.Dropdown(
                    label="📈 경력 수준",
                    choices=experience_levels,
                    value="신입",
                    interactive=True
                )
                
                generate_btn = gr.Button(
                    "📋 직무기술서 생성", 
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
                gr.Markdown("### 📋 **상세 직무기술서**")
                result_output = gr.Markdown(
                    value="직무, 회사명, 경력 수준을 입력하고 '직무기술서 생성' 버튼을 클릭하세요.",
                    elem_classes=["result-output"]
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 💼 **직무기술서 & 팁**")
                jd_cards = gr.HTML(
                    value="<div style='text-align: center; color: #6B7280; padding: 20px;'>직무기술서를 생성해주세요</div>",
                    elem_classes=["jd-cards"]
                )
        
        # 생성 버튼 클릭 이벤트
        generate_btn.click(
            fn=process_jd_generation,
            inputs=[job_input, company_input, experience_input],
            outputs=[result_output, jd_cards],
            api_name="generate_jd_recommendation"
        )
        
        # 푸터
        gr.Markdown("""
        ---
        **📋 직무기술서 특징**:
        - **현실적인 내용**: 실제 채용공고 스타일의 직무 설명
        - **경력별 맞춤**: 신입/경력/인턴/기타에 따른 적절한 수준의 요구사항
        - **회사 특성 반영**: 해당 회사의 사업 영역과 특성을 고려한 내용
        - **자소서 연계**: 자기소개서 작성에 직접 활용 가능한 구체적 정보
        
        💡 **활용 방법**: 생성된 직무기술서의 핵심 키워드와 요구사항을 자소서에 반영하여 맞춤형 지원서를 작성하세요.
        
        🤖 **Powered by**: OpenAI GPT-4o
        """)
    
    return demo

if __name__ == "__main__":
    # Gradio 앱 실행
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7863,
        share=True,
        show_error=True
    ) 