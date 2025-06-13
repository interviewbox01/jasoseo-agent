import gradio as gr
from llm_functions import generate_interview_questions

# LLM 관련 함수들은 llm_functions.py로 이동됨

# 예제 데이터
example_companies = ["삼성전자", "토스", "카카오", "네이버", "LG전자", "현대자동차", "CJ제일제당", "하이브", "쿠팡", "배달의민족"]
example_jobs = ["백엔드 개발", "프론트엔드 개발", "데이터 사이언티스트", "마케팅", "영업", "기획", "디자인", "HR", "재무", "A&R"]
experience_levels = ["신입", "경력", "인턴", "기타"]
common_questions_list = [
    "자기소개를 해보세요",
    "지원 동기가 무엇인가요",
    "본인의 강점은 무엇인가요",
    "가장 도전적인 경험은 무엇인가요",
    "성공 경험을 말해주세요",
    "실패 경험을 말해주세요",
    "입사 후 포부는 무엇인가요",
    "성격의 장단점을 말해주세요",
    "존경하는 인물은 누구인가요",
    "마지막으로 하고 싶은 말은?"
]

# generate_interview_questions 함수는 llm_functions.py로 이동됨

def create_question_cards(questions):
    """
    생성된 질문들을 카드 형태로 표시하는 HTML 생성
    """
    if not questions:
        return "<div style='text-align: center; color: #6B7280; padding: 20px;'>질문을 생성해주세요</div>"
    
    cards_html = "<div style='display: flex; flex-direction: column; gap: 15px;'>"
    
    colors = ["#EBF8FF", "#ECFDF5", "#FEF2F2", "#F5F3FF", "#FFF7ED"]
    border_colors = ["#1E40AF", "#059669", "#DC2626", "#7C3AED", "#EA580C"]
    
    for i, question in enumerate(questions):
        color = colors[i % len(colors)]
        border_color = border_colors[i % len(border_colors)]
        
        cards_html += f"""
        <div style="
            background-color: {color};
            border: 2px solid {border_color};
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <div style="
                font-weight: bold; 
                color: {border_color}; 
                font-size: 16px;
                margin-bottom: 10px;
            ">질문 {i+1}</div>
            <div style="
                color: #374151; 
                font-size: 15px; 
                line-height: 1.5;
            ">{question}</div>
        </div>
        """
    
    cards_html += "</div>"
    return cards_html

def process_question_generation(company_name, job_title, experience_level, selected_questions, num_questions):
    """
    질문 생성 결과를 처리하고 UI에 표시할 형태로 변환하는 함수
    """
    try:
        content, questions = generate_interview_questions(company_name, job_title, experience_level, selected_questions, num_questions)
        question_cards = create_question_cards(questions)
        return content, question_cards
    except Exception as e:
        error_content = f"""## ❌ 오류 발생

질문 생성 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주세요.
"""
        error_cards = create_question_cards([])
        return error_content, error_cards

# 전역 상태 관리
class AppState:
    def __init__(self):
        self.companies = ["토스", "네이버", "카카오", "삼성전자", "LG전자", "현대자동차", "SK하이닉스", "CJ제일제당", "하이브", "현대건설"]
        self.jobs = ["백엔드 개발자", "프론트엔드 개발자", "데이터 사이언티스트", "마케팅", "영업", "기획", "디자이너", "A&R", "해외영업", "사업기획"]
        self.questions = common_questions_list.copy()

app_state = AppState()

# 더 이상 사용하지 않는 함수들 제거됨

def add_company(new_company):
    """새 회사 추가"""
    if new_company and new_company.strip() and new_company.strip() not in app_state.companies:
        app_state.companies.append(new_company.strip())
        return gr.Dropdown.update(choices=app_state.companies), ""
    return gr.Dropdown.update(), ""

def add_job(new_job):
    """새 직무 추가"""
    if new_job and new_job.strip() and new_job.strip() not in app_state.jobs:
        app_state.jobs.append(new_job.strip())
        return gr.Dropdown.update(choices=app_state.jobs), ""
    return gr.Dropdown.update(), ""

def add_question(new_question):
    """새 일반 질문 추가"""
    if new_question and new_question.strip() and new_question.strip() not in app_state.questions:
        app_state.questions.append(new_question.strip())
    return gr.CheckboxGroup.update(choices=app_state.questions), ""

