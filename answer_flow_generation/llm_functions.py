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
    prompt = """
You are an expert resume consultant. Based on the provided guide and user's experiences, create a logical and persuasive story flow for a cover letter answer.

### Guide
{guide}

### User's Experiences
{user_experiences}

Please generate a step-by-step answer flow in JSON format, like {"answer_flow": ["Step 1:...", "Step 2:...", "Step 3:...", "Step 4:..."]}.
"""

def parse_markdown_table_from_response(text: str) -> str | None:
    """
    LLM 응답에서 markdown table을 추출합니다.

    Args:
        text (str): LLM이 반환한 전체 텍스트 응답.

    Returns:
        str | None: 추출된 markdown table 문자열, 또는 실패 시 None.
    """
    if not text:
        return None

    # ```markdown ... ``` 형식의 코드 블록에서 table 추출
    markdown_match = re.search(r"```markdown\s*([\s\S]*?)\s*```", text)
    if markdown_match:
        table_content = markdown_match.group(1).strip()
        return table_content
    
    # 코드 블록이 없다면, 전체 텍스트에서 table 찾기
    lines = text.strip().split('\n')
    table_lines = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            table_lines.append(line)
    
    if len(table_lines) >= 3:  # header, separator, at least one row
        return '\n'.join(table_lines)
    
    return None

def parse_json_from_response(text: str) -> dict | None:
    """
    Markdown 코드 블록 안에 포함될 수 있는 JSON 문자열을 추출하고 파싱합니다.
    (이전 버전과의 호환성을 위해 유지)

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

def generate_answer_flow(question, jd, company_name, experience_level, conversation):
    """
    답변 흐름(개요)을 생성하고, 파싱된 결과와 전체 응답 객체를 반환하는 함수
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt.format(
                question=question,
                jd=jd,
                company_name=company_name,
                experience_level=experience_level,
                conversation=conversation
            )}],
            # JSON 형태가 아니라 markdown table 형태로 응답 받기
        )
        
        # Markdown table 응답 파싱
        markdown_table = parse_markdown_table_from_response(response.choices[0].message.content)
        
        if markdown_table:
            parsed_content = {"flow": markdown_table}
        else:
            parsed_content = {"error": "Failed to parse markdown table"}
            
        return parsed_content, response

    except Exception as e:
        print(f"답변 흐름 생성 또는 파싱 중 오류 발생: {e}")
        return {"error": f"Failed to generate or parse flow: {str(e)}"}, None

if __name__ == "__main__":
    example_input = {
        "question": "삼성전자를 지원한 이유와 입사 후 이루고 싶은 꿈을 기술하시오.",
        "jd": "삼성전자는 세계적인 기술 기업으로, 다양한 분야에서 선도적인 기술을 개발하고 있습니다. 프론트엔드 개발자로 입사하면 다양한 프로젝트에 참여하며, 최신 기술을 적용하여 사용자 경험을 개선할 수 있습니다.",
        "company_name": "삼성전자",
        "experience_level": "신입",
        "conversation": "User: 안녕하세요, 삼성전자 프론트엔드 개발 직무에 지원하려고 합니다.\nAI: 네, 어떤 점이 궁금하신가요?\nUser: 자기소개서에 어떤 경험을 강조하면 좋을까요?\nAI: 프로젝트 경험에서 사용한 기술 스택과 성과를 구체적으로 작성하는 것이 좋습니다."
    }
    
    flow_json, _ = generate_answer_flow(**example_input)
    print(json.dumps(flow_json, indent=2, ensure_ascii=False))
