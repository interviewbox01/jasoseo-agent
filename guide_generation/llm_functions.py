from openai import OpenAI
from dotenv import load_dotenv
import yaml
import os
import json
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# load prompt
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, 'prompt.yaml')
    with open(prompt_path, "r", encoding='utf-8') as file:
        prompt = yaml.safe_load(file)["prompt"]
except Exception as e:
    print(f"Warning: prompt.yaml 로드 실패. 기본 프롬프트를 사용합니다. 오류: {e}")
    prompt = "Question: {question}\nJD: {jd}\nCompany: {company_name}\nExperience: {experience_level}\nGenerate a guide based on this information in markdown table format."


def parse_json_from_response(text: str) -> dict | None:
    """
    Markdown 코드 블록 안에 포함될 수 있는 JSON 문자열을 추출하고 파싱합니다.
    
    Deprecated: 이 함수는 JSON 파싱용이므로 guide generation에서는 더 이상 사용되지 않습니다.

    Args:
        text (str): LLM이 반환한 전체 텍스트 응답.

    Returns:
        dict | None: 파싱된 딕셔너리 객체, 또는 실패 시 None.
    """
    if not text:
        return None

    # ```json ... ``` 또는 ``` ... ``` 형식의 코드 블록에서 JSON 추출
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        json_str = match.group(1)
    else:
        # 코드 블록이 없다면, 전체 텍스트를 JSON으로 가정
        json_str = text

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 전체 파싱이 실패하면, 첫 '{'와 마지막 '}'를 기준으로 다시 시도
        start_index = json_str.find('{')
        end_index = json_str.rfind('}')
        if start_index != -1 and end_index != -1 and start_index < end_index:
            potential_json = json_str[start_index:end_index+1]
            try:
                return json.loads(potential_json)
            except json.JSONDecodeError:
                pass  # 이마저도 실패하면 그냥 None 반환

    return None

def parse_markdown_table_from_response(text: str) -> str:
    """
    LLM 응답에서 마크다운 테이블을 추출하여 반환합니다.
    
    Args:
        text (str): LLM이 반환한 전체 텍스트 응답.
        
    Returns:
        str: 추출된 마크다운 테이블 문자열, 실패 시 전체 텍스트 반환
    """
    if not text:
        return ""
    
    # 마크다운 코드 블록에서 테이블 추출 시도
    markdown_match = re.search(r"```(?:markdown)?\s*([\s\S]*?)\s*```", text)
    if markdown_match:
        return markdown_match.group(1).strip()
    
    # 테이블 패턴 직접 찾기 (| ... | ... | 형태)
    lines = text.split('\n')
    table_lines = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        if '|' in line and ('단계' in line or '---' in line or '①' in line):
            in_table = True
            table_lines.append(line)
        elif in_table and '|' in line:
            table_lines.append(line)
        elif in_table and not line:
            # 빈 줄이면 테이블 끝
            break
    
    if table_lines:
        return '\n'.join(table_lines)
    
    # 테이블을 찾지 못했으면 전체 텍스트 반환
    return text.strip()

def generate_guide(question, jd, company_name, experience_level):
    """
    자기소개서 문항 가이드를 생성하고, 마크다운 테이블과 전체 응답 객체를 반환하는 함수
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt.format(question=question, jd=jd, company_name=company_name, experience_level=experience_level)}],
            # response_format을 제거하여 일반 텍스트 응답을 받음
        )
        
        # 마크다운 테이블 파싱
        guide_content = parse_markdown_table_from_response(response.choices[0].message.content)
        
        # 호환성을 위해 딕셔너리 형태로 반환
        guide_dict = {"guide": guide_content}
        return guide_dict, response

    except Exception as e:
        print(f"가이드 생성 또는 파싱 중 오류 발생: {e}")
        return {"error": f"Failed to generate or parse guide: {str(e)}", "guide": ""}, None


if __name__ == "__main__":
    example_input = {
        "question": "삼성전자를 지원한 이유와 입사 후 이루고 싶은 꿈을 기술하시오.",
        "jd": "삼성전자는 세계적인 기술 기업으로, 다양한 분야에서 선도적인 기술을 개발하고 있습니다. 프론트엔드 개발자로 입사하면 다양한 프로젝트에 참여하며, 최신 기술을 적용하여 사용자 경험을 개선할 수 있습니다.",
        "company_name": "삼성전자",
        "experience_level": "신입"
    }
    guide_dict, _ = generate_guide(**example_input)
    print("Guide content:")
    print(guide_dict.get("guide", "No guide generated"))