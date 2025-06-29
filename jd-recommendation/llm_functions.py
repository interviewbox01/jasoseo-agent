import os
import json
import re
import yaml
from openai import OpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 프롬프트 템플릿 로드
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(current_dir, 'prompt.yaml')
with open(prompt_path, 'r', encoding='utf-8') as f:
    prompt_data = yaml.safe_load(f)
    prompt_template = prompt_data['prompt']

def parse_jd_recommendation(content):
    """
    AI 응답에서 직무기술서 JSON을 파싱하는 함수
    """
    try:
        print(f"파싱할 컨텐츠 길이: {len(content)}")
        print(f"파싱할 컨텐츠 첫 200자: {repr(content[:200])}")
        
        # 텍스트 전처리
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
                json_str = re.sub(r'\n\s*', ' ', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                
                parsed_json = json.loads(json_str)
                if isinstance(parsed_json, dict) and 'recommended_jd' in parsed_json:
                    return parsed_json['recommended_jd']
        
    except Exception as e:
        print(f"JD 파싱 전체 오류: {e}")
        print(f"파싱 실패한 컨텐츠: {repr(content)}")
        return f"파싱 오류: {str(e)}"

def generate_jd_recommendation(job_title, company_name, experience_level):
    """
    OpenAI API를 사용하여 직무기술서를 생성하는 함수
    """
    try:
        if not job_title or not company_name or not experience_level:
            return "직무, 회사명, 경력 수준을 모두 입력해주세요.", "", None
        
        # 프롬프트 생성
        prompt = prompt_template.format(
            job_title=job_title,
            company_name=company_name,
            experience_level=experience_level
        )
        
        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 채용 공고 작성 전문가입니다. 정확한 JSON 형식으로 직무기술서를 제공해주세요."},
                {"role": "user", "content": prompt}
            ],
        )
        
        content = response.choices[0].message.content
        print(f"=== AI 응답 원본 ===")
        print(content)
        print(f"=== AI 응답 끝 ===")
        
        jd_content = parse_jd_recommendation(content)
        
        if not jd_content or jd_content == "직무기술서를 생성할 수 없습니다.":
            return "직무기술서 생성에 실패했습니다. 다시 시도해주세요.", "", None
        
        # 결과 포맷팅
        result = f"""## 📋 {company_name} - {job_title} 직무기술서

### 💼 **추천 직무기술서**

{jd_content}

---

### 📊 **직무 정보 요약**

**🏢 회사:** {company_name}  
**💼 직무:** {job_title}  
**📈 경력:** {experience_level}  

### 💡 **자소서 작성 팁**

위 직무기술서를 참고하여 다음 사항을 자소서에 반영해보세요:

1. **핵심 업무**: 언급된 주요 업무와 관련된 경험이나 역량을 강조
2. **요구 스킬**: 필요한 기술이나 능력에 대한 본인의 준비도를 어필
3. **회사 특성**: 해당 회사의 사업 영역과 연관된 관심사나 경험을 언급
4. **성장 의지**: 직무에서 요구하는 성장 가능성과 학습 의지를 표현

---

*본 직무기술서는 AI가 생성한 것으로, 실제 채용공고와 다를 수 있습니다. 자소서 작성 시 참고용으로 활용하세요.*
"""
        
        return result, jd_content, response
        
    except Exception as e:
        error_msg = f"""## ❌ 오류 발생

직무기술서 생성 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주세요.
"""
        return error_msg, "", None 