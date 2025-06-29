import os
import sys

# Force the project root onto the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
import gradio as gr
import yaml
import json
import re
from chat.llm_functions import get_interviewer_response, get_student_response, generate_cover_letter_response
from utils import parse_json_from_response
from guide_generation.llm_functions import generate_guide as create_guide_from_llm
from answer_flow_generation.llm_functions import generate_answer_flow


# Load environment variables and initial data
load_dotenv()

# with open("prompt.yaml", "r", encoding='utf-8') as f:
#     prompts = yaml.safe_load(f)

with open("example_info.json", "r", encoding='utf-8') as f:
    # This now serves as the default values for the UI
    default_info = json.load(f)
    # word_limit 기본값 추가
    if 'word_limit' not in default_info:
        default_info['word_limit'] = 300

def user_submit(message, history):
    """사용자 입력을 처리하고, 챗봇 기록을 업데이트합니다."""
    if not message.strip():
        return "", history
    history.append([message, None])
    return "", history

def clean_markdown_response(text):
    """
    LLM 응답에서 markdown 코드 블록을 제거하고 실제 내용만 추출합니다.
    
    Args:
        text (str): LLM 응답 텍스트
        
    Returns:
        str: 정리된 텍스트
    """
    if not text:
        return text
    
    # ```markdown ... ``` 또는 ``` ... ``` 패턴 제거
    import re
    
    # markdown 코드 블록 패턴 찾기
    markdown_match = re.search(r"```(?:markdown)?\s*([\s\S]*?)\s*```", text)
    if markdown_match:
        return markdown_match.group(1).strip()
    
    # 일반적인 코드 블록 패턴 찾기
    code_match = re.search(r"```\s*([\s\S]*?)\s*```", text)
    if code_match:
        return code_match.group(1).strip()
    
    # 코드 블록이 없으면 원본 반환
    return text.strip()

def bot_response(history, shared_info, progress=gr.Progress()):
    """면접관의 응답을 생성하고 진행률을 업데이트합니다."""
    if not history or history[-1][1] is not None:
        return history, gr.update(), gr.update()
    
    conversation_str = ""
    for h in history:
        conversation_str += f"학생: {h[0]}\n"
        if h[1]:
            conversation_str += f"AI: {h[1]}\n"
    
    format_info = shared_info.copy()
    format_info['conversation'] = conversation_str
    # word_limit 기본값 설정 (혹시 없을 경우를 대비)
    if 'word_limit' not in format_info:
        format_info['word_limit'] = 300

    history[-1][1] = ""
    full_response = ""
    for chunk in get_interviewer_response(format_info):
        full_response += chunk
        history[-1][1] = full_response
        yield history, gr.update(), gr.update()

    final_data = parse_json_from_response(full_response)
    final_progress_update = gr.update()
    final_reason_update = gr.update()
    if final_data:
        history[-1][1] = final_data.get("answer", "응답을 처리하는 데 실패했습니다.")
        final_progress = final_data.get("progress", 0)
        reasoning = final_data.get("reasoning_for_progress", "")
        
        if isinstance(final_progress, int) and 0 <= final_progress <= 100:
            progress(final_progress / 100)
            final_progress_update = f"자기소개서 완성도: {final_progress}%"
            if reasoning:
                final_reason_update = gr.update(value=f"**진행 상황 분석:** {reasoning}", visible=True)
            else:
                final_reason_update = gr.update(visible=False)

        if final_progress >= 100:
             history.append([None, "면접이 종료되었습니다. 자기소개서 생성 탭으로 이동하세요."])
    
    yield history, final_progress_update, final_reason_update


def generate_ai_reply(history, shared_info, progress=gr.Progress()):
    """학생의 AI 답변을 생성하고, 그에 대한 면접관의 후속 질문을 받습니다."""
    if not history or not history[-1][1]:
        return history, gr.update(), gr.update()
    
    conversation_str = ""
    for h in history:
        conversation_str += f"학생: {h[0]}\n"
        if h[1]:
            conversation_str += f"AI: {h[1]}\n"

    format_info = shared_info.copy()
    format_info['conversation'] = conversation_str
    # word_limit 기본값 설정 (혹시 없을 경우를 대비)
    if 'word_limit' not in format_info:
        format_info['word_limit'] = 300

    student_answer_json = ""
    history.append(["", None])
    for chunk in get_student_response(format_info):
        student_answer_json += chunk
        parsed_data = parse_json_from_response(student_answer_json)
        if parsed_data:
            history[-1][0] = parsed_data.get("answer", "")
        else:
            history[-1][0] = student_answer_json
        yield history, gr.update(), gr.update()

    final_data = parse_json_from_response(student_answer_json)
    if final_data:
        history[-1][0] = final_data.get("answer", "응답을 처리하는 데 실패했습니다.")
    yield history, gr.update(), gr.update()

    yield from bot_response(history, shared_info, progress=progress)

