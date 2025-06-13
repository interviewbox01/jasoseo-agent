import openai
import yaml
import re

# OpenAI client 초기화
client = openai.OpenAI()

# 프롬프트 템플릿 로드
with open('prompt.yaml', 'r', encoding='utf-8') as f:
    prompt_data = yaml.safe_load(f)
    prompt_template = prompt_data['prompt']

def parse_prediction(content):
    """
    AI 응답에서 기업 규모 카테고리를 파싱하는 함수
    """
    predicted_category = "분류 불가"
    
    # 첫 번째 방법: ```<기업규모>``` 형식에서 파싱
    category_match = re.search(r'```<([^>]+)>```', content)
    if category_match:
        predicted_category = category_match.group(1)
    else:
        # 백업: 기존 방식으로 카테고리 찾기
        categories = ["대기업", "중견기업", "중소기업", "스타트업", "외국계기업", "공공기관 및 공기업", "비영리단체 및 협회재단", "금융업"]
        for category in categories:
            if category in content:
                predicted_category = category
                break
    
    return predicted_category

def analyze_company_size(company_name):
    """
    OpenAI Search API를 사용하여 기업 규모를 예측하는 함수
    """
    try:
        # OpenAI Search API를 사용한 회사 정보 검색
        search_response = client.responses.create(
            model="gpt-4o",
            tools=[
                {
                    "type": "web_search_preview",
                    "search_context_size": "low",
                }
            ],
            input= prompt_template.format(company_name=company_name)
        )
        
        # 응답에서 실제 메시지 찾기 (웹 검색 호출과 분리)
        print(search_response)
        message_output = None
        for output in search_response.output:
            if hasattr(output, 'content') and output.type == 'message':
                message_output = output
                break
        
        if message_output is None:
            raise Exception("응답에서 메시지 내용을 찾을 수 없습니다.")
        
        # 응답에서 내용과 URL 추출
        content = message_output.content[0].text
        
        # URL 인용 정보 추출
        citations = []
        if hasattr(message_output.content[0], 'annotations') and message_output.content[0].annotations:
            for annotation in message_output.content[0].annotations:
                if hasattr(annotation, 'url_citation'):
                    citations.append({
                        'title': annotation.url_citation.title,
                        'url': annotation.url_citation.url
                    })
        
        # 기업 규모 카테고리 추출
        predicted_category = parse_prediction(content)
        
        # 참조 URL 형식화
        reference_text = ""
        if citations:
            reference_text = "\n\n📚 **참고 자료:**\n"
            for i, citation in enumerate(citations, 1):
                reference_text += f"{i}. [{citation['title']}]({citation['url']})\n"
        
        # 최종 결과 형식화 (카테고리와 분석 내용 분리 반환)
        result_content = f"""## 🏢 {company_name} 기업 규모 분석 결과

{content}

{reference_text}

---
*본 분석은 OpenAI Search API를 통해 수집된 최신 웹 정보를 바탕으로 수행되었습니다.*
"""
        
        return result_content, predicted_category
        
    except Exception as e:
        error_msg = f"""## ❌ 오류 발생

죄송합니다. {company_name}의 기업 규모 분석 중 오류가 발생했습니다.

**오류 내용:** {str(e)}

다시 시도해주시거나 다른 기업명을 입력해주세요.
"""
        return error_msg, "오류 발생" 