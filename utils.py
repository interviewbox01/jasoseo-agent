import re
import json

def parse_json_from_response(text: str) -> dict | None:
    """
    Markdown 코드 블록 안에 포함될 수 있는 JSON 문자열을 추출하고 파싱합니다.

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

def track_api_cost(response, model_name, search_context_size):
    # Calculate web search cost based on model and context size
    search_cost = 0
    
    if model_name in ['gpt-4.1', 'gpt-4o', 'gpt-4o-search-preview']:
        if search_context_size == 'low':
            search_cost = 0.03  # $30/1000 calls = $0.03 per call
        elif search_context_size == 'medium':
            search_cost = 0.035 # $35/1000 calls = $0.035 per call 
        elif search_context_size == 'high':
            search_cost = 0.05  # $50/1000 calls = $0.05 per call
            
    elif model_name in ['gpt-4.1-mini', 'gpt-4o-mini', 'gpt-4o-mini-search-preview']:
        if search_context_size == 'low':
            search_cost = 0.025 # $25/1000 calls = $0.025 per call
        elif search_context_size == 'medium':
            search_cost = 0.0275 # $27.50/1000 calls = $0.0275 per call
        elif search_context_size == 'high':
            search_cost = 0.03  # $30/1000 calls = $0.03 per call
            
    generation_cost = 0
    # Calculate generation cost based on model and token counts
    if model_name in ['gpt-4.1', 'gpt-4.1-2025-04-14']:
        generation_cost = (response.usage.prompt_tokens * 0.002 / 1000) + (response.usage.completion_tokens * 0.008 / 1000)
    elif model_name in ['gpt-4.1-mini', 'gpt-4.1-mini-2025-04-14']:
        generation_cost = (response.usage.prompt_tokens * 0.0004 / 1000) + (response.usage.completion_tokens * 0.0016 / 1000)
    elif model_name in ['gpt-4.1-nano', 'gpt-4.1-nano-2025-04-14']:
        generation_cost = (response.usage.prompt_tokens * 0.0001 / 1000) + (response.usage.completion_tokens * 0.0004 / 1000)
    elif model_name in ['gpt-4.5-preview', 'gpt-4.5-preview-2025-02-27']:
        generation_cost = (response.usage.prompt_tokens * 0.075 / 1000) + (response.usage.completion_tokens * 0.15 / 1000)
    elif model_name in ['gpt-4o', 'gpt-4o-2024-08-06']:
        generation_cost = (response.usage.prompt_tokens * 0.0025 / 1000) + (response.usage.completion_tokens * 0.01 / 1000)
    else:
        generation_cost = 0  # Default to 0 for unknown models
        
    total_cost = search_cost + generation_cost
    return total_cost