def generate_all_cover_letters(history, shared_info, progress=gr.Progress()):
    """모든 자기소개서 문항에 대한 답변을 생성하고 진행률을 표시합니다."""
    if not history:
        empty_outputs = [gr.update(value="면접 대화가 없습니다.")] * len(shared_info.get('questions', []))
        empty_guidelines = [gr.update(value="")] * len(shared_info.get('questions', []))
        return empty_outputs + empty_guidelines + [gr.update()]

    # history -> conversation_history 형식 변환
    conversation_str = ""
    for h in history:
        if h[0]: conversation_str += f"학생: {h[0]}\n"
        if h[1]: conversation_str += f"AI: {h[1]}\n"

    total_questions = len(shared_info.get('questions', []))
    outputs = [""] * total_questions
    guidelines = [""] * total_questions
    
    format_info = shared_info.copy()
    format_info['conversation'] = conversation_str
    
    for i, question in enumerate(shared_info.get('questions', [])):
        # 1단계: Answer Flow Generation
        progress_text = f"자기소개서 생성 진행률: {int((i / total_questions) * 50)}% (답변 흐름 생성 중...)"
        yield [gr.update(value=o) for o in outputs] + [gr.update(value=g) for g in guidelines] + [gr.update(value=progress_text, visible=True)]
        
        flow_result, _ = generate_answer_flow(
            question=question,
            jd=format_info.get('jd', ''),
            company_name=format_info.get('company_name', ''),
            experience_level=format_info.get('experience_level', '신입'),
            conversation=conversation_str
        )
        
        flow_text = flow_result.get('flow', '') if flow_result else ''
        guidelines[i] = flow_text  # 가이드라인 저장
        
        # 2단계: Cover Letter Response Generation
        progress_text = f"자기소개서 생성 진행률: {int((i / total_questions) * 50 + 25)}% (답변 생성 중...)"
        yield [gr.update(value=o) for o in outputs] + [gr.update(value=g) for g in guidelines] + [gr.update(value=progress_text, visible=True)]
        
        full_response = ""
        word_limit = shared_info.get('word_limit', 300)  # shared_info에서 word_limit 가져오기
        for chunk in generate_cover_letter_response(question, [], format_info, flow_text, word_limit):
            full_response += chunk
            parsed_data = parse_json_from_response(full_response)
            if parsed_data and 'answer' in parsed_data:
                # JSON에서 답변을 추출한 후 마크다운 코드 블록 정리
                cleaned_answer = clean_markdown_response(parsed_data['answer'])
                outputs[i] = cleaned_answer
            else:
                # JSON 파싱 실패 시 전체 응답에서 마크다운 코드 블록 정리
                cleaned_response = clean_markdown_response(full_response)
                outputs[i] = cleaned_response
            
            overall_progress_val = (i + 0.75) / total_questions
            progress_text = f"자기소개서 생성 진행률: {int(overall_progress_val*100)}%"
            yield [gr.update(value=o) for o in outputs] + [gr.update(value=g) for g in guidelines] + [gr.update(value=progress_text, visible=True)]

        # 최종 파싱 및 정리
        final_data = parse_json_from_response(full_response)
        if final_data and 'answer' in final_data:
            # JSON에서 답변을 추출한 후 마크다운 코드 블록 정리
            cleaned_answer = clean_markdown_response(final_data['answer'])
            outputs[i] = cleaned_answer
        else:
            # JSON 파싱 실패 시 전체 응답에서 마크다운 코드 블록 정리
            cleaned_response = clean_markdown_response(full_response)
            outputs[i] = cleaned_response

    # 완료
    yield [gr.update(value=o) for o in outputs] + [gr.update(value=g) for g in guidelines] + [gr.update(visible=False)]

def update_guide_and_info(company, position, jd, questions_str, word_limit):
    guide_json, _ = create_guide_from_llm(questions_str, jd, company, "신입") # experience_level is hardcoded for now
    
    if guide_json and "guide" in guide_json:
        guide_text = guide_json["guide"]
    else:
        guide_text = "가이드 생성에 실패했습니다. 입력값을 확인해주세요."

    new_info = default_info.copy()
    new_info.update({
        "company_name": company,
        "position_title": position,
        "jd": jd,
        "questions": [q.strip() for q in questions_str.strip().split('\n') if q.strip()],
        "guide": guide_text,
        "word_limit": word_limit
    })
    
    # Return new state and update for the guide display
    return new_info, guide_text

