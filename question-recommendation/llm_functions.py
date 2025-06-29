import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_question_recommendation(client, prompts, job_title, company_name, experience_level):
    """
    면접 질문 추천을 생성하는 함수
    
    Args:
        client: OpenAI 클라이언트
        prompts: 프롬프트 딕셔너리
        job_title: 직무명
        company_name: 회사명
        experience_level: 경력 수준
    
    Returns:
        str: LLM 응답 결과
    """
    try:
        # 사용자 프롬프트 포맷팅
        user_prompt = prompts['user_prompt'].format(
            job_title=job_title,
            company_name=company_name,
            experience_level=experience_level
        )
        
        logger.info(f"면접 질문 추천 요청 - 직무: {job_title}, 회사: {company_name}, 경력: {experience_level}")
        
        # OpenAI Responses API 호출 (웹 검색 활성화)
        response = client.responses.create(
            model="gpt-4o-mini",
            tools=[{
                "type": "web_search_preview",
                "search_context_size": "high",
            }],
            input=f"{prompts['system_prompt']}\n\n{user_prompt}"
        )
        
        print(response)
        result = response.output_text
        logger.info("면접 질문 추천 생성 완료")
        
        return result, response
        
    except Exception as e:
        logger.error(f"면접 질문 추천 생성 중 오류 발생: {str(e)}")
        # raise e 대신 오류 정보와 None을 반환하도록 수정
        return f"오류 발생: {str(e)}", None

def parse_question_recommendation(response_text):
    """
    LLM 응답에서 면접 질문 추천 결과를 파싱하는 함수
    
    Args:
        response_text: LLM 응답 텍스트
    
    Returns:
        dict: 파싱된 면접 질문 추천 결과
    """
    try:
        # JSON 형태로 파싱 시도
        if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
            parsed_result = json.loads(response_text)
            logger.info("JSON 형태로 파싱 성공")
            return parsed_result
        
        # JSON 블록 추출 시도
        if '```json' in response_text:
            start_idx = response_text.find('```json') + 7
            end_idx = response_text.find('```', start_idx)
            json_content = response_text[start_idx:end_idx].strip()
            parsed_result = json.loads(json_content)
            logger.info("JSON 블록에서 파싱 성공")
            return parsed_result
        
    except Exception as e:
        logger.error(f"면접 질문 파싱 중 오류 발생: {str(e)}")
        return {"recommended_question": "질문 파싱에 실패했습니다."} 