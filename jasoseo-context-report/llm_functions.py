import os
import json
import re
import yaml
from openai import OpenAI
from dotenv import load_dotenv
from ..utils import track_api_cost

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



def parse_context_report(content):
    """
    AI 응답에서 컨텍스트 리포트 JSON을 파싱하는 함수
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
                json_str = re.sub(r',\s*]', ']', json_str)
                
                try:
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'company_profile' in parsed_json:
                        return parsed_json, content
                except json.JSONDecodeError as e:
                    print(f"JSON 블록 파싱 실패: {e}")
        
        
        # 4. 기본 구조 반환 (파싱 실패 시)
        print("JSON 파싱 실패, 기본 구조 반환")
        return {
            "company_profile": {
                "name": "파싱 실패",
                "vision_mission": "정보를 가져올 수 없습니다.",
                "core_values": ["정보 없음"],
                "talent_philosophy": "정보를 가져올 수 없습니다.",
                "recent_news_summary": "정보를 가져올 수 없습니다.",
                "main_products_services": ["정보 없음"]
            },
            "position_analysis": {
                "role_summary": "정보를 가져올 수 없습니다.",
                "required_skills": {
                    "hard": ["정보 없음"],
                    "soft": ["정보 없음"]
                },
                "keywords": ["정보 없음"]
            },
            "industry_context": {
                "trends": ["정보 없음"],
                "competitors": ["정보 없음"]
            }
        }, content
        
    except Exception as e:
        print(f"컨텍스트 리포트 파싱 전체 오류: {e}")
        print(f"파싱 실패한 컨텐츠: {repr(content)}")
        return {
            "company_profile": {
                "name": "오류 발생",
                "vision_mission": f"파싱 오류: {str(e)}",
                "core_values": ["오류"],
                "talent_philosophy": f"파싱 오류: {str(e)}",
                "recent_news_summary": f"파싱 오류: {str(e)}",
                "main_products_services": ["오류"]
            },
            "position_analysis": {
                "role_summary": f"파싱 오류: {str(e)}",
                "required_skills": {
                    "hard": ["오류"],
                    "soft": ["오류"]
                },
                "keywords": ["오류"]
            },
            "industry_context": {
                "trends": ["오류"],
                "competitors": ["오류"]
            }
        }, content

def generate_context_report(job_title, company_name, experience_level):
    """
    OpenAI API를 사용하여 자소서 컨텍스트 리포트를 생성하는 함수
    """
    try:
        if not job_title or not company_name or not experience_level:
            return "직무, 회사명, 경력 수준을 모두 입력해주세요.", {}
        
        # 프롬프트 생성
        prompt = prompt_template.format(
            job_title=job_title,
            company_name=company_name,
            experience_level=experience_level
        )
        
        # OpenAI Responses API 호출 (Web Search Preview 사용)
        response = client.responses.create(
            model="gpt-4o",
            tools=[{
                "type": "web_search_preview",
                "search_context_size": "high",
            }],
            input=f"당신은 자기소개서 작성을 위한 기업 및 직무 분석 전문가입니다. 웹 검색을 통해 최신 기업 정보와 산업 동향을 확인하고 정확한 JSON 형식으로 구조화된 정보를 제공해주세요.\n\n{prompt}"
        )
        
        content = response.output_text
        print(f"=== AI 응답 원본 ===")
        import pprint
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(content)
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
        
        report_data, raw_content = parse_context_report(content)
        
        if not report_data or 'company_profile' not in report_data:
            return "컨텍스트 리포트 생성에 실패했습니다. 다시 시도해주세요.", {}
        
        # 결과 포맷팅
        result = f"""## 📊 {company_name} - {job_title} 컨텍스트 리포트

### 🏢 **기업 프로필**

**🎯 비전 & 미션**
{report_data['company_profile']['vision_mission']}

**💎 핵심 가치**
"""
        for i, value in enumerate(report_data['company_profile']['core_values'], 1):
            result += f"**{i}.** {value}\n"
        
        result += f"""
**👥 인재상**
{report_data['company_profile']['talent_philosophy']}

**📰 최근 동향**
{report_data['company_profile']['recent_news_summary']}

**🛍️ 주요 제품/서비스**
"""
        for i, service in enumerate(report_data['company_profile']['main_products_services'], 1):
            result += f"**{i}.** {service}\n"
        
        result += f"""

### 💼 **직무 분석**

**📋 역할 요약**
{report_data['position_analysis']['role_summary']}

**🔧 필요 스킬**

*하드 스킬:*
"""
        for skill in report_data['position_analysis']['required_skills']['hard']:
            result += f"• {skill}\n"
        
        result += "\n*소프트 스킬:*\n"
        for skill in report_data['position_analysis']['required_skills']['soft']:
            result += f"• {skill}\n"
        
        result += f"""
**🏷️ 핵심 키워드**
"""
        for keyword in report_data['position_analysis']['keywords']:
            result += f"`{keyword}` "
        
        result += f"""

### 🌐 **산업 맥락**

**📈 주요 트렌드**
"""
        for i, trend in enumerate(report_data['industry_context']['trends'], 1):
            result += f"**{i}.** {trend}\n"
        
        result += f"""
**🏆 주요 경쟁사**
"""
        for i, competitor in enumerate(report_data['industry_context']['competitors'], 1):
            result += f"**{i}.** {competitor}\n"
        
        result += f"""

---
**📝 입력 정보:**
- 회사: {company_name}
- 직무: {job_title}
- 경력: {experience_level}

*본 리포트는 AI가 생성한 것으로, 실제 정보와 다를 수 있습니다. 자소서 작성 시 참고용으로 활용하세요.*
"""
        
        return result, report_data, raw_content
        
    except Exception as e:
        error_msg = f"""## ❌ 오류 발생

컨텍스트 리포트 생성 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주세요.
"""
        return error_msg, {}, raw_content    
        
        
if __name__ == "__main__":
    job_title = "백엔드 개발"
    company_name = "아이티뱅크"
    experience_level = "신입"
    result, report_data, raw_content = generate_context_report(job_title, company_name, experience_level)
    print(result)
    print(report_data)
    print(raw_content)