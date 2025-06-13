import gradio as gr
import yaml
import json
import os
from openai import OpenAI
from llm_functions import generate_question_recommendation, parse_question_recommendation

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 프롬프트 로드
def load_prompts():
    with open('prompt.yaml', 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

prompts = load_prompts()

def recommend_question(job_title, company_name, experience_level):
    """면접 질문을 추천하는 함수"""
    try:
        # LLM 함수 호출
        result = generate_question_recommendation(
            client=client,
            prompts=prompts,
            job_title=job_title,
            company_name=company_name,
            experience_level=experience_level
        )
        
        # 결과 파싱
        parsed_result = parse_question_recommendation(result)
        
        if parsed_result and 'recommended_question' in parsed_result:
            return parsed_result['recommended_question']
        else:
            return "질문 생성에 실패했습니다. 다시 시도해주세요."
            
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

# 예시 버튼 함수들
def example_1():
    return "백엔드 개발", "토스 (비바리퍼블리카)", "신입"

def example_2():
    return "식품마케팅", "CJ제일제당", "경력"

def example_3():
    return "A&R", "하이브", "인턴"

def example_4():
    return "경영기획", "현대건설", "신입"

def example_5():
    return "해외영업", "삼성전자", "경력"

# Gradio 인터페이스 생성
with gr.Blocks(
    title="면접 질문 추천",
    theme=gr.themes.Soft(
        primary_hue="purple",
        secondary_hue="pink",
        neutral_hue="gray"
    ),
    css="""
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    .header {
        text-align: center;
        margin-bottom: 30px;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
    }
    .input-section {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .result-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin-top: 20px;
    }
    .example-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 15px;
        justify-content: center;
    }
    .example-btn {
        background: linear-gradient(45deg, #667eea, #764ba2);
        border: none;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .example-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    """
) as demo:
    
    with gr.Column(elem_classes="main-container"):
        # 헤더
        gr.HTML("""
        <div class="header">
            <h1>🎯 면접 질문 추천</h1>
            <p>직무, 회사명, 경력 수준을 입력하면 맞춤형 면접 질문을 추천해드립니다</p>
        </div>
        """)
        
        with gr.Column(elem_classes="input-section"):
            gr.HTML("<h3>📝 정보 입력</h3>")
            
            job_title = gr.Textbox(
                label="직무",
                placeholder="예: 백엔드 개발, 마케팅, 기획 등",
                lines=1
            )
            
            company_name = gr.Textbox(
                label="회사명",
                placeholder="예: 토스, 삼성전자, 네이버 등",
                lines=1
            )
            
            experience_level = gr.Dropdown(
                label="경력 수준",
                choices=["신입", "경력", "인턴", "기타"],
                value="신입"
            )
            
            # 예시 버튼들
            gr.HTML("<h4>💡 예시로 시작하기</h4>")
            with gr.Row():
                ex1_btn = gr.Button("토스 백엔드 신입", size="sm", variant="secondary")
                ex2_btn = gr.Button("CJ제일제당 마케팅 경력", size="sm", variant="secondary")
                ex3_btn = gr.Button("하이브 A&R 인턴", size="sm", variant="secondary")
            
            with gr.Row():
                ex4_btn = gr.Button("현대건설 경영기획 신입", size="sm", variant="secondary")
                ex5_btn = gr.Button("삼성전자 해외영업 경력", size="sm", variant="secondary")
            
            submit_btn = gr.Button("🎯 면접 질문 추천받기", variant="primary", size="lg")
        
        # 결과 출력
        with gr.Column(elem_classes="result-section"):
            gr.HTML("<h3>💬 추천 면접 질문</h3>")
            result_output = gr.Textbox(
                label="",
                placeholder="위 정보를 입력하고 '면접 질문 추천받기' 버튼을 클릭하세요.",
                lines=5,
                show_label=False,
                interactive=False
            )
    
    # 이벤트 핸들러
    submit_btn.click(
        fn=recommend_question,
        inputs=[job_title, company_name, experience_level],
        outputs=result_output
    )
    
    # 예시 버튼 이벤트
    ex1_btn.click(fn=example_1, outputs=[job_title, company_name, experience_level])
    ex2_btn.click(fn=example_2, outputs=[job_title, company_name, experience_level])
    ex3_btn.click(fn=example_3, outputs=[job_title, company_name, experience_level])
    ex4_btn.click(fn=example_4, outputs=[job_title, company_name, experience_level])
    ex5_btn.click(fn=example_5, outputs=[job_title, company_name, experience_level])

if __name__ == "__main__":
    demo.launch(
        # server_port=7864,
        share=True,
        show_error=True
    ) 