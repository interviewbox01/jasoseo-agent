import os
from dotenv import load_dotenv
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from typing import Iterator
import yaml
import json

# Load environment variables
load_dotenv()

# Initialize the ChatOpenAI model with streaming enabled
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.2,
    streaming=True
)

student_llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    streaming=True
)

cover_letter_llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.3,
    streaming=True
)

with open("prompt.yaml", "r", encoding='utf-8') as f:
    data = yaml.safe_load(f)
    interviewer_prompt = data["Interviewer"]
    student_prompt = data["Student"]

with open("example_info.json", "r", encoding='utf-8') as f:
    example_info = json.load(f)

def get_student_response(interviewer_message, history):
    # Prepare context for student LLM
    messages = [
        HumanMessage(content=student_prompt.format(**example_info)),
        HumanMessage(content="이전 대화 기록:")
    ]
    
    # Add conversation history
    for human, ai in history:
        messages.extend([
            HumanMessage(content=f"학생: {human}"),
            HumanMessage(content=f"면접관: {ai}")
        ])
    
    # Add current interviewer message
    messages.append(HumanMessage(content=f"면접관: {interviewer_message}"))
    messages.append(HumanMessage(content="위 대화 기록을 바탕으로, 면접관의 마지막 질문에 답변해주세요."))
    
    # Get streaming response
    response_stream = student_llm.stream(messages)
    
    # Stream the response
    partial_message = ""
    for chunk in response_stream:
        if chunk.content:
            partial_message += chunk.content
            yield partial_message

def respond(message, history):
    # Convert history to LangChain message format
    messages = [HumanMessage(content=interviewer_prompt.format(**example_info))]
    for human, ai in history:
        messages.extend([
            HumanMessage(content=human),
            AIMessage(content=ai)
        ])
    
    # Add the current message
    messages.append(HumanMessage(content=message))
    
    # Get streaming response from LangChain
    response_stream = llm.stream(messages)
    
    # Stream the response
    partial_message = ""
    for chunk in response_stream:
        if chunk.content:
            partial_message += chunk.content
            yield partial_message

def generate_cover_letter_response(question, conversation_history):
    """Generate a cover letter response for a specific question based on conversation history"""
    
    # Prepare conversation context
    conversation_text = ""
    for human, ai in conversation_history:
        conversation_text += f"학생: {human}\n면접관: {ai}\n\n"
    
    prompt = f"""
다음은 {example_info['company_name']} {example_info['position_title']} 직무 면접 대화 내용입니다:

{conversation_text}

위 면접 대화 내용을 바탕으로, 다음 자기소개서 문항에 대한 답변을 작성해주세요:

**문항: {question}**

**작성 지침:**
- 면접에서 언급된 구체적인 경험과 사례를 활용하세요
- 300-500자 정도의 적절한 길이로 작성하세요
- STAR 방식(상황-과제-행동-결과)을 활용하여 구조화하세요
- {example_info['company_name']}의 인재상({example_info['core_values']})과 연계하여 작성하세요
- 전문적이고 진정성 있는 문체로 작성하세요

자기소개서 답변:
"""
    
    messages = [HumanMessage(content=prompt)]
    response_stream = cover_letter_llm.stream(messages)
    
    partial_message = ""
    for chunk in response_stream:
        if chunk.content:
            partial_message += chunk.content
            yield partial_message

