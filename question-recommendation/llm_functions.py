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
        
        return result
        
    except Exception as e:
        logger.error(f"면접 질문 추천 생성 중 오류 발생: {str(e)}")
        raise e

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
        
        # 중괄호로 둘러싸인 JSON 추출 시도
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_content = response_text[start_idx:end_idx]
            parsed_result = json.loads(json_content)
            logger.info("중괄호 JSON에서 파싱 성공")
            return parsed_result
        
        # JSON 파싱 실패 시 텍스트에서 질문 추출
        logger.warning("JSON 파싱 실패, 텍스트에서 질문 추출 시도")
        
        # 따옴표로 둘러싸인 질문 찾기
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                # 따옴표 제거
                question = line.strip('"').strip("'").strip()
                if len(question) > 10:  # 최소 길이 체크
                    return {"recommended_question": question}
        
        # 전체 텍스트를 질문으로 사용 (최후의 수단)
        clean_text = response_text.strip().strip('"').strip("'")
        if len(clean_text) > 10:
            return {"recommended_question": clean_text}
        
        logger.error("면접 질문 추출 실패")
        return {"recommended_question": "질문 생성에 실패했습니다."}
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        # JSON 파싱 실패 시 텍스트에서 직접 추출
        clean_text = response_text.strip().strip('"').strip("'")
        return {"recommended_question": clean_text if clean_text else "질문 생성에 실패했습니다."}
    
    except Exception as e:
        logger.error(f"면접 질문 파싱 중 오류 발생: {str(e)}")
        return {"recommended_question": "질문 파싱에 실패했습니다."} 