import os
import json
import re
import yaml
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 프롬프트 템플릿 로드
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(current_dir, 'prompt.yaml')
with open(prompt_path, 'r', encoding='utf-8') as f:
    prompt_data = yaml.safe_load(f)
    prompt_template = prompt_data['prompt']

def parse_prediction(content):
    """
    AI 응답에서 JSON 형식의 면접 질문을 파싱하는 간단한 함수
    """
    try:
        # 1. JSON 코드 블록(```json ... ```)을 찾아 파싱합니다.
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            if 'sample_questions' in data and isinstance(data['sample_questions'], list):
                return data['sample_questions']

        # 2. 코드 블록이 없다면, 응답 전체를 JSON으로 파싱 시도합니다.
        cleaned_content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_content)
        if 'sample_questions' in data and isinstance(data['sample_questions'], list):
            return data['sample_questions']


    except Exception as e:
        print(f"An unexpected error occurred during parsing: {e}")

    # 모든 방법이 실패하면 빈 리스트를 반환합니다.
    return []

def parse_prediction_complex(content):
    """
    AI 응답에서 JSON 형식의 면접 질문을 파싱하는 함수
    """
    try:
        print(f"파싱할 컨텐츠 길이: {len(content)}")
        print(f"파싱할 컨텐츠 첫 200자: {repr(content[:200])}")
        
        # 텍스트 전처리 - 불필요한 공백과 특수문자 제거
        cleaned_content = content.strip()
        
        # 1. JSON 코드 블록 찾기 (```json ... ``` 형식)
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```'
        ]
        
        for pattern in json_patterns:
            json_match = re.search(pattern, cleaned_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                print(f"JSON 블록 발견: {repr(json_str[:100])}")
                
                # JSON 문자열 정리
                json_str = re.sub(r'\n\s*', ' ', json_str)  # 줄바꿈과 공백 정리
                json_str = re.sub(r',\s*}', '}', json_str)  # 마지막 콤마 제거
                json_str = re.sub(r',\s*]', ']', json_str)  # 배열 마지막 콤마 제거
                
                try:
                    parsed_json = json.loads(json_str)
                    if 'sample_questions' in parsed_json:
                        return parsed_json['sample_questions']
                except json.JSONDecodeError as e:
                    print(f"JSON 블록 파싱 실패: {e}")
                    print(f"실패한 JSON: {repr(json_str)}")
        
        # 2. 중괄호로 둘러싸인 전체 JSON 찾기
        brace_patterns = [
            r'\{[^{}]*"sample_questions"[^{}]*\[[^\]]*\][^{}]*\}',
            r'\{.*?"sample_questions".*?\[.*?\].*?\}'
        ]
        
        for pattern in brace_patterns:
            brace_match = re.search(pattern, cleaned_content, re.DOTALL)
            if brace_match:
                json_str = brace_match.group(0).strip()
                print(f"중괄호 JSON 발견: {repr(json_str[:100])}")
                
                # JSON 문자열 정리
                json_str = re.sub(r'\n\s*', ' ', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                
                try:
                    parsed_json = json.loads(json_str)
                    if 'sample_questions' in parsed_json:
                        return parsed_json['sample_questions']
                except json.JSONDecodeError as e:
                    print(f"중괄호 JSON 파싱 실패: {e}")
        
        # 3. sample_questions 배열만 직접 찾기
        array_patterns = [
            r'"sample_questions"\s*:\s*\[(.*?)\]',
            r'sample_questions\s*:\s*\[(.*?)\]'
        ]
        
        for pattern in array_patterns:
            array_match = re.search(pattern, cleaned_content, re.DOTALL)
            if array_match:
                array_content = array_match.group(1).strip()
                print(f"배열 내용 발견: {repr(array_content[:100])}")
                
                # 배열 내용에서 문자열 추출
                questions = []
                # 따옴표로 둘러싸인 문자열들 찾기
                question_matches = re.findall(r'"([^"]+)"', array_content)
                for q in question_matches:
                    if len(q.strip()) > 10:  # 의미있는 길이의 질문만
                        questions.append(q.strip())
                
                if questions:
                    return questions
        
        # 4. 전체 텍스트를 JSON으로 파싱 시도
        try:
            # 코드 블록 마커 제거
            if cleaned_content.startswith('```'):
                lines = cleaned_content.split('\n')
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = len(lines)
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip() == '```':
                        end_idx = i
                        break
                cleaned_content = '\n'.join(lines[start_idx:end_idx])
            
            cleaned_content = cleaned_content.strip()
            parsed_json = json.loads(cleaned_content)
            if 'sample_questions' in parsed_json:
                return parsed_json['sample_questions']
        except json.JSONDecodeError as e:
            print(f"전체 JSON 파싱 실패: {e}")
        
        # 5. 최후의 수단: 패턴 매칭으로 질문 추출
        print("패턴 매칭으로 질문 추출 시도")
        questions = []
        
        # 다양한 패턴으로 질문 찾기
        patterns = [
            r'"([^"]{20,}[?])"',  # 따옴표 안의 물음표로 끝나는 긴 문장
            r'"([^"]{20,})"',     # 따옴표 안의 긴 문장
            r'[1-9]\.\s*([^"\n]{20,}[?])',  # 번호. 질문 형태
            r'[1-9]\.\s*([^"\n]{20,})',     # 번호. 문장 형태
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, cleaned_content)
            for match in matches:
                question = match.strip()
                if len(question) > 15 and question not in questions:
                    questions.append(question)
                    if len(questions) >= 5:  # 최대 5개
                        break
            if questions:
                break
        
        return questions[:5] if questions else []
        
    except Exception as e:
        print(f"JSON 파싱 전체 오류: {e}")
        print(f"파싱 실패한 컨텐츠: {repr(content)}")
        return []

