import os
import sys
import json
import asyncio
import aiofiles
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import uuid
from pathlib import Path
import random
import time

# 프로젝트 루트를 path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
from chat.llm_functions import get_interviewer_response, get_student_response, generate_cover_letter_response
from utils import parse_json_from_response
from guide_generation.llm_functions import generate_guide as create_guide_from_llm
from answer_flow_generation.llm_functions import generate_answer_flow

load_dotenv()

class TestCase:
    def __init__(self, case_id, company_name, position_title, jd, questions, word_limit=300):
        self.case_id = case_id
        self.company_name = company_name
        self.position_title = position_title
        self.jd = jd
        self.questions = questions
        self.word_limit = word_limit
        self.results = {
            'guide_generation': None,
            'chat_history': [],
            'answer_flows': [],
            'final_answers': [],
            'errors': [],
            'start_time': None,
            'end_time': None,
            'total_duration': None
        }

# 다양한 테스트 케이스 정의
TEST_CASES = [
    {
        "company_name": "삼성전자",
        "position_title": "반도체 설계 엔지니어",
        "jd": "반도체 회로 설계, SoC 개발, 저전력 회로 최적화 업무를 담당합니다.",
        "questions": [
            "지원 동기와 입사 후 포부를 기술하시오.",
        ]
    },
    {
        "company_name": "카카오",
        "position_title": "백엔드 개발자",
        "jd": "대규모 트래픽 처리, 마이크로서비스 설계 및 운영, RESTful API 개발을 담당합니다.",
        "questions": [
            "공동의 목표를 달성하기 위해 타인과 힘을 합쳐 노력했던 경험을 기술해주세요.",
        ]
    },
    {
        "company_name": "네이버",
        "position_title": "AI 엔지니어",
        "jd": "머신러닝 모델 개발, 데이터 분석, AI 서비스 구축을 담당합니다.",
        "questions": [
            "기존 방식에서 벗어나 더 효율적인 프로세스를 도입했던 경험을 제시하시오.",
        ]
    },
    {
        "company_name": "현대자동차",
        "position_title": "자율주행 소프트웨어 엔지니어",
        "jd": "자율주행 알고리즘 개발, 센서 데이터 처리, 안전성 검증을 담당합니다.",
        "questions": [
            "목표 달성을 위해 끈기있게 노력한 경험을 기술하시오.",
        ]
    },
    {
        "company_name": "LG전자",
        "position_title": "IoT 플랫폼 개발자",
        "jd": "IoT 디바이스 연동, 클라우드 플랫폼 개발, 데이터 분석을 담당합니다.",
        "questions": [
            "창의적 문제해결 경험을 구체적으로 기술하시오.",
        ]
    }
]

def generate_company_context(company_name, position_title):
    """회사별 컨텍스트 정보를 생성합니다."""
    company_contexts = {
        "삼성전자": {
            "context_report": "삼성전자는 글로벌 반도체 시장 선도기업으로서 최근 차세대 반도체 기술 개발과 AI 반도체 분야에 집중 투자하고 있으며, 혁신적 기술력과 글로벌 마인드를 중시합니다.",
            "recent_issue": "차세대 반도체 기술 개발 및 AI 반도체 분야 집중 투자",
            "core_values": "혁신, 글로벌 마인드, 기술력"
        },
        "카카오": {
            "context_report": "카카오는 최근 클라우드 기반 마이크로서비스 아키텍처로의 전환을 진행 중이며, 혁신과 협업을 중시하는 기업 문화를 가지고 있습니다.",
            "recent_issue": "클라우드 기반 마이크로서비스 아키텍처로의 전환 진행 중",
            "core_values": "혁신성, 협업능력, 도전정신"
        },
        "네이버": {
            "context_report": "네이버는 AI 기술을 기반으로 한 플랫폼 혁신을 주도하고 있으며, 글로벌 AI 기술 경쟁력 확보와 사용자 중심의 서비스 개발에 집중하고 있습니다.",
            "recent_issue": "AI 기술 기반 플랫폼 혁신 및 글로벌 AI 경쟁력 확보",
            "core_values": "기술 혁신, 사용자 중심, 글로벌 경쟁력"
        },
        "현대자동차": {
            "context_report": "현대자동차는 미래 모빌리티 기업으로의 전환을 추진하며, 자율주행 기술과 전기차 플랫폼 개발에 대규모 투자를 진행하고 있습니다.",
            "recent_issue": "미래 모빌리티 기업으로의 전환 및 자율주행 기술 개발",
            "core_values": "도전정신, 품질 혁신, 미래 지향성"
        },
        "LG전자": {
            "context_report": "LG전자는 스마트 라이프케어 솔루션과 IoT 기반 생활가전 생태계 구축에 집중하며, 디지털 전환을 통한 미래 성장 동력 확보에 힘쓰고 있습니다.",
            "recent_issue": "스마트 라이프케어 솔루션 및 IoT 생태계 구축",
            "core_values": "고객 가치, 혁신 기술, 지속가능성"
        }
    }
    
    context = company_contexts.get(company_name, {
        "context_report": f"{company_name}는 최근 디지털 전환 및 혁신을 진행 중이며, 혁신과 협업을 중시하는 기업 문화를 가지고 있습니다.",
        "recent_issue": "디지털 전환 및 혁신 진행 중",
        "core_values": "혁신성, 협업능력, 도전정신"
    })
    
    return context