# --- Gradio UI ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    shared_info = gr.State(default_info)

    with gr.Tabs() as tabs:
        with gr.TabItem("가이드 생성", id=0):
            gr.Markdown("## 📝 자기소개서 정보 입력")
            gr.Markdown("면접 시뮬레이션에 필요한 정보를 입력하고 '가이드 생성' 버튼을 눌러주세요.")
            with gr.Row():
                company_name_input = gr.Textbox(label="회사명", value=default_info.get("company_name"))
                position_title_input = gr.Textbox(label="직무명", value=default_info.get("position_title"))
            jd_input = gr.Textbox(label="Job Description (JD)", lines=5, value=default_info.get("jd"))
            questions_input = gr.Textbox(label="자기소개서 질문 (한 줄에 한 개씩)", lines=3, value="\n".join(default_info.get("questions", [])))
            
            with gr.Row():
                word_limit_input = gr.Number(
                    label="자기소개서 글자수 제한", 
                    value=300, 
                    minimum=100, 
                    maximum=1000,
                    step=50,
                    info="자기소개서 각 문항별 글자수 제한을 설정하세요."
                )
            
            generate_guide_btn = gr.Button("가이드 생성", variant="primary")
            guide_output = gr.Markdown(label="생성된 가이드", value=f"**가이드:**\n{default_info.get('guide')}")
        
        with gr.TabItem("면접 대화", id=1):
            gr.Markdown("## 💬 면접 시뮬레이션")
            gr.Markdown("면접관의 질문에 답변하거나, 'AI 답변 생성' 버튼을 눌러보세요. 면접관이 판단하는 자기소개서 완성도가 100%가 되면 면접이 종료됩니다.")
            
            with gr.Row():
                progress_display = gr.Markdown("자기소개서 완성도: 0%")
            reason_display = gr.Markdown("", visible=False)
            chatbot = gr.Chatbot(label="면접 대화", bubble_full_width=False, avatar_images=("👤", "👔"), height=500)
            msg = gr.Textbox(label="메시지 입력", placeholder="메시지를 입력하세요...", lines=2)
            with gr.Row():
                submit_btn = gr.Button("전송", variant="primary")
                ai_reply_btn = gr.Button("AI 답변 생성", variant="secondary")
                clear_btn = gr.Button("초기화")

        with gr.TabItem("자기소개서 생성", id=2):
            gr.Markdown("## 📝 자기소개서 답변 생성")
            gr.Markdown("면접이 완료되면 대화 내용을 바탕으로 자기소개서 답변을 생성합니다.")
            
            generate_btn = gr.Button("자기소개서 생성 시작", variant="primary", size="lg")
            cover_letter_progress_display = gr.Markdown("", visible=False)

            cover_letter_outputs = []
            guideline_outputs = []
            for i, question in enumerate(default_info.get('questions', [])):
                with gr.Accordion(f"문항 {i+1}: {question[:50]}...", open=True):
                    gr.Markdown(f"**{question}**")
                    
                    with gr.Tabs():
                        with gr.TabItem("생성된 답변"):
                            output = gr.Textbox(
                                label=f"답변 {i+1}", 
                                lines=8, 
                                max_lines=20,
                                interactive=False,
                                show_copy_button=True,
                                placeholder="자기소개서 답변이 생성되면 여기에 표시됩니다...",
                                info="긴 답변의 경우 스크롤하여 전체 내용을 확인할 수 있습니다."
                            )
                            cover_letter_outputs.append(output)
                        
                        with gr.TabItem("답변 가이드라인"):
                            guideline = gr.Markdown(value="가이드라인이 생성되면 여기에 표시됩니다.")
                            guideline_outputs.append(guideline)

    # Event Handlers
    generate_guide_btn.click(
        fn=update_guide_and_info,
        inputs=[company_name_input, position_title_input, jd_input, questions_input, word_limit_input],
        outputs=[shared_info, guide_output]
    )
    
    submit_btn.click(user_submit, [msg, chatbot], [msg, chatbot]).then(bot_response, [chatbot, shared_info], [chatbot, progress_display, reason_display])
    msg.submit(user_submit, [msg, chatbot], [msg, chatbot]).then(bot_response, [chatbot, shared_info], [chatbot, progress_display, reason_display])
    ai_reply_btn.click(generate_ai_reply, [chatbot, shared_info], [chatbot, progress_display, reason_display])
    clear_btn.click(lambda: ([], "자기소개서 완성도: 0%", ""), None, [chatbot, progress_display, reason_display], queue=False)
    generate_btn.click(generate_all_cover_letters, [chatbot, shared_info], cover_letter_outputs + guideline_outputs + [cover_letter_progress_display])

if __name__ == "__main__":
    demo.launch(share=True)