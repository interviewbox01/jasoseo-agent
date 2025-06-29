from openai import OpenAI
import yaml
import os
import json

# 클라이언트 및 프롬프트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, 'prompt.yaml')
    with open(prompt_path, "r", encoding='utf-8') as file:
        prompts = yaml.safe_load(file)
except Exception as e:
    print(f"Warning: prompt.yaml 로드 실패. 기본 프롬프트를 사용합니다. 오류: {e}")
    prompts = {
        "Interviewer": "You are a job interviewer.",
        "Student": "You are a job applicant.",
        "CoverLetter": "Write a cover letter based on the conversation."
    }

def get_interviewer_response(example_info):
    """
    진행률(progress)을 포함한 면접관의 응답을 스트리밍으로 생성합니다.
    """
    # 프롬프트 포매팅에 필요한 모든 변수를 kwargs로 묶기
    format_kwargs = {
        **example_info
    }
    system_prompt = prompts.get("Interviewer", "").format(**format_kwargs)
    
    with open("system_prompt.txt", "w", encoding='utf-8') as f:
        f.write(system_prompt)
    conversation = [{"role": "system", "content": "You must generate the response in json format."}, {"role": "user", "content": system_prompt}]
    # for role, content in messages:
    #     conversation.append({"role": role, "content": content})
        
    response_stream = client.chat.completions.create(
        model="gpt-4.1",
        messages=conversation,
        stream=True
    )
    for chunk in response_stream:
        yield chunk.choices[0].delta.content or ""

def get_student_response(example_info):
    """학생의 AI 답변을 스트리밍으로 생성합니다."""
    system_prompt = prompts.get("Student", "").format(**example_info)
    
    conversation = [{"role": "system", "content": "You must generate the response in json format."}]
    
    with open("student_input.txt", "w", encoding='utf-8') as f:
        f.write(system_prompt)
    # for speaker, content in history:
    #     conversation.append({"role": "user", "content": f"{speaker}: {content}"})
    
    conversation.append({"role": "user", "content": f"{system_prompt}"})

    response_stream = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation,
        stream=True
    )
    for chunk in response_stream:
        yield chunk.choices[0].delta.content or ""

def generate_cover_letter_response(question, conversation_history, example_info, flow, word_limit):
    """
    진행률을 포함하여 자기소개서 답변을 스트리밍으로 생성합니다.
    """
    conversation_text = "\n".join([f"{speaker}: {content}" for speaker, content in conversation_history])
    
    # 진행률 표시를 요청하는 프롬프트
    prompt = prompts.get("CoverLetter", "").format(
        conversation=conversation_text,
        question=question,
        flow=flow,
        word_limit=word_limit,
        **example_info
    )
    
    response_stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    for chunk in response_stream:
        yield chunk.choices[0].delta.content or "" 