def generate_test_cases(num_cases=50):
    """50개의 테스트 케이스를 생성합니다."""
    base_cases = TEST_CASES.copy()
    test_cases = []
    
    for i in range(num_cases):
        # 기본 케이스 중 하나를 선택하고 변형
        base = base_cases[i % len(base_cases)].copy()
        
        # 케이스 ID 및 변형 요소 추가
        case_id = f"case_{i+1:03d}"
        word_limit = random.choice([200, 300, 400, 500])
        
        test_case = TestCase(
            case_id=case_id,
            company_name=base["company_name"],
            position_title=base["position_title"],
            jd=base["jd"],
            questions=base["questions"],
            word_limit=word_limit
        )
        test_cases.append(test_case)
    
    return test_cases

async def run_guide_generation(test_case):
    """1단계: 가이드 생성"""
    print(f"  📋 {test_case.case_id}: Starting guide generation...")
    
    try:
        questions_str = '\n'.join(test_case.questions)
        print(f"  📝 Questions: {len(test_case.questions)} items")
        print(f"  🏢 Company: {test_case.company_name}")
        print(f"  📄 JD length: {len(test_case.jd)} characters")
        
        guide_json, _ = create_guide_from_llm(
            questions_str, 
            test_case.jd, 
            test_case.company_name, 
            "신입"
        )
        
        if guide_json and "guide" in guide_json:
            guide_text = guide_json["guide"]
            print(f"  ✅ Guide generated successfully: {len(guide_text)} characters")
            test_case.results['guide_generation'] = {
                'success': True,
                'guide_text': guide_text,
                'timestamp': datetime.now().isoformat()
            }
            return guide_text
        else:
            print(f"  ❌ Guide generation failed: Invalid response format")
            print(f"  📄 Raw response: {str(guide_json)[:200]}...")
            test_case.results['guide_generation'] = {
                'success': False,
                'error': 'Guide generation failed - invalid response format',
                'timestamp': datetime.now().isoformat()
            }
            return "가이드 생성 실패"
    except Exception as e:
        print(f"  ❌ Guide generation error: {str(e)}")
        test_case.results['errors'].append(f"Guide generation error: {str(e)}")
        test_case.results['guide_generation'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return "가이드 생성 중 오류 발생"

async def run_chat_simulation(test_case, guide_text):
    """2단계: 채팅 시뮬레이션"""
    print(f"  📋 {test_case.case_id}: Starting chat simulation...")
    
    try:
        # 회사별 컨텍스트 정보 가져오기
        company_context = generate_company_context(test_case.company_name, test_case.position_title)
        
        # 공유 정보 설정 (example_info.json 형식에 맞춤)
        shared_info = {
            "company_name": test_case.company_name,
            "industry": "IT/소프트웨어",
            "position_title": test_case.position_title,
            "core_values": company_context["core_values"],
            "company_size": "대기업",
            "context_report": company_context["context_report"],
            "jd": test_case.jd,
            "recent_issue": company_context["recent_issue"],
            "student_name": "김철수",
            "student_major": "컴퓨터공학과",
            "student_status": "4학년",
            "experience_summary": "학부 시절 다양한 팀 프로젝트와 인턴 경험을 통해 협업과 문제 해결 능력을 키웠으며, 관련 분야 프로젝트를 다수 수행하였습니다.",
            "guide": guide_text,
            "questions": test_case.questions,
            "word_limit": test_case.word_limit,
            "conversation": ""
        }
        
        history = []
        max_turns = 20  # 최대 대화 턴
        
        print(f"  🔄 {test_case.case_id}: Starting {max_turns} conversation turns...")
        
        # 대화 턴 진행
        for turn in range(max_turns):
            print(f"    Turn {turn + 1}/{max_turns} processing...")
            
            try:
                # 면접관 응답 생성
                conversation_str = ""
                for h in history:
                    if h[1]: conversation_str += f"AI: {h[1]}\n"
                    if h[0]: conversation_str += f"학생: {h[0]}\n"
                
                format_info = shared_info.copy()
                format_info['conversation'] = conversation_str
                
                # 면접관 질문 생성
                print(f"      Getting interviewer response...")
                full_response = ""
                for chunk in get_interviewer_response(format_info):
                    full_response += chunk
                
                if not full_response.strip():
                    print(f"      ❌ Empty interviewer response at turn {turn + 1}")
                    test_case.results['errors'].append(f"Turn {turn+1}: Empty interviewer response")
                    break
                
                # JSON 파싱
                final_data = parse_json_from_response(full_response)
                if not final_data:
                    print(f"      ❌ Failed to parse interviewer JSON at turn {turn + 1}")
                    print(f"      Raw response: {full_response[:200]}...")
                    test_case.results['errors'].append(f"Turn {turn+1}: Failed to parse interviewer JSON")
                    # 실패해도 계속 진행하도록 기본값 설정
                    final_data = {
                        "answer": "면접관 질문 생성 실패",
                        "progress": min(20 * (turn + 1), 100),
                        "reasoning_for_progress": "JSON 파싱 실패로 인한 기본 진행률"
                    }
                
                interviewer_question = final_data.get("answer", "질문 생성 실패")
                progress = final_data.get("progress", min(20 * (turn + 1), 100))
                reasoning = final_data.get("reasoning_for_progress", "진행률 분석 실패")
                
                print(f"      ✅ Interviewer question generated, progress: {progress}%")
                
                # 대화 기록에 추가 (학생 답변은 None으로 시작)
                history.append([None, interviewer_question])
                
                conversation_str = ""
                for h in history:
                    if h[1]: conversation_str += f"AI: {h[1]}\n"
                    if h[0]: conversation_str += f"학생: {h[0]}\n"
                format_info['conversation'] = conversation_str
                
                # 학생 답변 생성 (100% 전에 생성)
                student_answer = ""
                print(f"      Getting student response...")
                try:
                    student_answer_json = ""
                    for chunk in get_student_response(format_info):
                        student_answer_json += chunk
                    
                    if student_answer_json.strip():
                        student_data = parse_json_from_response(student_answer_json)
                        if student_data:
                            student_answer = student_data.get("answer", "답변 생성 실패")
                        else:
                            student_answer = student_answer_json.strip()
                    else:
                        student_answer = "학생 답변 생성 실패"
                    
                    history[-1][0] = student_answer
                    print(f"      ✅ Student answer generated")
                    
                except Exception as student_error:
                    print(f"      ⚠️ Student response error: {str(student_error)}")
                    student_answer = f"학생 답변 생성 중 오류: {str(student_error)}"
                    history[-1][0] = student_answer
                
                # 채팅 기록에 저장 (학생 답변 포함)
                chat_record = {
                    'turn': turn + 1,
                    'interviewer_question': interviewer_question,
                    'student_answer': student_answer,
                    'progress': progress,
                    'reasoning': reasoning,
                    'timestamp': datetime.now().isoformat()
                }
                test_case.results['chat_history'].append(chat_record)
                
                # 100% 달성 시 종료 (학생 답변까지 완료 후)
                if progress >= 100:
                    print(f"      🎯 Progress reached {progress}%, ending chat simulation")
                    break
                
                # 잠시 대기 (API 제한 방지)
                await asyncio.sleep(0.5)
                
            except Exception as turn_error:
                print(f"      ❌ Turn {turn + 1} error: {str(turn_error)}")
                test_case.results['errors'].append(f"Turn {turn+1} error: {str(turn_error)}")
                break
        
        print(f"  ✅ {test_case.case_id}: Chat simulation completed with {len(test_case.results['chat_history'])} turns")
        return history
        
    except Exception as e:
        print(f"  ❌ {test_case.case_id}: Chat simulation failed: {str(e)}")
        test_case.results['errors'].append(f"Chat simulation error: {str(e)}")
        return []

async def run_answer_flow_generation(test_case, conversation_history):
    """3단계: 답변 흐름 생성"""
    try:
        conversation_str = ""
        for h in conversation_history:
            if h[0]: conversation_str += f"학생: {h[0]}\n"
            if h[1]: conversation_str += f"AI: {h[1]}\n"
        
        for i, question in enumerate(test_case.questions):
            flow_result, _ = generate_answer_flow(
                question=question,
                jd=test_case.jd,
                company_name=test_case.company_name,
                experience_level="신입",
                conversation=conversation_str
            )
            
            flow_text = flow_result.get('flow', '') if flow_result else ''
            test_case.results['answer_flows'].append({
                'question_index': i,
                'question': question,
                'flow_text': flow_text,
                'success': bool(flow_text),
                'timestamp': datetime.now().isoformat()
            })
            
            await asyncio.sleep(0.5)  # API 제한 방지
            
    except Exception as e:
        test_case.results['errors'].append(f"Answer flow generation error: {str(e)}")

async def run_answer_generation(test_case, conversation_history):
    """4단계: 최종 답변 생성"""
    try:
        conversation_str = ""
        for h in conversation_history:
            if h[0]: conversation_str += f"학생: {h[0]}\n"
            if h[1]: conversation_str += f"AI: {h[1]}\n"
        
        # 회사별 컨텍스트 정보 가져오기
        company_context = generate_company_context(test_case.company_name, test_case.position_title)
        
        format_info = {
            "company_name": test_case.company_name,
            "industry": "IT/소프트웨어",
            "position_title": test_case.position_title,
            "core_values": company_context["core_values"],
            "company_size": "대기업",
            "context_report": company_context["context_report"],
            "jd": test_case.jd,
            "recent_issue": company_context["recent_issue"],
            "student_name": "김철수",
            "student_major": "컴퓨터공학과",
            "student_status": "4학년",
            "experience_summary": "학부 시절 다양한 팀 프로젝트와 인턴 경험을 통해 협업과 문제 해결 능력을 키웠으며, 관련 분야 프로젝트를 다수 수행하였습니다.",
            "questions": test_case.questions,
            "word_limit": test_case.word_limit,
            "conversation": conversation_str,
            "experience_level": "신입"
        }
        
        for i, question in enumerate(test_case.questions):
            # 해당 질문의 flow 가져오기
            flow_text = ""
            if i < len(test_case.results['answer_flows']):
                flow_text = test_case.results['answer_flows'][i]['flow_text']
            
            # 답변 생성
            full_response = ""
            for chunk in generate_cover_letter_response(question, [], format_info, flow_text, test_case.word_limit):
                full_response += chunk
            
            # 파싱
            final_data = parse_json_from_response(full_response)
            if final_data and 'answer' in final_data:
                answer = final_data['answer']
            else:
                answer = full_response
            
            test_case.results['final_answers'].append({
                'question_index': i,
                'question': question,
                'answer': answer,
                'flow_used': flow_text,
                'success': bool(answer),
                'timestamp': datetime.now().isoformat()
            })
            
            await asyncio.sleep(0.5)  # API 제한 방지
            
    except Exception as e:
        test_case.results['errors'].append(f"Answer generation error: {str(e)}")

async def process_single_case(test_case):
    """단일 테스트 케이스를 처리합니다."""
    print(f"🚀 Starting {test_case.case_id}: {test_case.company_name} - {test_case.position_title}")
    test_case.results['start_time'] = datetime.now().isoformat()
    
    try:
        # 1단계: 가이드 생성
        print(f"📝 {test_case.case_id}: Guide generation...")
        guide_text = await run_guide_generation(test_case)
        print(f"  📝 Guide result: {len(guide_text)} characters")
        
        # 2단계: 채팅 시뮬레이션
        print(f"💬 {test_case.case_id}: Chat simulation...")
        conversation_history = await run_chat_simulation(test_case, guide_text)
        print(f"  💬 Chat result: {len(conversation_history)} turns, {len(test_case.results['chat_history'])} records")
        
        # 채팅 기록 확인
        if not test_case.results['chat_history']:
            print(f"  ⚠️ {test_case.case_id}: No chat records found!")
        
        # 3단계: 답변 흐름 생성
        print(f"🔄 {test_case.case_id}: Answer flow generation...")
        await run_answer_flow_generation(test_case, conversation_history)
        print(f"  🔄 Flow result: {len(test_case.results['answer_flows'])} flows")
        
        # 4단계: 최종 답변 생성
        print(f"✍️ {test_case.case_id}: Final answer generation...")
        await run_answer_generation(test_case, conversation_history)
        print(f"  ✍️ Answer result: {len(test_case.results['final_answers'])} answers")
        
        test_case.results['end_time'] = datetime.now().isoformat()
        
        # 소요 시간 계산
        start_time = datetime.fromisoformat(test_case.results['start_time'])
        end_time = datetime.fromisoformat(test_case.results['end_time'])
        test_case.results['total_duration'] = (end_time - start_time).total_seconds()
        
        # 개별 HTML 파일 생성
        generate_individual_html_report(test_case)
        
        # 최종 상태 확인
        chat_count = len(test_case.results['chat_history'])
        error_count = len(test_case.results['errors'])
        print(f"✅ {test_case.case_id}: Completed in {test_case.results['total_duration']:.2f}s")
        print(f"   📊 Summary: {chat_count} chats, {error_count} errors")
        
    except Exception as e:
        test_case.results['errors'].append(f"Process error: {str(e)}")
        print(f"❌ {test_case.case_id}: Failed - {str(e)}")
        # 실패한 경우에도 HTML 생성
        generate_individual_html_report(test_case)
    
    return test_case

def generate_individual_html_report(test_case):
    """개별 테스트 케이스의 HTML 리포트를 생성합니다."""
    # htmls 디렉토리 생성
    htmls_dir = Path("htmls")
    htmls_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    has_errors = bool(test_case.results['errors'])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{test_case.case_id}: {test_case.company_name} - {test_case.position_title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                line-height: 1.6;
            }}
            .header {{
                background: linear-gradient(135deg, {'#e74c3c 0%, #c0392b 100%' if has_errors else '#667eea 0%, #764ba2 100%'});
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .info-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .step {{
                background: white;
                margin-bottom: 25px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .step-header {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-weight: bold;
                font-size: 18px;
            }}
            .step-content {{
                padding: 20px;
            }}
            .chat-turn {{
                background: #ecf0f1;
                padding: 15px;
                margin: 15px 0;
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }}
            .progress-bar {{
                background: #ecf0f1;
                height: 25px;
                border-radius: 12px;
                overflow: hidden;
                margin: 10px 0;
                position: relative;
            }}
            .progress-fill {{
                background: linear-gradient(90deg, #4CAF50, #8BC34A);
                height: 100%;
                transition: width 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                border-left: 4px solid #dc3545;
            }}
            .success {{
                background: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                border-left: 4px solid #28a745;
            }}
            .question-answer {{
                background: #f8f9fa;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
                border-left: 4px solid #007bff;
            }}
            .question-title {{
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
                font-size: 16px;
            }}
            pre {{
                background: #f1f3f4;
                padding: 15px;
                border-radius: 8px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
                border: 1px solid #e9ecef;
                font-size: 14px;
            }}
            .meta-info {{
                background: #e9ecef;
                padding: 10px 15px;
                border-radius: 5px;
                margin: 10px 0;
                font-size: 14px;
                color: #6c757d;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin: 5px 0;
            }}
            .status-success {{
                background: #28a745;
                color: white;
            }}
            .status-error {{
                background: #dc3545;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{'❌' if has_errors else '✅'} {test_case.case_id}</h1>
            <h2>{test_case.company_name} - {test_case.position_title}</h2>
            <p>생성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
        </div>
        
        <div class="info-card">
            <h2>📋 테스트 케이스 정보</h2>
            <p><strong>케이스 ID:</strong> {test_case.case_id}</p>
            <p><strong>회사명:</strong> {test_case.company_name}</p>
            <p><strong>직무:</strong> {test_case.position_title}</p>
            <p><strong>글자수 제한:</strong> {test_case.word_limit}자</p>
            <p><strong>처리 시간:</strong> {test_case.results.get('total_duration', 0):.2f}초</p>
            <p><strong>상태:</strong> <span class="status-badge {'status-error' if has_errors else 'status-success'}">{'실패' if has_errors else '성공'}</span></p>
            
            <h3>📄 JD (Job Description)</h3>
            <pre>{test_case.jd}</pre>
            
            <h3>❓ 자기소개서 질문들</h3>
            <ol>
    """
    
    for question in test_case.questions:
        html_content += f"<li>{question}</li>"
    
    html_content += """
            </ol>
        </div>
    """
    
    # 1단계: 가이드 생성
    html_content += """
        <div class="step">
            <div class="step-header">📝 1단계: 가이드 생성</div>
            <div class="step-content">
    """
    guide_gen = test_case.results.get('guide_generation')
    if guide_gen:
        if guide_gen['success']:
            html_content += f"""
                <div class="success">✅ 가이드 생성 성공</div>
                <div class="meta-info">생성 시간: {guide_gen['timestamp']}</div>
                <pre>{guide_gen['guide_text']}</pre>
            """
        else:
            html_content += f"""
                <div class="error">❌ 가이드 생성 실패: {guide_gen.get('error', 'Unknown error')}</div>
                <div class="meta-info">실패 시간: {guide_gen['timestamp']}</div>
            """
    else:
        html_content += '<div class="error">❌ 가이드 생성 정보 없음</div>'
    html_content += "</div></div>"
    
    # 2단계: 채팅 시뮬레이션
    html_content += """
        <div class="step">
            <div class="step-header">💬 2단계: 채팅 시뮬레이션</div>
            <div class="step-content">
    """
    if test_case.results['chat_history']:
        html_content += f'<div class="success">✅ 총 {len(test_case.results["chat_history"])}개의 대화 턴 완료</div>'
        for i, chat in enumerate(test_case.results['chat_history']):
            progress = chat.get('progress', 0)
            html_content += f"""
                <div class="chat-turn">
                    <h4>턴 {chat['turn']}</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress}%">{progress}%</div>
                    </div>
                    <div class="meta-info">시간: {chat.get('timestamp', '')}</div>
                    <p><strong>진행률 분석:</strong> {chat.get('reasoning', '')}</p>
                    <p><strong>면접관 질문:</strong></p>
                    <pre>{chat.get('interviewer_question', '')}</pre>
                    <p><strong>학생 답변:</strong></p>
                    <pre>{chat.get('student_answer', '답변 없음')}</pre>
                </div>
            """
    else:
        html_content += '<div class="error">❌ 채팅 기록 없음 - 채팅 시뮬레이션이 실패했거나 진행되지 않았습니다.</div>'
        # 에러 원인 분석
        chat_errors = [error for error in test_case.results['errors'] if 'chat' in error.lower() or 'turn' in error.lower()]
        if chat_errors:
            html_content += '<div class="error"><strong>채팅 관련 에러:</strong><ul>'
            for error in chat_errors:
                html_content += f'<li>{error}</li>'
            html_content += '</ul></div>'
    html_content += "</div></div>"
    
    # 3단계: 답변 흐름 생성
    html_content += """
        <div class="step">
            <div class="step-header">🔄 3단계: 답변 흐름 생성</div>
            <div class="step-content">
    """
    if test_case.results['answer_flows']:
        for flow in test_case.results['answer_flows']:
            html_content += f"""
                <div class="question-answer">
                    <div class="question-title">질문 {flow['question_index'] + 1}: {flow['question']}</div>
                    {'<div class="success">✅ 흐름 생성 성공</div>' if flow['success'] else '<div class="error">❌ 흐름 생성 실패</div>'}
                    <div class="meta-info">생성 시간: {flow['timestamp']}</div>
                    <pre>{flow['flow_text'] if flow['flow_text'] else '흐름 생성 실패'}</pre>
                </div>
            """
    else:
        html_content += '<div class="error">❌ 답변 흐름 정보 없음</div>'
    html_content += "</div></div>"
    
    # 4단계: 최종 답변 생성
    html_content += """
        <div class="step">
            <div class="step-header">✍️ 4단계: 최종 답변 생성</div>
            <div class="step-content">
    """
    if test_case.results['final_answers']:
        for answer in test_case.results['final_answers']:
            html_content += f"""
                <div class="question-answer">
                    <div class="question-title">질문 {answer['question_index'] + 1}: {answer['question']}</div>
                    {'<div class="success">✅ 답변 생성 성공</div>' if answer['success'] else '<div class="error">❌ 답변 생성 실패</div>'}
                    <div class="meta-info">생성 시간: {answer['timestamp']}</div>
                    
                    <h4>📝 최종 답변:</h4>
                    <pre>{answer['answer'] if answer['answer'] else '답변 생성 실패'}</pre>
                    
                    <h4>🔄 사용된 답변 흐름:</h4>
                    <pre>{answer['flow_used'] if answer['flow_used'] else '흐름 정보 없음'}</pre>
                </div>
            """
    else:
        html_content += '<div class="error">❌ 최종 답변 정보 없음</div>'
    html_content += "</div></div>"
    
    # 에러 로그
    if test_case.results['errors']:
        html_content += """
            <div class="step">
                <div class="step-header">❌ 에러 로그</div>
                <div class="step-content">
        """
        for error in test_case.results['errors']:
            html_content += f'<div class="error">{error}</div>'
        html_content += "</div></div>"
    
    html_content += """
    </body>
    </html>
    """
    
    # HTML 파일 저장
    filename = f"{test_case.case_id}_{test_case.company_name}_{timestamp}.html"
    # 파일명에서 특수문자 제거
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
    filepath = htmls_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 {test_case.case_id}: HTML 리포트 생성 완료 -> {filepath}")

def generate_html_report(test_cases):
    """HTML 리포트를 생성합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>자기소개서 생성 테스트 리포트 - {timestamp}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .summary {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .test-case {{
                background: white;
                margin-bottom: 30px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .case-header {{
                background: #2c3e50;
                color: white;
                padding: 20px;
                cursor: pointer;
            }}
            .case-header.success {{
                background: #27ae60;
            }}
            .case-header.error {{
                background: #e74c3c;
            }}
            .case-content {{
                padding: 20px;
                display: none;
            }}
            .step {{
                margin-bottom: 25px;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }}
            .step h4 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .chat-turn {{
                background: #ecf0f1;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
            }}
            .progress-bar {{
                background: #ecf0f1;
                height: 20px;
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
            }}
            .progress-fill {{
                background: linear-gradient(90deg, #4CAF50, #8BC34A);
                height: 100%;
                transition: width 0.3s ease;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
            }}
            .success {{
                background: #d4edda;
                color: #155724;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
            }}
            .question-answer {{
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }}
            pre {{
                background: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
        <script>
            function toggleCase(caseId) {{
                const content = document.getElementById(caseId);
                if (content.style.display === 'none' || content.style.display === '') {{
                    content.style.display = 'block';
                }} else {{
                    content.style.display = 'none';
                }}
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h1>🚀 자기소개서 생성 시스템 테스트 리포트</h1>
            <p>생성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <h2>📊 테스트 요약</h2>
            <p><strong>총 테스트 케이스:</strong> {len(test_cases)}개</p>
            <p><strong>성공한 케이스:</strong> {sum(1 for tc in test_cases if not tc.results['errors'])}개</p>
            <p><strong>실패한 케이스:</strong> {sum(1 for tc in test_cases if tc.results['errors'])}개</p>
            <p><strong>평균 처리 시간:</strong> {sum(tc.results.get('total_duration', 0) for tc in test_cases) / len(test_cases):.2f}초</p>
            <hr>
            <p><strong>📁 개별 상세 리포트:</strong> 각 케이스의 상세한 분석은 <strong>htmls/</strong> 디렉토리의 개별 HTML 파일에서 확인하세요</p>
        </div>
    """
    
    for test_case in test_cases:
        has_errors = bool(test_case.results['errors'])
        status_class = "error" if has_errors else "success"
        
        html_content += f"""
        <div class="test-case">
            <div class="case-header {status_class}" onclick="toggleCase('{test_case.case_id}')">
                <h3>📋 {test_case.case_id}: {test_case.company_name} - {test_case.position_title}</h3>
                <p>상태: {'❌ 실패' if has_errors else '✅ 성공'} | 
                   처리 시간: {test_case.results.get('total_duration', 0):.2f}초 | 
                   글자수 제한: {test_case.word_limit}자</p>
            </div>
            <div class="case-content" id="{test_case.case_id}">
        """
        
        # 1단계: 가이드 생성
        html_content += """
                <div class="step">
                    <h4>📝 1단계: 가이드 생성</h4>
        """
        guide_gen = test_case.results.get('guide_generation')
        if guide_gen:
            if guide_gen['success']:
                html_content += f"""
                    <div class="success">✅ 가이드 생성 성공</div>
                    <pre>{guide_gen['guide_text'][:500]}{'...' if len(guide_gen['guide_text']) > 500 else ''}</pre>
                """
            else:
                html_content += f"""
                    <div class="error">❌ 가이드 생성 실패: {guide_gen.get('error', 'Unknown error')}</div>
                """
        html_content += "</div>"
        
        # 2단계: 채팅 시뮬레이션
        html_content += """
                <div class="step">
                    <h4>💬 2단계: 채팅 시뮬레이션</h4>
        """
        if test_case.results['chat_history']:
            html_content += f'<div class="success">✅ {len(test_case.results["chat_history"])}개 턴 완료</div>'
            for i, chat in enumerate(test_case.results['chat_history']):
                progress = chat.get('progress', 0)
                html_content += f"""
                    <div class="chat-turn">
                        <strong>턴 {chat['turn']}:</strong>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {progress}%"></div>
                        </div>
                        <p><strong>진행률:</strong> {progress}%</p>
                        <p><strong>이유:</strong> {chat.get('reasoning', '')}</p>
                        <p><strong>면접관 질문:</strong> {chat.get('interviewer_question', '')}</p>
                        <p><strong>학생 답변:</strong> {chat.get('student_answer', '')}</p>
                    </div>
                """
        else:
            html_content += '<div class="error">❌ 채팅 기록 없음</div>'
        html_content += "</div>"
        
        # 3단계: 답변 흐름 생성
        html_content += """
                <div class="step">
                    <h4>🔄 3단계: 답변 흐름 생성</h4>
        """
        for flow in test_case.results['answer_flows']:
            html_content += f"""
                <div class="question-answer">
                    <h5>질문 {flow['question_index'] + 1}: {flow['question']}</h5>
                    {'<div class="success">✅ 흐름 생성 성공</div>' if flow['success'] else '<div class="error">❌ 흐름 생성 실패</div>'}
                    <pre>{flow['flow_text'][:300]}{'...' if len(flow['flow_text']) > 300 else ''}</pre>
                </div>
            """
        html_content += "</div>"
        
        # 4단계: 최종 답변 생성
        html_content += """
                <div class="step">
                    <h4>✍️ 4단계: 최종 답변 생성</h4>
        """
        for answer in test_case.results['final_answers']:
            html_content += f"""
                <div class="question-answer">
                    <h5>질문 {answer['question_index'] + 1}: {answer['question']}</h5>
                    {'<div class="success">✅ 답변 생성 성공</div>' if answer['success'] else '<div class="error">❌ 답변 생성 실패</div>'}
                    <pre>{answer['answer'][:500]}{'...' if len(answer['answer']) > 500 else ''}</pre>
                </div>
            """
        html_content += "</div>"
        
        # 에러 로그
        if test_case.results['errors']:
            html_content += """
                <div class="step">
                    <h4>❌ 에러 로그</h4>
            """
            for error in test_case.results['errors']:
                html_content += f'<div class="error">{error}</div>'
            html_content += "</div>"
        
        html_content += """
            </div>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    # HTML 파일 저장
    report_filename = f"test_report_{timestamp}.html"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 HTML 리포트가 생성되었습니다: {report_filename}")
    return report_filename

async def main():
    """메인 실행 함수"""
    print("🔧 테스트 케이스 생성 중...")
    test_cases = generate_test_cases(25)
    
    print(f"🚀 {len(test_cases)}개의 테스트 케이스 병렬 처리 시작...")
    start_time = time.time()
    
    # 병렬 처리 (세마포어로 동시 실행 수 제한)
    semaphore = asyncio.Semaphore(10)  # 동시에 10개만 실행
    
    async def process_with_semaphore(test_case):
        async with semaphore:
            return await process_single_case(test_case)
    
    # 모든 테스트 케이스 병렬 실행
    completed_cases = await asyncio.gather(
        *[process_with_semaphore(tc) for tc in test_cases],
        return_exceptions=True
    )
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n✅ 모든 테스트 완료! 총 소요 시간: {total_time:.2f}초")
    
    # 결과 처리
    successful_cases = []
    for result in completed_cases:
        if isinstance(result, Exception):
            print(f"❌ 예외 발생: {result}")
        else:
            successful_cases.append(result)
    
    # HTML 리포트 생성
    report_filename = generate_html_report(successful_cases)
    
    # 간단한 통계
    success_count = sum(1 for tc in successful_cases if not tc.results['errors'])
    print(f"\n📊 최종 통계:")
    print(f"   총 테스트: {len(successful_cases)}개")
    print(f"   성공: {success_count}개")
    print(f"   실패: {len(successful_cases) - success_count}개")
    print(f"   성공률: {success_count/len(successful_cases)*100:.1f}%")
    print(f"\n📁 개별 상세 리포트는 htmls/ 디렉토리에서 확인하세요")
    print(f"📄 통합 리포트: {report_filename}")

if __name__ == "__main__":
    asyncio.run(main()) 