def create_interface():
    """
    Gradio 인터페이스 생성
    """
    with gr.Blocks(
        title="🎯 AI 면접 질문 생성기",
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
            <h1>🎯 AI 면접 질문 생성기</h1>
            <p>회사와 직무에 맞춤형 면접 질문을 AI가 생성해드립니다</p>
        </div>
        """)
        
        # 설명
        gr.Markdown("""
        ### 🚀 **사용 방법**
        1. **회사명**: 지원하고자 하는 회사를 입력하세요
        2. **직무**: 지원 직무를 입력하세요  
        3. **경력 수준**: 본인의 경력 수준을 선택하세요
        4. **일반 질문**: 참고할 일반적인 면접 질문들을 선택하세요
        5. **생성**: '질문 생성' 버튼을 클릭하여 맞춤형 질문을 받아보세요
        
        ✨ **특징**: 회사의 특성, 직무 요구사항, 경력 수준을 모두 고려한 구체적이고 현실적인 질문을 생성합니다.
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # 입력 섹션
                gr.HTML('<div class="input-section">')
                gr.Markdown("### 📝 **기본 정보 입력**")
                
                with gr.Row():
                    company_input = gr.Textbox(
                        label="🏢 회사명",
                        placeholder="예: 삼성전자, 토스, 카카오 등",
                        value="",
                        scale=2,
                        elem_id="company_input"
                    )
                    
                    job_input = gr.Textbox(
                        label="💼 직무",
                        placeholder="예: 백엔드 개발, 마케팅, 기획 등",
                        value="",
                        scale=2,
                        elem_id="job_input"
                    )
                
                with gr.Row():
                    experience_input = gr.Dropdown(
                        label="📊 경력 수준",
                        choices=experience_levels,
                        value="신입",
                        interactive=True,
                        scale=2
                    )
                    
                    num_questions_input = gr.Dropdown(
                        label="🔢 질문 개수",
                        choices=[1, 2, 3, 4, 5],
                        value=3,
                        interactive=True,
                        scale=1
                    )
                
                common_questions_input = gr.CheckboxGroup(
                    label="📋 참고할 일반 면접 질문 (3-5개 선택 권장)",
                    choices=common_questions_list,
                    value=common_questions_list[:4],
                    interactive=True
                )
                
                generate_btn = gr.Button(
                    "🎯 맞춤형 질문 생성", 
                    variant="primary", 
                    size="lg"
                )
                gr.HTML('</div>')
                
            with gr.Column(scale=1):
                # 예제 및 가이드
                gr.HTML('<div class="example-section">')
                
                # 사용자 정의 회사 추가
                gr.Markdown("### 🏢 **회사 관리**")
                with gr.Row():
                    new_company_input = gr.Textbox(
                        label="새 회사 추가",
                        placeholder="회사명 입력",
                        scale=2
                    )
                    add_company_btn = gr.Button("추가", size="sm", scale=1)
                
                # 예제 회사 드롭다운
                company_dropdown = gr.Dropdown(
                    label="예제 회사 선택",
                    choices=app_state.companies,
                    value=None,
                    interactive=True
                )
                
                # 사용자 정의 직무 추가
                gr.Markdown("### 💼 **직무 관리**")
                with gr.Row():
                    new_job_input = gr.Textbox(
                        label="새 직무 추가",
                        placeholder="직무명 입력",
                        scale=2
                    )
                    add_job_btn = gr.Button("추가", size="sm", scale=1)
                
                # 예제 직무 드롭다운
                job_dropdown = gr.Dropdown(
                    label="예제 직무 선택",
                    choices=app_state.jobs,
                    value=None,
                    interactive=True
                )
                
                # 사용자 정의 일반 질문 추가
                gr.Markdown("### 📋 **일반 질문 관리**")
                with gr.Row():
                    new_question_input = gr.Textbox(
                        label="새 일반 질문 추가",
                        placeholder="질문 내용 입력",
                        scale=2
                    )
                    add_question_btn = gr.Button("추가", size="sm", scale=1)
                
                gr.HTML('</div>')
        
        # 결과 출력 섹션
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📋 **생성 결과**")
                result_output = gr.Markdown(
                    value="기본 정보를 입력하고 '맞춤형 질문 생성' 버튼을 클릭하세요.",
                    elem_classes=["result-output"]
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 🎯 **질문 카드**")
                question_cards = gr.HTML(
                    value="<div style='text-align: center; color: #6B7280; padding: 20px;'>질문을 생성해주세요</div>",
                    elem_classes=["question-cards"]
                )
        
        # 이벤트 핸들러 연결
        add_company_btn.click(
            fn=add_company,
            inputs=[new_company_input],
            outputs=[company_dropdown, new_company_input]
        )
        
        add_job_btn.click(
            fn=add_job,
            inputs=[new_job_input],
            outputs=[job_dropdown, new_job_input]
        )
        
        add_question_btn.click(
            fn=add_question,
            inputs=[new_question_input],
            outputs=[common_questions_input, new_question_input]
        )
        
        # 드롭다운 선택 시 입력 필드에 자동 입력
        company_dropdown.change(
            fn=lambda x: x if x else "",
            inputs=[company_dropdown],
            outputs=[company_input]
        )
        
        job_dropdown.change(
            fn=lambda x: x if x else "",
            inputs=[job_dropdown],
            outputs=[job_input]
        )
        
        # 생성 버튼 클릭 이벤트
        generate_btn.click(
            fn=process_question_generation,
            inputs=[company_input, job_input, experience_input, common_questions_input, num_questions_input],
            outputs=[result_output, question_cards],
            api_name="generate_questions"
        )
        
        # 푸터
        gr.Markdown("""
        ---
        **💡 생성된 질문 활용 팁**:
        - 각 질문에 대해 STAR(Situation, Task, Action, Result) 기법으로 답변을 준비해보세요
        - 회사와 직무에 대한 사전 조사를 바탕으로 구체적인 사례를 준비하세요
        - 생성된 질문을 바탕으로 추가 질문들도 예상해보세요
        
        🤖 **Powered by**: OpenAI GPT-4o with Web Search
        """)
    
    return demo

if __name__ == "__main__":
    # Gradio 앱 실행
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        # server_port=7864,
        share=True,
        show_error=True
    )
