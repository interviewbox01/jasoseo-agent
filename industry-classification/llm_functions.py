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

def parse_industry_tags(content):
    """
    AI 응답에서 산업 태그 배열을 파싱하는 함수
    """
    try:
        print(f"파싱할 컨텐츠 길이: {len(content)}")
        print(f"파싱할 컨텐츠 첫 200자: {repr(content[:200])}")
        
        # 텍스트 전처리
        cleaned_content = content.strip()
        
        # 1. JSON 코드 블록 찾기 (```json ... ``` 형식)
        json_patterns = [
            r'```json\s*(\[.*?\])\s*```',
            r'```\s*(\[.*?\])\s*```',
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
                json_str = re.sub(r',\s*]', ']', json_str)
                
                try:
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, list):
                        return parsed_json
                except json.JSONDecodeError as e:
                    print(f"JSON 블록 파싱 실패: {e}")
        
        # 2. 대괄호로 둘러싸인 배열 찾기
        array_patterns = [
            r'\[(.*?)\]'
        ]
        
        for pattern in array_patterns:
            array_match = re.search(pattern, cleaned_content, re.DOTALL)
            if array_match:
                array_content = array_match.group(1).strip()
                print(f"배열 내용 발견: {repr(array_content[:100])}")
                
                # 배열 내용에서 문자열 추출
                tags = []
                # 따옴표로 둘러싸인 문자열들 찾기
                tag_matches = re.findall(r'"([^"]+)"', array_content)
                for tag in tag_matches:
                    if tag.strip():
                        tags.append(tag.strip())
                
                if tags:
                    return tags
        
        # 3. 전체 텍스트를 JSON으로 파싱 시도
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
            if isinstance(parsed_json, list):
                return parsed_json
        except json.JSONDecodeError as e:
            print(f"전체 JSON 파싱 실패: {e}")
        
        # 4. 최후의 수단: 패턴 매칭으로 태그 추출
        print("패턴 매칭으로 태그 추출 시도")
        tags = []
        
        # 다양한 패턴으로 태그 찾기
        patterns = [
            r'"([a-z-]+)"',  # 따옴표 안의 태그 형태
            r'([a-z-]+)',    # 단순 태그 형태
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, cleaned_content)
            for match in matches:
                tag = match.strip()
                if len(tag) > 2 and '-' in tag and tag not in tags:
                    tags.append(tag)
                    if len(tags) >= 5:  # 최대 5개
                        break
            if tags:
                break
        
        return tags[:5] if tags else []
        
    except Exception as e:
        print(f"태그 파싱 전체 오류: {e}")
        print(f"파싱 실패한 컨텐츠: {repr(content)}")
        return []

def classify_industry(job_title, company_name):
    """
    OpenAI API를 사용하여 기업의 산업을 분류하는 함수
    """
    try:
        if not job_title or not company_name:
            return "직무와 회사명을 모두 입력해주세요.", []
        
        # 프롬프트 생성
        prompt = prompt_template.format(
            job_title=job_title,
            company_name=company_name
        )
        
        # OpenAI Responses API 호출 (Web Search Preview 사용)
        response = client.responses.create(
            model="gpt-4o",
            tools=[{
                "type": "web_search_preview",
                "search_context_size": "high",
            }],
            input=f"당신은 기업 산업 분류 전문가입니다. 웹 검색을 통해 최신 정보를 확인하고 정확한 산업 태그를 JSON 배열 형식으로 반환해주세요.\n\n{prompt}"
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
        
        tags = parse_industry_tags(content)
        
        if not tags:
            return "산업 분류에 실패했습니다. 다시 시도해주세요.", []
        
        # 태그명 매핑 (표시용)
        tag_mapping = {
            "platform-portal": "플랫폼/포털",
            "e-commerce": "이커머스",
            "game": "게임",
            "it-solution-si": "IT솔루션/SI",
            "o2o-vertical": "O2O/버티컬",
            "ai-data": "AI/데이터",
            "cloud-saas": "클라우드/SaaS",
            "fintech": "핀테크",
            "semiconductor": "반도체",
            "electronics-home": "가전/전자제품",
            "automotive-mobility": "자동차/모빌리티",
            "battery": "2차전지",
            "display": "디스플레이",
            "heavy-industry-shipbuilding": "중공업/조선",
            "steel-metal": "철강/금속",
            "bank": "은행",
            "securities": "증권",
            "insurance": "보험",
            "card": "카드",
            "asset-management": "자산운용",
            "dept-store-mart": "백화점/마트",
            "convenience-store": "편의점",
            "fmcg-beverage": "FMCG/식음료",
            "fashion-beauty": "패션/뷰티",
            "duty-free": "면세점",
            "pharma-new-drug": "제약/신약개발",
            "bio-cmo": "바이오/CMO",
            "medical-device": "의료기기",
            "digital-healthcare": "디지털헬스케어",
            "entertainment": "엔터테인먼트",
            "contents-video": "콘텐츠/영상제작",
            "ad-agency": "광고대행사",
            "webtoon-webnovel": "웹툰/웹소설",
            "broadcasting-press": "방송/언론",
            "construction-engineering": "건설/엔지니어링",
            "realestate-development": "부동산개발",
            "plant": "플랜트",
            "interior": "인테리어",
            "public-soc": "SOC (공항,도로,철도)",
            "public-energy": "에너지 공기업",
            "public-finance": "금융 공기업",
            "public-admin": "일반행정",
            "mpe-semiconductor": "반도체 소부장",
            "mpe-display": "디스플레이 소부장",
            "mpe-battery": "2차전지 소부장",
            "auto-parts": "자동차 부품",
            "chemical-materials": "화학/소재",
            "hotel": "호텔",
            "travel-agency": "여행사",
            "airline": "항공사",
            "leisure-resort": "레저/리조트",
            "consulting": "컨설팅",
            "accounting-tax": "회계/세무",
            "law-firm": "법률 (로펌)",
            "market-research": "리서치",
            "logistics-delivery": "물류/택배",
            "shipping": "해운",
            "forwarding": "포워딩",
            "land-transport": "육상운송",
            "edutech": "에듀테크",
            "private-academy": "입시/보습학원",
            "edu-publishing": "교육출판",
            "language-edu": "외국어교육",
            "ngo-npo": "NGO/NPO",
            "social-enterprise": "사회적기업",
            "foundation": "재단"
        }
        
        # 결과 포맷팅
        result = f"""## 🏢 {company_name} - {job_title} 산업 분류 결과

### 🏷️ **분류된 산업 태그**

"""
        for i, tag in enumerate(tags, 1):
            tag_name = tag_mapping.get(tag, tag)
            result += f"**{i}.** #{tag_name} (`{tag}`)\n\n"
        
        result += f"""
---
**📝 입력 정보:**
- 회사: {company_name}
- 직무: {job_title}
- 분류된 태그 수: {len(tags)}개

*본 분류는 AI가 수행한 것으로, 실제와 다를 수 있습니다.*
"""
        
        return result, tags
        
    except Exception as e:
        error_msg = f"""## ❌ 오류 발생

산업 분류 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주세요.
"""
        return error_msg, [] 