def check_interview_end(history):
    """Check if the interview has ended"""
    if not history:
        return False
    
    # Check the last AI response for END_OF_INTERVIEW
    last_ai_response = history[-1][1] if history[-1][1] else ""
    return "[END_OF_INTERVIEW]" in last_ai_response

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    with gr.Tabs() as tabs:
        with gr.TabItem("면접 대화", id=0) as chat_tab:
            chatbot = gr.Chatbot(
                label="면접 대화",
                bubble_full_width=False,
                avatar_images=("👤", "👔"),
                height=500
            )
            msg = gr.Textbox(
                label="메시지 입력",
                placeholder="메시지를 입력하거나 'AI 답변 생성' 버튼을 클릭하세요...",
                lines=2
            )
            
            with gr.Row():
                submit = gr.Button("전송", variant="primary")
                ai_reply = gr.Button("AI 답변 생성", variant="secondary")
                clear = gr.Button("대화 초기화")
            
            with gr.Accordion("예시 답변", open=False):
                examples = gr.Examples(
                    examples=["안녕하세요, 저는 면접 보러 왔습니다.", 
                             "제 성장 과정에 대해 말씀드리겠습니다.",
                             "이 직무를 위해 준비한 프로젝트 경험이 있습니다."],
                    inputs=msg
                )
        
        with gr.TabItem("자기소개서 생성", id=1) as cover_letter_tab:
            gr.Markdown("## 📝 자기소개서 답변 생성")
            gr.Markdown("면접이 완료되면 대화 내용을 바탕으로 자기소개서 답변을 생성합니다.")
            
            generate_btn = gr.Button("자기소개서 생성", variant="primary", size="lg")
            
            cover_letter_outputs = []
            for i, question in enumerate(example_info.get('questions', [])):
                with gr.Accordion(f"문항 {i+1}: {question[:50]}...", open=False):
                    gr.Markdown(f"**{question}**")
                    output = gr.Textbox(
                        label=f"답변 {i+1}",
                        lines=8,
                        placeholder="면접 완료 후 답변이 생성됩니다...",
                        interactive=False
                    )
                    cover_letter_outputs.append(output)

    def user_submit(message, history):
        if message.strip() == "":
            return "", history, gr.update()
        history = history + [[message, None]]
        return "", history, gr.update()

    def bot_response(history):
        if not history or history[-1][1] is not None:
            return history, gr.update()
        message = history[-1][0]
        history[-1][1] = ""
        for chunk in respond(message, history[:-1]):
            history[-1][1] = chunk
            yield history, gr.update()
        
        # Check if interview ended and switch to cover letter tab
        if check_interview_end(history):
            yield history, gr.update(selected=1)
        else:
            yield history, gr.update()

    def generate_ai_reply(history):
        if not history or not history[-1][1]:
            return history, gr.update()
        
        history.append(["", None])
        for chunk in get_student_response(history[-2][1], history[:-2]):
            history[-1][0] = chunk
            yield history, gr.update()
        
        # Now get interviewer's response to the generated reply
        history[-1][1] = ""
        for chunk in respond(history[-1][0], history[:-1]):
            history[-1][1] = chunk
            yield history, gr.update()
        
        # Check if interview ended and switch to cover letter tab
        if check_interview_end(history):
            yield history, gr.update(selected=1)
        else:
            yield history, gr.update()

    def generate_all_responses(history):
        """Generate responses for all cover letter questions"""
        if not history:
            return [gr.update(value="면접 대화가 없습니다.")] * len(example_info.get('questions', []))
        
        results = []
        for question in example_info.get('questions', []):
            response = ""
            for chunk in generate_cover_letter_response(question, history):
                response = chunk
            results.append(gr.update(value=response))
        
        return results

    msg.submit(user_submit, [msg, chatbot], [msg, chatbot, tabs]).then(
        bot_response, chatbot, [chatbot, tabs]
    )
    
    submit.click(user_submit, [msg, chatbot], [msg, chatbot, tabs]).then(
        bot_response, chatbot, [chatbot, tabs]
    )
    
    ai_reply.click(generate_ai_reply, chatbot, [chatbot, tabs])
    clear.click(lambda: ([], gr.update(selected=0)), None, [chatbot, tabs], queue=False)
    
    generate_btn.click(
        generate_all_responses, 
        chatbot, 
        cover_letter_outputs
    )

if __name__ == "__main__":
    demo.launch(share=True)