import os
import random
import datetime
import json
import multiprocessing
from tqdm import tqdm
from llm_functions import generate_context_report

# 테스트를 위한 환경 변수 로드 (필요시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 테스트 데이터
example_companies = ["토스", "삼성전자", "CJ제일제당", "하이브", "현대건설", "신한은행", "카카오", "네이버", "LG전자", "SK하이닉스", "쿠팡", "배달의민족", "당근마켓", "라인", "우아한형제들", "야놀자", "마켓컬리", "무신사", "29CM", "직방"]
example_jobs = ["백엔드 개발", "경영기획", "식품마케팅", "A&R", "HRM(인사운영)", "해외영업", "데이터 분석", "온라인마케팅", "기획", "개발", "프론트엔드 개발", "데이터 사이언티스트", "디자인", "재무", "프로덕트 매니저", "QA", "DevOps", "AI/ML 엔지니어", "UX/UI 디자이너", "콘텐츠 기획"]
experience_levels = ["신입", "경력", "인턴", "기타"]

NUM_TESTS = 1000
NUM_PROCESSES = 50

def validate_context_report_format(data):
    """
    컨텍스트 리포트 JSON 포맷이 올바른지 검증하는 함수
    
    Args:
        data (dict): 검증할 JSON 데이터
        
    Returns:
        tuple: (is_valid, error_messages)
            - is_valid (bool): 포맷이 올바른지 여부
            - error_messages (list): 오류 메시지 리스트
    """
    error_messages = []
    
    # 기본 타입 체크
    if not isinstance(data, dict):
        return False, ["데이터가 딕셔너리 타입이 아닙니다."]
    
    # 최상위 키 체크
    required_top_keys = ["company_profile", "position_analysis", "industry_context"]
    for key in required_top_keys:
        if key not in data:
            error_messages.append(f"필수 키 '{key}'가 없습니다.")
        elif not isinstance(data[key], dict):
            error_messages.append(f"'{key}'의 값이 딕셔너리 타입이 아닙니다.")
    
    # company_profile 검증
    if "company_profile" in data and isinstance(data["company_profile"], dict):
        cp = data["company_profile"]
        required_cp_keys = ["name", "vision_mission", "core_values", "talent_philosophy", "recent_news_summary", "main_products_services"]
        
        for key in required_cp_keys:
            if key not in cp:
                error_messages.append(f"company_profile에 필수 키 '{key}'가 없습니다.")
            elif key in ["core_values", "main_products_services"]:
                if not isinstance(cp[key], list):
                    error_messages.append(f"company_profile.{key}가 리스트 타입이 아닙니다.")
                elif len(cp[key]) == 0:
                    error_messages.append(f"company_profile.{key}가 빈 리스트입니다.")
            elif key in ["name", "vision_mission", "talent_philosophy", "recent_news_summary"]:
                if not isinstance(cp[key], str):
                    error_messages.append(f"company_profile.{key}가 문자열 타입이 아닙니다.")
                elif not cp[key].strip():
                    error_messages.append(f"company_profile.{key}가 빈 문자열입니다.")
    
    # position_analysis 검증
    if "position_analysis" in data and isinstance(data["position_analysis"], dict):
        pa = data["position_analysis"]
        required_pa_keys = ["role_summary", "required_skills", "keywords"]
        
        for key in required_pa_keys:
            if key not in pa:
                error_messages.append(f"position_analysis에 필수 키 '{key}'가 없습니다.")
        
        # role_summary 검증
        if "role_summary" in pa:
            if not isinstance(pa["role_summary"], str):
                error_messages.append("position_analysis.role_summary가 문자열 타입이 아닙니다.")
            elif not pa["role_summary"].strip():
                error_messages.append("position_analysis.role_summary가 빈 문자열입니다.")
        
        # required_skills 검증
        if "required_skills" in pa:
            if not isinstance(pa["required_skills"], dict):
                error_messages.append("position_analysis.required_skills가 딕셔너리 타입이 아닙니다.")
            else:
                rs = pa["required_skills"]
                for skill_type in ["hard", "soft"]:
                    if skill_type not in rs:
                        error_messages.append(f"position_analysis.required_skills에 '{skill_type}' 키가 없습니다.")
                    elif not isinstance(rs[skill_type], list):
                        error_messages.append(f"position_analysis.required_skills.{skill_type}가 리스트 타입이 아닙니다.")
                    elif len(rs[skill_type]) == 0:
                        error_messages.append(f"position_analysis.required_skills.{skill_type}가 빈 리스트입니다.")
        
        # keywords 검증
        if "keywords" in pa:
            if not isinstance(pa["keywords"], list):
                error_messages.append("position_analysis.keywords가 리스트 타입이 아닙니다.")
            elif len(pa["keywords"]) == 0:
                error_messages.append("position_analysis.keywords가 빈 리스트입니다.")
    
    # industry_context 검증
    if "industry_context" in data and isinstance(data["industry_context"], dict):
        ic = data["industry_context"]
        required_ic_keys = ["trends", "competitors"]
        
        for key in required_ic_keys:
            if key not in ic:
                error_messages.append(f"industry_context에 필수 키 '{key}'가 없습니다.")
            elif not isinstance(ic[key], list):
                error_messages.append(f"industry_context.{key}가 리스트 타입이 아닙니다.")
            elif len(ic[key]) == 0:
                error_messages.append(f"industry_context.{key}가 빈 리스트입니다.")
    
    is_valid = len(error_messages) == 0
    return is_valid, error_messages

