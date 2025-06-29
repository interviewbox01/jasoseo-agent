import gradio as gr
import os
import sys
import importlib.util
from pathlib import Path
import dotenv

dotenv.load_dotenv()

# 현재 디렉토리 설정
current_dir = Path(__file__).parent

# 각 기능별 모듈 로드 함수
def load_module_from_path(module_name, file_path):
    """동적으로 모듈을 로드하는 함수"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"모듈 로드 실패 {module_name}: {e}")
        return None

# 각 기능별 모듈 및 함수 로드
modules = {}
available_features = {}

# 1. commonly-asked-question
try:
    llm_functions_path = current_dir / "commonly-asked-question" / "llm_functions.py"
    if llm_functions_path.exists():
        modules['commonly_asked'] = load_module_from_path("commonly_asked_llm", llm_functions_path)
        available_features['commonly_asked'] = modules['commonly_asked'] is not None
    else:
        available_features['commonly_asked'] = False
except Exception as e:
    print(f"commonly-asked-question 모듈 로드 실패: {e}")
    available_features['commonly_asked'] = False

# 2. question-recommendation
try:
    llm_functions_path = current_dir / "question-recommendation" / "llm_functions.py"
    if llm_functions_path.exists():
        modules['question_rec'] = load_module_from_path("question_rec_llm", llm_functions_path)
        available_features['question_rec'] = modules['question_rec'] is not None
    else:
        available_features['question_rec'] = False
except Exception as e:
    print(f"question-recommendation 모듈 로드 실패: {e}")
    available_features['question_rec'] = False

# 3. jd-recommendation
try:
    llm_functions_path = current_dir / "jd-recommendation" / "llm_functions.py"
    if llm_functions_path.exists():
        modules['jd_rec'] = load_module_from_path("jd_rec_llm", llm_functions_path)
        available_features['jd_rec'] = modules['jd_rec'] is not None
    else:
        available_features['jd_rec'] = False
except Exception as e:
    print(f"jd-recommendation 모듈 로드 실패: {e}")
    available_features['jd_rec'] = False

# 4. industry-classification
try:
    llm_functions_path = current_dir / "industry-classification" / "llm_functions.py"
    if llm_functions_path.exists():
        modules['industry'] = load_module_from_path("industry_llm", llm_functions_path)
        available_features['industry'] = modules['industry'] is not None
    else:
        available_features['industry'] = False
except Exception as e:
    print(f"industry-classification 모듈 로드 실패: {e}")
    available_features['industry'] = False

# 5. jasoseo-context-report
try:
    llm_functions_path = current_dir / "jasoseo-context-report" / "llm_functions.py"
    if llm_functions_path.exists():
        modules['jasoseo'] = load_module_from_path("jasoseo_llm", llm_functions_path)
        available_features['jasoseo'] = modules['jasoseo'] is not None
    else:
        available_features['jasoseo'] = False
except Exception as e:
    print(f"jasoseo-context-report 모듈 로드 실패: {e}")
    available_features['jasoseo'] = False

# 6. company-size-classification
try:
    llm_functions_path = current_dir / "company-size-classification" / "llm_functions.py"
    if llm_functions_path.exists():
        modules['company_size'] = load_module_from_path("company_size_llm", llm_functions_path)
        available_features['company_size'] = modules['company_size'] is not None
    else:
        available_features['company_size'] = False
except Exception as e:
    print(f"company-size-classification 모듈 로드 실패: {e}")
    available_features['company_size'] = False

# OpenAI 관련 모듈
try:
    from openai import OpenAI
    import yaml
    openai_available = True
except ImportError:
    openai_available = False

# OpenAI 클라이언트 초기화
client = None
if openai_available and os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 공통 CSS 스타일
common_css = """
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
.tab-container {
    margin: 20px 0;
    height: 100%;
}
"""

# 예제 데이터
example_companies = ["삼성전자", "토스", "카카오", "네이버", "LG전자", "현대자동차", "CJ제일제당", "하이브", "쿠팡", "배달의민족", "신한은행", "SKT", "포스코", "현대건설", "아모레퍼시픽"]
example_jobs = ["백엔드 개발", "프론트엔드 개발", "데이터 사이언티스트", "마케팅", "영업", "기획", "디자인", "HR", "재무", "A&R", "경영기획", "해외영업", "온라인마케팅", "식품마케팅", "HRM(인사운영)"]
experience_levels = ["신입", "경력", "인턴", "기타"]

# 공통 함수들
def create_example_buttons(companies, jobs, company_input, job_input):
    """예제 버튼들을 생성하는 함수"""
    
    gr.Markdown("### 💡 **예제 회사**")
    with gr.Row():
        for company in companies[:5]:
            btn = gr.Button(company, size="sm", variant="secondary")
            btn.click(fn=lambda x=company: x, outputs=company_input)
    
    with gr.Row():
        for company in companies[5:10]:
            btn = gr.Button(company, size="sm", variant="secondary")
            btn.click(fn=lambda x=company: x, outputs=company_input)
    
    gr.Markdown("### 💼 **예제 직무**")
    with gr.Row():
        for job in jobs[:5]:
            btn = gr.Button(job, size="sm", variant="secondary")
            btn.click(fn=lambda x=job: x, outputs=job_input)
    
    with gr.Row():
        for job in jobs[5:10]:
            btn = gr.Button(job, size="sm", variant="secondary")
            btn.click(fn=lambda x=job: x, outputs=job_input)

# 1. 일반적인 면접 질문 생성 탭
def create_commonly_asked_tab():
    if not available_features.get('commonly_asked'):
        gr.Markdown("❌ **일반적인 면접 질문 생성 기능을 사용할 수 없습니다.** (모듈 로드 실패)")
        return
    gr.HTML("""
    <div class="main-header">
        <h2>🎯 일반적인 면접 질문 생성</h2>
        <p>회사와 직무에 맞춤형 면접 질문을 AI가 생성해드립니다</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 **기본 정보 입력**")
            
            company_input = gr.Textbox(label="🏢 회사명", placeholder="예: 삼성전자, 토스, 카카오 등")
            job_input = gr.Textbox(label="💼 직무", placeholder="예: 백엔드 개발, 마케팅, 기획 등")
            
            with gr.Row():
                experience_input = gr.Dropdown(label="📊 경력 수준", choices=experience_levels, value="신입", interactive=True)
                num_questions_input = gr.Dropdown(label="📋 생성할 질문 수", choices=[1, 2, 3, 4, 5], value=3, interactive=True)
            
            common_questions_list = [
                "자기소개를 해보세요", "지원 동기가 무엇인가요", "본인의 강점은 무엇인가요",
                "가장 도전적인 경험은 무엇인가요", "성공 경험을 말해주세요", "실패 경험을 말해주세요",
                "입사 후 포부는 무엇인가요", "성격의 장단점을 말해주세요", "존경하는 인물은 누구인가요",
                "마지막으로 하고 싶은 말은?"
            ]
            selected_questions = gr.CheckboxGroup(label="📝 참고할 일반 질문 (선택)", choices=common_questions_list, value=common_questions_list[:3])
            
            generate_btn = gr.Button("🎯 면접 질문 생성", variant="primary", size="lg")
            
        with gr.Column(scale=1):
            create_example_buttons(example_companies, example_jobs, company_input, job_input)
    
    gr.Markdown("### 📋 **생성된 면접 질문**")
    result_output = gr.Markdown("위 정보를 입력하고 '면접 질문 생성' 버튼을 클릭하세요.")
    
    def process_question_generation(company, job, experience, selected, num):
        try:
            content, _ = modules['commonly_asked'].generate_interview_questions(company, job, experience, selected, num)
            return content
        except Exception as e:
            return f"❌ 오류가 발생했습니다: {e}"
    
    generate_btn.click(
        fn=process_question_generation,
        inputs=[company_input, job_input, experience_input, selected_questions, num_questions_input],
        outputs=result_output
    )

