import os
import random
import datetime
import json
import multiprocessing
from tqdm import tqdm
from llm_functions import generate_interview_questions

# 테스트를 위한 환경 변수 로드 (필요시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 테스트 데이터
example_companies = ["삼성전자", "토스", "카카오", "네이버", "LG전자", "현대자동차", "CJ제일제당", "하이브", "쿠팡", "배달의민족", "SK하이닉스", "당근마켓"]
example_jobs = ["백엔드 개발", "프론트엔드 개발", "데이터 사이언티스트", "마케팅", "영업", "기획", "디자인", "HR", "재무", "A&R", "프로덕트 매니저"]
experience_levels = ["신입", "경력(3~5년)", "인턴", "시니어(5년 이상)"]
common_questions_list = [
    "자기소개를 해보세요", "지원 동기가 무엇인가요", "본인의 강점은 무엇인가요",
    "가장 도전적인 경험은 무엇인가요", "성공 경험을 말해주세요", "실패 경험을 말해주세요",
    "입사 후 포부는 무엇인가요", "성격의 장단점을 말해주세요", "존경하는 인물은 누구인가요",
    "마지막으로 하고 싶은 말은?", "스트레스는 어떻게 해소하나요?", "협업 경험에 대해 말해주세요"
]

NUM_TESTS = 100
NUM_PROCESSES = 10

def run_test(test_input_with_id):
    """개별 테스트 케이스를 실행하는 워커 함수"""
    test_id, test_input = test_input_with_id
    try:
        _, parsed_questions, raw_output = generate_interview_questions(**test_input)
        is_success = isinstance(parsed_questions, list) and len(parsed_questions) > 0
        
        return {
            "id": test_id,
            "input": test_input,
            "raw_output": raw_output,
            "parsed_result": parsed_questions,
            "status": "✅ Success" if is_success else "❌ Failure"
        }
    except Exception as e:
        return {
            "id": test_id,
            "input": test_input,
            "raw_output": f"Error: {e}",
            "parsed_result": [],
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
        common_questions = random.sample(common_questions_list, random.randint(2, 5))
        num_to_generate = random.randint(3, 5)
        
        test_input = {
            "company_name": company, "job_title": job, "experience_level": experience,
            "selected_questions": ", ".join(common_questions), "num_questions": num_to_generate
        }
        test_inputs.append((i + 1, test_input))

    # 멀티프로세싱 풀을 사용하여 테스트 실행
    results = []
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        with tqdm(total=NUM_TESTS, desc="테스트 진행 중") as pbar:
            for result in pool.imap_unordered(run_test, test_inputs):
                results.append(result)
                pbar.update()
    
    # ID 순으로 결과 정렬
    results.sort(key=lambda x: x['id'])

    print("모든 테스트가 완료되었습니다.")
    
    # --- HTML 보고서 생성 ---
    now = datetime.datetime.now()
    report_filename = f"parsing_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    error_count = sum(1 for r in results if "Success" not in r["status"])
    success_rate = ((NUM_TESTS - error_count) / NUM_TESTS) * 100

    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>파싱 테스트 보고서</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif; margin: 20px; color: #333; }}
            h1, h2 {{ text-align: center; color: #111;}}
            .summary {{ border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 20px; background-color: #fcfcfc; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            th, td {{ border: 1px solid #e0e0e0; padding: 12px; text-align: left; vertical-align: top; }}
            th {{ background-color: #f7f7f7; font-weight: 600; }}
            .status-success {{ color: #28a745; font-weight: bold; }} .status-failure {{ color: #dc3545; font-weight: bold; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f3f4f6; padding: 10px; border-radius: 5px; border: 1px solid #d1d5db; }}
            .container {{ max-width: 1200px; margin: auto; }}
        </style>
    </head>
    <body>
    <div class="container">
        <h1>LLM 응답 파싱 테스트 보고서</h1>
        <div class="summary">
            <h2>요약</h2>
            <p><strong>테스트 시간:</strong> {now}</p>
            <p><strong>총 테스트 수:</strong> {total_tests}</p>
            <p><strong>성공:</strong> {success_count}</p>
            <p><strong>실패/에러:</strong> {error_count}</p>
            <p><strong>성공률:</strong> <span class="{status_class}">{success_rate:.2f}%</span></p>
        </div>
        <h2>상세 결과</h2>
        <table>
            <thead><tr><th>ID</th><th>입력 (Input)</th><th>원본 응답 (Raw Output)</th><th>파싱 결과 (Parsed)</th><th>상태 (Status)</th></tr></thead>
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
                <td><pre>{res['raw_output']}</pre></td>
                <td><pre>{json.dumps(res['parsed_result'], indent=2, ensure_ascii=False)}</pre></td>
                <td class="{status_class}">{res['status']}</td>
            </tr>
    """

    final_html = html_template.format(
        now=now.strftime('%Y-%m-%d %H:%M:%S'),
        total_tests=NUM_TESTS,
        success_count=NUM_TESTS - error_count,
        error_count=error_count,
        status_class="status-success" if success_rate > 90 else "status-failure",
        success_rate=success_rate,
        table_rows=table_rows_html
    )

    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"'{report_filename}' 파일로 보고서가 저장되었습니다.")

if __name__ == "__main__":
    main()
