#!/usr/bin/env python3
"""
HTML to PDF 변환 스크립트
htmls 디렉토리의 모든 HTML 파일을 PDF로 변환합니다.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    print("❌ weasyprint가 설치되지 않았습니다. 다음 명령어로 설치해주세요:")
    print("pip install weasyprint")
    sys.exit(1)

def convert_html_to_pdf(html_file_path, pdf_file_path):
    """
    HTML 파일을 PDF로 변환합니다.
    
    Args:
        html_file_path (str): 변환할 HTML 파일 경로
        pdf_file_path (str): 저장할 PDF 파일 경로
        
    Returns:
        bool: 변환 성공 여부
    """
    try:
        print(f"  🔄 Converting: {os.path.basename(html_file_path)}")
        
        # HTML 파일 읽기 및 PDF 변환
        html_doc = HTML(filename=html_file_path)
        
        # CSS 스타일 설정 (한글 폰트 및 페이지 설정)
        css_content = """
        @page {
            size: A4;
            margin: 1cm;
        }
        
        body {
            font-family: "Arial", "Helvetica", sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        h1 { font-size: 24px; }
        h2 { font-size: 20px; }
        h3 { font-size: 16px; }
        h4 { font-size: 14px; }
        
        .progress {
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 2px;
            margin: 5px 0;
        }
        
        .progress-bar {
            background-color: #007bff;
            color: white;
            text-align: center;
            border-radius: 4px;
            padding: 4px;
        }
        
        .step {
            margin-bottom: 20px;
            padding: 15px;
            border-left: 4px solid #007bff;
            background-color: #f8f9fa;
        }
        
        .error {
            color: #dc3545;
            background-color: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        
        .success {
            color: #155724;
            background-color: #d4edda;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            overflow-wrap: break-word;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        """
        
        css = CSS(string=css_content)
        
        # PDF 변환 및 저장
        html_doc.write_pdf(pdf_file_path, stylesheets=[css])
        
        print(f"  ✅ Success: {os.path.basename(pdf_file_path)}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error converting {os.path.basename(html_file_path)}: {str(e)}")
        return False

def main():
    """메인 함수"""
    print("🚀 HTML to PDF 변환 시작")
    print("=" * 50)
    
    # htmls 디렉토리 확인
    htmls_dir = Path("htmls")
    if not htmls_dir.exists():
        print("❌ 'htmls' 디렉토리를 찾을 수 없습니다.")
        return
    
    # HTML 파일 찾기
    html_files = list(htmls_dir.glob("*.html"))
    if not html_files:
        print("❌ 'htmls' 디렉토리에 HTML 파일이 없습니다.")
        return
    
    print(f"📁 발견된 HTML 파일: {len(html_files)}개")
    print("-" * 50)
    
    # 변환 통계
    success_count = 0
    failed_count = 0
    
    # 각 HTML 파일을 PDF로 변환
    for html_file in sorted(html_files):
        # PDF 파일명 생성 (HTML 확장자를 PDF로 변경)
        pdf_file = html_file.with_suffix('.pdf')
        
        # 이미 PDF가 존재하는지 확인
        if pdf_file.exists():
            # 파일 수정 시간 비교
            html_mtime = html_file.stat().st_mtime
            pdf_mtime = pdf_file.stat().st_mtime
            
            if pdf_mtime > html_mtime:
                print(f"  ⏭️  Skip: {pdf_file.name} (이미 최신 버전 존재)")
                success_count += 1
                continue
        
        # 변환 실행
        if convert_html_to_pdf(str(html_file), str(pdf_file)):
            success_count += 1
        else:
            failed_count += 1
    
    # 결과 출력
    print("-" * 50)
    print("📊 변환 완료!")
    print(f"  ✅ 성공: {success_count}개")
    print(f"  ❌ 실패: {failed_count}개")
    print(f"  📁 총 파일: {len(html_files)}개")
    
    if failed_count == 0:
        print("🎉 모든 파일이 성공적으로 변환되었습니다!")
    else:
        print(f"⚠️  {failed_count}개 파일에서 오류가 발생했습니다.")
    
    print(f"📂 결과 파일 위치: {htmls_dir.absolute()}")

if __name__ == "__main__":
    main() 