# 2. 면접 질문 추천 탭
def create_question_recommendation_tab():
    if not available_features.get('question_rec') or not openai_available:
        gr.Markdown("❌ **면접 질문 추천 기능을 사용할 수 없습니다.** (모듈 로드 실패 또는 API 키 없음)")
        return
    gr.HTML("""
    <div class="main-header">
        <h2>💡 면접 질문 추천</h2>
        <p>직무, 회사명, 경력 수준을 입력하면 AI가 맞춤형 질문을 추천합니다</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 **정보 입력**")
            job_input = gr.Textbox(label="💼 직무", placeholder="예: 백엔드 개발, 마케팅, 기획 등")
            company_input = gr.Textbox(label="🏢 회사명", placeholder="예: 토스, 삼성전자, 네이버 등")
            experience_input = gr.Dropdown(label="📊 경력 수준", choices=experience_levels, value="신입")
            submit_btn = gr.Button("💡 면접 질문 추천받기", variant="primary", size="lg")
            
        with gr.Column(scale=1):
            create_example_buttons(example_companies, example_jobs, company_input, job_input)
    
    gr.Markdown("### 💬 **추천 면접 질문**")
    result_output = gr.Textbox(label="", placeholder="추천된 면접 질문이 여기에 표시됩니다.", lines=5, show_label=False, interactive=False)
    
    def recommend_question(job, company, experience):
        try:
            if not client: return "❌ OpenAI API 키가 설정되지 않았습니다."
            prompt_path = current_dir / "question-recommendation" / "prompt.yaml"
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompts = yaml.safe_load(f)
            
            result = modules['question_rec'].generate_question_recommendation(client, prompts, job, company, experience)
            parsed = modules['question_rec'].parse_question_recommendation(result)
            return parsed.get('recommended_question', "질문 생성에 실패했습니다.")
        except Exception as e:
            return f"❌ 오류가 발생했습니다: {e}"
    
    submit_btn.click(fn=recommend_question, inputs=[job_input, company_input, experience_input], outputs=result_output)

# 3. 직무기술서 생성 탭
def create_jd_recommendation_tab():
    if not available_features.get('jd_rec'):
        gr.Markdown("❌ **직무기술서 생성 기능을 사용할 수 없습니다.** (모듈 로드 실패)")
        return
    gr.HTML("""
    <div class="main-header">
        <h2>📋 AI 직무기술서 생성기</h2>
        <p>맞춤형 직무기술서로 완벽한 자기소개서를 준비하세요</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 **기본 정보 입력**")
            job_input = gr.Textbox(label="💼 직무", placeholder="예: 경영기획, 백엔드 개발, 온라인마케팅 등")
            company_input = gr.Textbox(label="🏢 회사명", placeholder="예: 삼성전자, 토스, 카카오 등")
            experience_input = gr.Dropdown(label="📈 경력 수준", choices=experience_levels, value="신입", interactive=True)
            generate_btn = gr.Button("📋 직무기술서 생성", variant="primary", size="lg")

        with gr.Column(scale=1):
            create_example_buttons(example_companies, example_jobs, company_input, job_input)
    
    gr.Markdown("### 📜 **생성된 직무기술서**")
    result_output = gr.Markdown("위 정보를 입력하고 '직무기술서 생성' 버튼을 클릭하세요.")

    def process_jd_generation(job, company, experience):
        try:
            content, _ = modules['jd_rec'].generate_jd_recommendation(job, company, experience)
            return content
        except Exception as e:
            return f"❌ 오류가 발생했습니다: {e}"
    
    generate_btn.click(fn=process_jd_generation, inputs=[job_input, company_input, experience_input], outputs=result_output)

# 4. 산업 분류 탭
def create_industry_classification_tab():
    if not available_features.get('industry'):
        gr.Markdown("❌ **산업 분류 기능을 사용할 수 없습니다.** (모듈 로드 실패)")
        return
    gr.HTML("""
    <div class="main-header">
        <h2>🏷️ AI 산업 분류기</h2>
        <p>직무와 회사명을 바탕으로 정확한 산업 분야를 분류합니다</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 **기본 정보 입력**")
            job_input = gr.Textbox(label="💼 직무", placeholder="예: 경영기획, 백엔드 개발, 온라인마케팅 등")
            company_input = gr.Textbox(label="🏢 회사명", placeholder="예: 삼성전자, 토스, 카카오 등")
            classify_btn = gr.Button("🏷️ 산업 분류", variant="primary", size="lg")

        with gr.Column(scale=1):
            create_example_buttons(example_companies, example_jobs, company_input, job_input)
            
    gr.Markdown("### 📑 **분류 결과**")
    result_output = gr.Markdown("위 정보를 입력하고 '산업 분류' 버튼을 클릭하세요.")

    def process_classification(job, company):
        try:
            content, _ = modules['industry'].classify_industry(job, company)
            return content
        except Exception as e:
            return f"❌ 오류가 발생했습니다: {e}"

    classify_btn.click(fn=process_classification, inputs=[job_input, company_input], outputs=result_output)

# 5. 자소서 컨텍스트 리포트 탭
def create_jasoseo_context_tab():
    if not available_features.get('jasoseo'):
        gr.Markdown("❌ **자소서 컨텍스트 리포트 기능을 사용할 수 없습니다.** (모듈 로드 실패)")
        return
    gr.HTML("""
    <div class="main-header">
        <h2>📊 자소서 컨텍스트 리포트</h2>
        <p>기업과 직무에 대한 종합적인 분석으로 완벽한 자기소개서를 준비하세요</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 **기본 정보 입력**")
            job_input = gr.Textbox(label="💼 직무", placeholder="예: 백엔드 개발, 경영기획, 마케팅 등")
            company_input = gr.Textbox(label="🏢 회사명", placeholder="예: 토스, 삼성전자, 카카오 등")
            experience_input = gr.Dropdown(label="📈 경력 수준", choices=experience_levels, value="신입", interactive=True)
            generate_btn = gr.Button("📊 리포트 생성", variant="primary", size="lg")

        with gr.Column(scale=1):
            create_example_buttons(example_companies, example_jobs, company_input, job_input)
            
    gr.Markdown("### 📈 **컨텍스트 리포트**")
    result_output = gr.Markdown("위 정보를 입력하고 '리포트 생성' 버튼을 클릭하세요.")

    def process_report_generation(job, company, experience):
        try:
            content, _ = modules['jasoseo'].generate_context_report(job, company, experience)
            return content
        except Exception as e:
            return f"❌ 오류가 발생했습니다: {e}"

    generate_btn.click(fn=process_report_generation, inputs=[job_input, company_input, experience_input], outputs=result_output)

# 6. 기업 규모 분류 탭
def create_company_size_tab():
    if not available_features.get('company_size'):
        gr.Markdown("❌ **기업 규모 분류 기능을 사용할 수 없습니다.** (모듈 로드 실패)")
        return
    gr.HTML("""
    <div class="main-header">
        <h2>🏢 AI 기업 규모 예측기</h2>
        <p>실시간 웹 정보를 활용한 기업 정보 분석</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 **기업 정보 입력**")
            company_input = gr.Textbox(label="🏢 기업명 입력", placeholder="분석하고 싶은 기업명을 입력하세요 (예: 삼성전자, 카카오 등)")
            analyze_btn = gr.Button("🔍 기업 규모 분석", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("""
            ### ℹ️ **분류 기준**
            - **대기업**: 매출 1조원 이상
            - **중견기업**: 매출 1000억-1조원
            - **중소기업**: 매출 1000억원 미만
            - **스타트업**: 설립 10년 이내
            - **외국계기업**: 해외 본사
            - **공공기관/공기업**: 정부 출자/출연
            """)

    gr.Markdown("### 💼 **예제 기업 선택** (클릭하면 자동 입력됩니다)")
    example_company_names = ["삼성전자", "현대자동차", "SK하이닉스", "포스코홀딩스", "토스", "카카오", "네이버", "쿠팡", "배달의민족", "당근마켓"]
    with gr.Row():
        for company in example_company_names[:5]:
            btn = gr.Button(company, size="sm", variant="secondary")
            btn.click(fn=lambda x=company: x, outputs=company_input)
    with gr.Row():
        for company in example_company_names[5:]:
            btn = gr.Button(company, size="sm", variant="secondary")
            btn.click(fn=lambda x=company: x, outputs=company_input)
            
    gr.Markdown("### 📊 **분석 결과**")
    result_output = gr.Markdown("기업명을 입력하고 '기업 규모 분석' 버튼을 클릭하세요.")
    
    def process_analysis_result(company):
        try:
            content, _ = modules['company_size'].analyze_company_size(company)
            return content
        except Exception as e:
            return f"❌ 오류가 발생했습니다: {e}"
    
    analyze_btn.click(fn=process_analysis_result, inputs=[company_input], outputs=result_output)

# 메인 애플리케이션 생성
def create_main_app():
    with gr.Blocks(
        title="🚀 JasoSeo Agent - 취업 지원 AI 도구",
        theme=gr.themes.Soft(primary_hue="purple", secondary_hue="pink", neutral_hue="gray"),
        css=common_css
    ) as app:
        
        gr.HTML("""
        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; margin-bottom: 30px;">
            <h1 style="font-size: 32px; margin-bottom: 10px;">🚀 JasoSeo Agent</h1>
            <p style="font-size: 18px; margin-bottom: 0; opacity: 0.9;">AI 기반 취업 지원 통합 플랫폼</p>
        </div>
        """)
        
        status_items = [name for name, ok in available_features.items() if ok]
        status_text = f"✅ 사용 가능한 기능 ({len(status_items)}/{len(available_features)}): {', '.join(status_items)}" if status_items else "❌ 사용 가능한 기능이 없습니다."
        gr.Markdown(f"**{status_text}**")
        
     
        
        with gr.Tabs(elem_classes="tab-container"):
            with gr.Tab("🎯 면접 질문 생성", elem_id="commonly-asked-tab"):
                create_commonly_asked_tab()
            
            with gr.Tab("💡 질문 추천", elem_id="question-recommendation-tab"):
                create_question_recommendation_tab()
            
            with gr.Tab("📋 직무기술서", elem_id="jd-recommendation-tab"):
                create_jd_recommendation_tab()
            
            with gr.Tab("🏷️ 산업 분류", elem_id="industry-classification-tab"):
                create_industry_classification_tab()
            
            with gr.Tab("📊 컨텍스트 리포트", elem_id="jasoseo-context-tab"):
                create_jasoseo_context_tab()
            
            with gr.Tab("🏢 기업 규모", elem_id="company-size-tab"):
                create_company_size_tab()
        
    return app

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
    
    print("\n📊 모듈 로드 상태:")
    for feature, available in available_features.items():
        print(f"  {'✅' if available else '❌'} {feature}")
    
    print("\n🚀 JasoSeo Agent 시작 중...")
    app = create_main_app()
    app.launch(share=True, show_error=True, debug=True) 