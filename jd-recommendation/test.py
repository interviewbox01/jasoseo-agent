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
from llm_functions import generate_jd_recommendation

# 테스트를 위한 환경 변수 로드 (필요시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 예제 데이터
example_companies = ["삼성전자", "쿠팡", "하이브", "토스", "현대건설", "신한은행", "넥슨", "아모레퍼시픽", "삼성바이오로직스", "HMM", "카카오", "네이버", "LG전자", "SK하이닉스", "배달의민족"]
example_jobs = ["경영기획", "온라인마케팅", "HRM(인사운영)", "백엔드 개발", "해외영업", "데이터 분석", "영업", "마케팅", "기획", "개발", "프론트엔드 개발", "데이터 사이언티스트", "프로덕트 매니저"]
experience_levels = ["신입", "경력", "인턴", "기타"]

NUM_TESTS = 10
NUM_PROCESSES = 10
MODEL_NAME = "gpt-4o" # llm_functions.py에서 사용하는 모델명과 일치해야 함

def run_test(test_input_with_id):
    """개별 테스트 케이스를 실행하는 워커 함수"""
    test_id, test_input = test_input_with_id
    total_cost = 0
    error_message = ""
    status = "✅ Success"

    try:
        formatted_result, parsed_jd, response = generate_jd_recommendation(**test_input)
        
        # 비용 계산
        if response and hasattr(response, 'usage'):
            total_cost = track_api_cost(response, MODEL_NAME, None) # web search 안쓰므로 None
        
        # 파싱 성공 여부 확인
        if not parsed_jd or "파싱 오류" in str(parsed_jd) or "생성할 수 없습니다" in str(parsed_jd):
            status = "❌ Parsing Failure"
            error_message = str(parsed_jd)

        return {
            "id": test_id,
            "input": test_input,
            "formatted_result": formatted_result,
            "parsed_jd": parsed_jd if "❌" not in status else "",
            "error": error_message,
            "cost": total_cost,
            "status": status,
        }
    except Exception as e:
        return {
            "id": test_id,
            "input": test_input,
            "formatted_result": "",
            "parsed_jd": "",
            "error": f"Exception: {str(e)}",
            "cost": total_cost,
            "status": "❌ Error"
        }

def main():
    """테스트를 준비, 실행하고 보고서를 생성하는 메인 함수"""
    print(f"총 {NUM_TESTS}개의 테스트를 {NUM_PROCESSES}개 프로세스로 병렬 실행합니다...")

    # 테스트 입력 데이터 생성
    test_inputs = []
    for i in range(NUM_TESTS):
        company = random.choice(example_companies)
        job = random.choice(example_jobs)
        experience = random.choice(experience_levels)
        
        test_input = {
            "company_name": company, "job_title": job, "experience_level": experience
        }
        test_inputs.append((i + 1, test_input))

    # 멀티프로세싱 풀을 사용하여 테스트 실행
    results = []
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        with tqdm(total=NUM_TESTS, desc="JD 추천 테스트 진행 중") as pbar:
            for result in pool.imap_unordered(run_test, test_inputs):
                results.append(result)
                pbar.update()
    
    # ID 순으로 결과 정렬
    results.sort(key=lambda x: x['id'])

    print("모든 테스트가 완료되었습니다.")
    
    # --- 결과 분석 및 보고서 생성 ---
    now = datetime.datetime.now()
    report_filename = f"jd_recommendation_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    
    failure_count = sum(1 for r in results if "Success" not in r["status"])
    total_cost = sum(r['cost'] for r in results)
    failure_rate = (failure_count / NUM_TESTS) * 100 if NUM_TESTS > 0 else 0

    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>JD 추천 생성 테스트 보고서</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif; margin: 20px; color: #333; }}
            h1, h2 {{ text-align: center; color: #111;}}
            .summary {{ border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 20px; background-color: #fcfcfc; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            th, td {{ border: 1px solid #e0e0e0; padding: 12px; text-align: left; vertical-align: top; }}
            th {{ background-color: #f7f7f7; font-weight: 600; }}
            .status-success {{ color: #28a745; font-weight: bold; }} .status-failure {{ color: #dc3545; font-weight: bold; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f3f4f6; padding: 10px; border-radius: 5px; border: 1px solid #d1d5db; max-height: 400px; overflow-y: auto;}}
            .container {{ max-width: 1400px; margin: auto; }}
        </style>
    </head>
    <body>
    <div class="container">
        <h1>JD 추천 생성 테스트 보고서</h1>
        <div class="summary">
            <h2>요약</h2>
            <p><strong>테스트 시간:</strong> {now}</p>
            <p><strong>총 테스트 수:</strong> {total_tests}</p>
            <p><strong>성공:</strong> {success_count}</p>
            <p><strong>실패/에러:</strong> {failure_count}</p>
            <p><strong>실패율:</strong> <span class="{status_class}">{failure_rate:.2f}%</span></p>
            <p><strong>총 예상 비용:</strong> ${total_cost:.6f}</p>
        </div>
        <h2>상세 결과</h2>
        <table>
            <thead><tr><th>ID</th><th>입력 (Input)</th><th>포맷팅된 결과</th><th>파싱된 JD 원본</th><th>에러</th><th>비용</th><th>상태</th></tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
    </div>
    </body>
    </html>
    """

    table_rows_html = ""
    for res in results:
        status_class = "status-success" if "Success" in res["status"] else "status-failure"
        table_rows_html += f"""
            <tr>
                <td>{res['id']}</td>
                <td><pre>{json.dumps(res['input'], indent=2, ensure_ascii=False)}</pre></td>
                <td><pre>{res['formatted_result']}</pre></td>
                <td><pre>{res['parsed_jd']}</pre></td>
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