def run_test(test_input_with_id):
    """개별 테스트 케이스를 실행하는 워커 함수"""
    test_id, test_input = test_input_with_id
    try:
        result, parsed_data, raw_content = generate_context_report(**test_input)
        
        # 포맷 검증
        is_valid, validation_errors = validate_context_report_format(parsed_data)
        
        if is_valid:
            status = "✅ Success"
        else:
            status = f"❌ Format Error: {'; '.join(validation_errors[:3])}{'...' if len(validation_errors) > 3 else ''}"
        
        return {
            "id": test_id,
            "input": test_input,
            "raw_output": result,
            "raw_content": raw_content,
            "parsed_result": parsed_data,
            "validation_errors": validation_errors,
            "status": status
        }
    except Exception as e:
        return {
            "id": test_id,
            "input": test_input,
            "raw_output": f"Error: {e}",
            "raw_content": "",
            "parsed_result": {},
            "validation_errors": [f"Exception: {str(e)}"],
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
            "job_title": job,
            "company_name": company,
            "experience_level": experience
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
    report_filename = f"context_report_test_{now.strftime('%Y%m%d_%H%M%S')}.html"
    error_count = sum(1 for r in results if "Success" not in r["status"])
    success_rate = ((NUM_TESTS - error_count) / NUM_TESTS) * 100

    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>컨텍스트 리포트 생성 테스트 보고서</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif; margin: 20px; color: #333; }}
            h1, h2 {{ text-align: center; color: #111;}}
            .summary {{ border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 20px; background-color: #fcfcfc; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            th, td {{ border: 1px solid #e0e0e0; padding: 12px; text-align: left; vertical-align: top; }}
            th {{ background-color: #f7f7f7; font-weight: 600; }}
            .status-success {{ color: #28a745; font-weight: bold; }} .status-failure {{ color: #dc3545; font-weight: bold; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f3f4f6; padding: 10px; border-radius: 5px; border: 1px solid #d1d5db; max-height: 300px; overflow-y: auto; }}
            .container {{ max-width: 1200px; margin: auto; }}
        </style>
    </head>
    <body>
    <div class="container">
        <h1>컨텍스트 리포트 생성 테스트 보고서</h1>
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
            <thead><tr><th>ID</th><th>입력 (Input)</th><th>원본 응답 (Raw Output)</th><th>AI 원본 응답 (Raw Content)</th><th>파싱 결과 (Parsed)</th><th>검증 오류 (Validation Errors)</th><th>상태 (Status)</th></tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
    </div>
    </body>
    </html>
    """

    table_rows_html = ""
    for res in results:
        status_class = "status-success" if "Success" in res["status"] else "status-failure"
        validation_errors_text = '\n'.join(res.get('validation_errors', []))
        table_rows_html += f"""
            <tr>
                <td>{res['id']}</td>
                <td><pre>{json.dumps(res['input'], indent=2, ensure_ascii=False)}</pre></td>
                <td><pre>{res['raw_output']}</pre></td>
                <td><pre>{res['raw_content']}</pre></td>
                <td><pre>{json.dumps(res['parsed_result'], indent=2, ensure_ascii=False)}</pre></td>
                <td><pre>{validation_errors_text}</pre></td>
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