import os
import random
import datetime
import json
import multiprocessing
import sys
from tqdm import tqdm

# 상위 디렉토리의 utils.py를 import하기 위해 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import track_api_cost
from llm_functions import generate_answer_flow

# 테스트를 위한 환경 변수 로드 (필요시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 예제 데이터
example_companies = ["삼성전자", "카카오", "네이버", "쿠팡", "토스", "현대자동차", "CJ제일제당", "하이브"]
example_jobs_jds = {
    "백엔드 개발자": "Spring Boot, JPA, MySQL 경험자. MSA 환경 경험 우대. 클라우드(AWS) 환경 배포 및 운영 경험자.",
    "프론트엔드 개발자": "React, TypeScript, Redux 사용. 반응형 웹 개발 경험 필수. UI/UX에 대한 이해도가 높은 분.",
    "데이터 분석가": "SQL, Python(Pandas, Scikit-learn) 활용 능력. 통계적 지식과 데이터 시각화(Tableau 등) 능력.",
    "프로덕트 매니저(PM)": "IT 프로덕트 기획 및 관리 경험. 사용자 스토리 작성, 백로그 관리. 데이터 기반 의사결정 능력.",
    "마케터": "디지털 마케팅(SA, DA, SEO) 경험. 콘텐츠 기획 및 제작, 성과 분석. SNS 채널 운영 경험."
}
example_questions = {
    "지원동기": "{company_name}에 지원한 동기에 대해 기술해주십시오.",
    "성장과정": "본인의 성장과정을 간략히 기술하되 현재의 자신에게 가장 큰 영향을 끼친 사건, 인물 등을 포함하여 기술해주십시오.",
    "직무역량": "{job_title} 직무 수행에 필요한 역량은 무엇이라고 생각하며, 이를 갖추기 위해 어떤 노력을 해왔는지 기술해주십시오.",
    "입사후포부": "입사 후 10년 동안의 회사생활 시나리오와 그것을 추구하는 이유를 기술해주십시오."
}
experience_levels = ["신입", "경력", "인턴"]
example_conversations = [
    "User: 안녕하세요, 자기소개서 컨설팅을 받고 싶습니다.\nAI: 네, 어떤 직무와 회사에 지원하시나요?\nUser: 쿠팡의 PM 직무입니다. 제 강점은 데이터 분석 능력입니다.",
    "User: 성장과정 항목은 어떻게 쓰는 게 좋을까요?\nAI: 직무와 관련된 경험을 중심으로, 그 경험을 통해 무엇을 배우고 어떻게 성장했는지 구체적인 사례를 들어 작성하는 것이 중요합니다.",
    "User: 제 경험 중 어떤 것을 강조해야 할지 모르겠어요.\nAI: 지원하시는 직무의 JD(직무기술서)를 보면 어떤 역량을 중요하게 생각하는지 알 수 있습니다. 그와 관련된 경험을 우선적으로 어필해보세요."
]

NUM_TESTS = 100
NUM_PROCESSES = 10
MODEL_NAME = "gpt-4o-mini"

def run_test(test_input_with_id):
    """개별 테스트 케이스를 실행하는 워커 함수"""
    test_id, test_input = test_input_with_id
    total_cost = 0
    error_message = ""
    status = "✅ Success"

    try:
        parsed_flow, response = generate_answer_flow(**test_input)
        
        if response and hasattr(response, 'usage'):
            total_cost = track_api_cost(response, MODEL_NAME, None)
        
        if "error" in parsed_flow or "flow" not in parsed_flow or not parsed_flow["flow"]:
            status = "❌ Failure"
            error_message = str(parsed_flow.get("error", "Invalid flow format"))

        return {
            "id": test_id,
            "input": test_input,
            "parsed_result": parsed_flow,
            "error": error_message,
            "cost": total_cost,
            "status": status,
        }
    except Exception as e:
        return {
            "id": test_id,
            "input": test_input,
            "parsed_result": {},
            "error": f"Exception: {str(e)}",
            "cost": total_cost,
            "status": "❌ Error"
        }

def main():
    """테스트를 준비, 실행하고 보고서를 생성하는 메인 함수"""
    print(f"총 {NUM_TESTS}개의 테스트를 {NUM_PROCESSES}개 프로세스로 병렬 실행합니다...")

    test_inputs = []
    for i in range(NUM_TESTS):
        company = random.choice(example_companies)
        job_title, jd = random.choice(list(example_jobs_jds.items()))
        question_template = random.choice(list(example_questions.values()))
        question = question_template.format(company_name=company, job_title=job_title)
        experience = random.choice(experience_levels)
        conversation = random.choice(example_conversations)
        
        test_input = {
            "company_name": company,
            "jd": jd,
            "question": question,
            "experience_level": experience,
            "conversation": conversation
        }
        test_inputs.append((i + 1, test_input))

    results = []
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        with tqdm(total=NUM_TESTS, desc="답변 흐름 생성 테스트") as pbar:
            for result in pool.imap_unordered(run_test, test_inputs):
                results.append(result)
                pbar.update()
    
    results.sort(key=lambda x: x['id'])
    print("모든 테스트가 완료되었습니다.")
    
    now = datetime.datetime.now()
    report_filename = f"answer_flow_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    
    failure_count = sum(1 for r in results if "Success" not in r["status"])
    total_cost = sum(r['cost'] for r in results)
    failure_rate = (failure_count / NUM_TESTS) * 100 if NUM_TESTS > 0 else 0

    html_template = """
    <!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>답변 흐름 생성 테스트 보고서</title>
    <style>body{{font-family:sans-serif;margin:20px;}} h1,h2{{text-align:center;}} .summary{{border:1px solid #ddd;padding:20px;margin-bottom:20px;}} table{{width:100%;border-collapse:collapse;}} th,td{{border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top;}} th{{background-color:#f2f2f2;}} .status-success{{color:green;font-weight:bold;}} .status-failure{{color:red;font-weight:bold;}} pre{{white-space:pre-wrap;word-wrap:break-word;background-color:#f9f9f9;padding:10px;border:1px solid #ddd;}} .container{{max-width:1400px;margin:auto;}}</style>
    </head><body><div class="container"><h1>답변 흐름 생성 테스트 보고서</h1><div class="summary"><h2>요약</h2><p><strong>테스트 시간:</strong> {now}</p><p><strong>총 테스트 수:</strong> {total_tests}</p><p><strong>성공:</strong> {success_count}</p><p><strong>실패/에러:</strong> {failure_count}</p><p><strong>실패율:</strong> <span class="{status_class}">{failure_rate:.2f}%</span></p><p><strong>총 예상 비용:</strong> ${total_cost:.6f}</p></div>
    <h2>상세 결과</h2><table><thead><tr><th>ID</th><th>입력 (Input)</th><th>파싱 결과 (Parsed)</th><th>에러</th><th>비용</th><th>상태</th></tr></thead><tbody>{table_rows}</tbody></table></div></body></html>
    """

    table_rows_html = ""
    for res in results:
        status_class = "status-success" if "Success" in res["status"] else "status-failure"
        table_rows_html += f"""
            <tr>
                <td>{res['id']}</td>
                <td><pre>{json.dumps(res['input'], indent=2, ensure_ascii=False)}</pre></td>
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
