import os
import random
import datetime
import json
import multiprocessing
import sys
from tqdm import tqdm
from openai import OpenAI
import yaml

# 상위 디렉토리의 utils.py를 import하기 위해 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import track_api_cost
from llm_functions import generate_question_recommendation, parse_question_recommendation

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 테스트를 위한 환경 변수 로드 (필요시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 프롬프트 로드 (테스트용으로 llm_functions.py와 동일한 로직 사용)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, 'prompt.yaml')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
except Exception as e:
    print(f"Warning: prompt.yaml 로드 실패. 기본 프롬프트를 사용합니다. 오류: {e}")
    prompts = {
        'system_prompt': 'You are a helpful assistant that generates interview questions.',
        'user_prompt': 'Please generate interview questions for the following job description:\n\n{jd}'
    }

# 예제 데이터
example_jds = [
    "백엔드 개발자: Spring Boot, JPA, MySQL 경험자. MSA 환경 경험 우대. 클라우드(AWS) 환경 배포 및 운영 경험자. 책임감이 강하고 소통이 원활한 분.",
    "프론트엔드 개발자: React, TypeScript, Redux 사용. 반응형 웹 개발 경험 필수. UI/UX에 대한 이해도가 높은 분. RESTful API 연동 경험.",
    "데이터 분석가: SQL, Python(Pandas, Scikit-learn) 활용 능력. 통계적 지식과 데이터 시각화(Tableau 등) 능력. 가설 검증 및 A/B 테스트 경험자.",
    "프로덕트 매니저(PM): IT 프로덕트 기획 및 관리 경험. 사용자 스토리 작성, 백로그 관리. 데이터 기반 의사결정 능력. 개발자, 디자이너와 원활한 협업 능력.",
    "마케터: 디지털 마케팅(SA, DA, SEO) 경험. 콘텐츠 기획 및 제작, 성과 분석. SNS 채널 운영 경험. 최신 마케팅 트렌드에 밝은 분."
]

NUM_TESTS = 100
NUM_PROCESSES = 10
MODEL_NAME = "gpt-4o-mini" # llm_functions.py에서 사용하는 모델명과 일치

def run_test(test_input_with_id):
    """개별 테스트 케이스를 실행하는 워커 함수"""
    test_id, test_input = test_input_with_id
    total_cost = 0
    error_message = ""
    status = "✅ Success"

    try:
        response_text, response = generate_question_recommendation(client=client, prompts=prompts, **test_input)
        
        # 비용 계산
        if response and hasattr(response, 'usage'):
            total_cost = track_api_cost(response, MODEL_NAME, "high") # search_context_size high로 가정
        
        parsed_result = parse_question_recommendation(response_text)
        
        # 파싱 성공 여부 확인
        if "파싱에 실패했습니다" in str(parsed_result.get("recommended_question", "")):
            status = "❌ Parsing Failure"
            error_message = "파싱 실패"

        return {
            "id": test_id,
            "input": test_input,
            "raw_response": response_text,
            "parsed_result": parsed_result,
            "error": error_message,
            "cost": total_cost,
            "status": status,
        }
    except Exception as e:
        return {
            "id": test_id,
            "input": test_input,
            "raw_response": "",
            "parsed_result": {},
            "error": f"Exception: {str(e)}",
            "cost": total_cost,
            "status": "❌ Error"
        }

def main():
    """테스트를 준비, 실행하고 보고서를 생성하는 메인 함수"""
    print(f"총 {NUM_TESTS}개의 테스트를 {NUM_PROCESSES}개 프로세스로 병렬 실행합니다...")

    # 테스트 입력 데이터 생성 (llm_functions.py의 함수 인자에 맞춰 수정)
    test_inputs = []
    for i in range(NUM_TESTS):
        test_input = {
            "job_title": "임의 직무", # 함수 시그니처에는 있으나 프롬프트에서 미사용
            "company_name": "임의 회사", # 함수 시그니처에는 있으나 프롬프트에서 미사용
            "experience_level": "임의 경력", # 함수 시그니처에는 있으나 프롬프트에서 미사용
            "jd": random.choice(example_jds)
        }
        test_inputs.append((i + 1, test_input))

    # 멀티프로세싱 풀을 사용하여 테스트 실행
    results = []
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        with tqdm(total=NUM_TESTS, desc="면접 질문 추천 테스트") as pbar:
            for result in pool.imap_unordered(run_test, test_inputs):
                results.append(result)
                pbar.update()
    
    results.sort(key=lambda x: x['id'])
    print("모든 테스트가 완료되었습니다.")
    
    # --- 결과 분석 및 보고서 생성 ---
    now = datetime.datetime.now()
    report_filename = f"question_recommendation_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    
    failure_count = sum(1 for r in results if "Success" not in r["status"])
    total_cost = sum(r['cost'] for r in results)
    failure_rate = (failure_count / NUM_TESTS) * 100 if NUM_TESTS > 0 else 0

    html_template = """
    <!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>면접 질문 추천 테스트 보고서</title>
    <style>body{{font-family:sans-serif;margin:20px;}} h1,h2{{text-align:center;}} .summary{{border:1px solid #ddd;padding:20px;margin-bottom:20px;}} table{{width:100%;border-collapse:collapse;}} th,td{{border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top;}} th{{background-color:#f2f2f2;}} .status-success{{color:green;font-weight:bold;}} .status-failure{{color:red;font-weight:bold;}} pre{{white-space:pre-wrap;word-wrap:break-word;background-color:#f9f9f9;padding:10px;border:1px solid #ddd;}}</style>
    </head><body><h1>면접 질문 추천 테스트 보고서</h1><div class="summary"><h2>요약</h2><p><strong>테스트 시간:</strong> {now}</p><p><strong>총 테스트 수:</strong> {total_tests}</p><p><strong>성공:</strong> {success_count}</p><p><strong>실패/에러:</strong> {failure_count}</p><p><strong>실패율:</strong> <span class="{status_class}">{failure_rate:.2f}%</span></p><p><strong>총 예상 비용:</strong> ${total_cost:.6f}</p></div>
    <h2>상세 결과</h2><table><thead><tr><th>ID</th><th>입력 (JD)</th><th>Raw Response</th><th>파싱 결과</th><th>에러</th><th>비용</th><th>상태</th></tr></thead><tbody>{table_rows}</tbody></table></body></html>
    """

    table_rows_html = ""
    for res in results:
        status_class = "status-success" if "Success" in res["status"] else "status-failure"
        # 입력값에서 'jd'만 표시
        input_jd = res['input'].get('jd', 'N/A')
        table_rows_html += f"""
            <tr>
                <td>{res['id']}</td>
                <td><pre>{input_jd}</pre></td>
                <td><pre>{res['raw_response']}</pre></td>
                <td><pre>{json.dumps(res['parsed_result'], indent=2, ensure_ascii=False)}</pre></td>
                <td><pre>{res['error']}</pre></td>
                <td>${res['cost']:.6f}</td>
                <td class="{status_class}">{res['status']}</td>
            </tr>
    """

    final_html = html_template.format(
        now=now.strftime('%Y-%m-%d %H:%M:%S'),
        total_tests=NUM_TESTS,
        success_count=NUM_TESTS - failure_count,
        failure_count=failure_count,
        status_class="status-success" if failure_rate < 10 else "status-failure",
        failure_rate=failure_rate,
        total_cost=total_cost,
        table_rows=table_rows_html
    )

    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"'{report_filename}' 파일로 보고서가 저장되었습니다.")
    print(f"총 예상 비용: ${total_cost:.6f}")

if __name__ == "__main__":
    main()
