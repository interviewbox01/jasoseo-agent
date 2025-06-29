import os
import random
import datetime
import json
import multiprocessing
from tqdm import tqdm
from llm_functions_w_structured_output import analyze_company_size

# 테스트를 위한 환경 변수 로드 (필요시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


example_company_name = ["삼성전자", "현대자동차", "LG전자", "SK하이닉스", "포스코홀딩스", "한화", "롯데케미칼", "CJ제일제당", "두산에너빌리티", "KT", "셀트리온헬스케어", "에스에프에이", "하림지주", "이녹스첨단소재", "코웨이", "한솔케미칼", "덴티움", "에코프로에이치엔", "다우기술", "제넥신", "오스템임플란트", "비츠로셀", "바디프랜드", "씨아이에스", "아이센스", "이루다", "나노신소재", "위메이드맥스", "에이치엘사이언스", "더네이쳐홀딩스", "피에스케이", "뉴파워프라즈마", "지누스", "원익IPS", "지아이이노베이션", "뤼이드", "센드버드", "직방", "리디", "버즈빌", "당근마켓", "컬리", "왓챠", "루닛", "플라네타리움", "크래프톤 벤처스", "뱅크샐러드", "직토", "트레바리", "메스프레소"]