def generate_interview_questions(company_name, job_title, experience_level, selected_questions, num_questions=3):
    """
    OpenAI API를 사용하여 맞춤형 면접 질문을 생성하는 함수
    """
    # try:
    if True:
        if not company_name or not job_title or not experience_level or not selected_questions:
            return "모든 필드를 입력해주세요.", []
        
        # 선택된 질문들을 리스트로 변환
        if isinstance(selected_questions, str):
            common_questions = [q.strip() for q in selected_questions.split(',')]
        else:
            common_questions = selected_questions
        
        # 프롬프트 생성
        prompt = prompt_template.format(
            company_name=company_name,
            job_title=job_title,
            experience_level=experience_level,
            common_questions=common_questions,
            num_questions=num_questions
        )
        
        print(prompt)
        # OpenAI Responses API 호출 (Web Search Preview 사용)
        response = client.responses.create(
            model="gpt-4o",
            tools=[{
                "type": "web_search_preview",
                "search_context_size": "high",
            }],
            input=f"당신은 면접 질문 생성 전문가입니다. 웹 검색을 통해 최신 기업 정보와 채용 동향을 확인하고 주어진 조건에 맞는 구체적이고 실용적인 면접 질문을 생성해주세요.\n\n{prompt}"
        )
        
        content = response.output_text
        print(f"=== AI 응답 원본 ===")
        print(content)
        print(f"=== 전체 응답 객체 ===")
        print(response)
        
        # 웹 검색 참고 링크 출력
        if hasattr(response, 'web_search_results') and response.web_search_results:
            print(f"=== 참고한 웹 검색 링크 ===")
            for i, result in enumerate(response.web_search_results, 1):
                if hasattr(result, 'url'):
                    print(f"{i}. {result.url}")
                elif hasattr(result, 'link'):
                    print(f"{i}. {result.link}")
        
        print(f"=== AI 응답 끝 ===")
        questions = parse_prediction(content)
        
        if not questions:
            return "질문 생성에 실패했습니다. 다시 시도해주세요.", []
        
        # 결과 포맷팅
        result = f"""## 🎯 {company_name} - {job_title} 맞춤형 면접 질문

### 📋 **생성된 질문들**

"""
        for i, question in enumerate(questions, 1):
            result += f"**{i}.** {question}\n\n"
        
        result += f"""
---
**📝 입력 정보:**
- 회사: {company_name}
- 직무: {job_title}  
- 경력: {experience_level}
- 생성된 질문 수: {len(questions)}개 (요청: {num_questions}개)
- 참고 질문 수: {len(common_questions)}개

*본 질문들은 AI가 생성한 것으로, 실제 면접과 다를 수 있습니다.*
"""
        
        return result, questions, content
        
#     except Exception as e:
#         error_msg = f"""## ❌ 오류 발생

# 질문 생성 중 오류가 발생했습니다.

# **오류 내용:** {str(e)}

# 다시 시도해주세요.
# """
#         return error_msg, []

if __name__ == "__main__":
    company_name = "카카오"
    job_title = "백엔드 개발"
    experience_level = "신입"
    selected_questions = "자기소개를 해보세요, 지원 동기가 무엇인가요, 가장 도전적인 경험은 무엇인가요, 입사 후 포부는 무엇인가요"
    num_questions = 3
    result, questions, raw_content = generate_interview_questions(company_name, job_title, experience_level, selected_questions, num_questions)
    print(result)
    print(questions)
    print(f"=== 원본 응답 ===")
    print(raw_content)