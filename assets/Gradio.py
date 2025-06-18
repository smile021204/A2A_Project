import gradio as gr
import requests

# 로컬 환경에서 Coordinator Agent가 실행 중인 주소 (통상 localhost:8000)
COORDINATOR_URL = "http://127.0.0.1:8000/summarization_workflow"

def run_summarization(topic: str, max_results: int):
    """
    Gradio에서 호출되는 함수:
    1) Coordinator Agent에 POST 요청 → JSON 결과 수신
    2) 결과를 읽기 좋은 HTML 형식으로 가공해서 반환
    """
    # 입력 검증
    if not topic.strip():
        return "❗️ 논문 주제(topic)를 입력해주세요."

    try:
        resp = requests.post(
            COORDINATOR_URL,
            json={"topic": topic, "max_results": max_results},
            timeout=120
        )
        resp.raise_for_status()
    except Exception as e:
        return f"❗️ 요청 실패:\n```\n{e}\n```"

    data = resp.json()
    report = data.get("report")

    # 만약 report가 문자열(예: "검색된 논문이 없습니다.")이라면 그대로 반환
    if isinstance(report, str):
        return f"### 📝 결과\n\n{report}"

    # report가 리스트일 경우, 각 논문별 결과를 HTML 형식으로 포맷팅
    if not report:
        return """
        <div style="text-align: center; padding: 2rem; color: #e53e3e;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">❌</div>
            <h3>No Papers Found</h3>
            <p>No academic papers were found for your search topic. Try a different or more general term.</p>
        </div>
        """
    
    # --- 🌟 변경된 부분: 결과물 상단 제목 제거 🌟 ---
    html_parts = ['<div style="padding: 1rem;">']
    
    for item in report:
        idx = item.get("paper_index", "?")
        title = item.get("title", "제목 없음")
        summary = item.get("summary", "")
        feedback = item.get("feedback", "")
        
        # 요약문과 피드백에서 오류 메시지 확인
        summary_status = "❌ Error" if "실패" in summary or "❌" in summary else "✅ Success"
        feedback_status = "❌ Error" if "실패" in feedback or "❌" in feedback else "✅ Success"
        
        html_parts.append(f"""
        <div style="margin-bottom: 2rem; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem;">
                <h3 style="margin: 0; font-size: 1.3rem; font-weight: 600;">
                    📄 Paper #{idx}: {title}
                </h3>
            </div>
            
            <div style="padding: 1.5rem;">
                <div style="margin-bottom: 1.5rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0; color: #2d3748; font-size: 1.1rem;">📝 Summary</h4>
                        <span style="margin-left: auto; font-size: 0.9rem; color: #4a5568;">{summary_status}</span>
                    </div>
                    <div style="background: #f7fafc; border-radius: 8px; padding: 1rem; border-left: 4px solid #667eea; line-height: 1.6;">
                        {summary}
                    </div>
                </div>
                
                <div>
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0; color: #2d3748; font-size: 1.1rem;">💬 Review Feedback</h4>
                        <span style="margin-left: auto; font-size: 0.9rem; color: #4a5568;">{feedback_status}</span>
                    </div>
                    <div style="background: #fff5f5; border-radius: 8px; padding: 1rem; border-left: 4px solid #e53e3e; line-height: 1.6;">
                        {feedback}
                    </div>
                </div>
            </div>
        </div>
        """)
    
    html_parts.append("</div>")
    return "".join(html_parts)

# ─────────────────────────────────────────────────────────────────────────────────
# Gradio 인터페이스 정의
custom_css = """
/* 전체 페이지 스타일 */
.gradio-container, .app, .main {
    max-width: 1400px !important;
    margin: 0 auto !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
.container {
    max-width: 1400px !important;
    margin: 0 auto !important;
}
#search_box .gradio-markdown h3 {
  display: flex;
  align-items: center;   /* 수직 중앙 정렬 */
  justify-content: center;/* 수평 중앙 정렬 (필요시) */
  height: 2.5rem;         /* 헤더 높이에 맞춰 조절 */
  margin: 0;              /* 기본 마진 제거 */
  line-height: 1;         /* flex box와 충돌하지 않도록 */
}
"""

#  --- 🌟 변경된 부분 시작 🌟 ---
# 요청하신 이미지와 동일한 디자인의 헤더 HTML 코드
header_html = """
<div style="background: linear-gradient(to right, #4A3C8B, #6A5ACD); padding: 25px 15px; text-align: center; border-radius: 12px; margin-bottom: 20px;">
    <div style="background-color: rgba(255, 255, 255, 0.2); width: 70px; height: 70px; border-radius: 15px; display: flex; justify-content: center; align-items: center; margin: 0 auto 20px auto;">
        <span style="font-size: 2.5em;">🧠</span>
    </div>
    
    <h1 style="font-size: 2.8em; font-weight: bold; color: white; margin-bottom: 20px;">
        Academic Paper Summarization
    </h1>
    
    <div style="margin: 15px 0; display: inline-block;">
        <span style="background-color: #f0e040; color: #4f3d85; font-weight: bold; padding: 10px 25px; border-radius: 25px; font-size: 1.3em;">a2a</span>
    </div>
    
    <p style="font-size: 1.3em; font-style: italic; color: #e0e0e0; margin-top: 10px;">Autonomous Academic Paper Summarization Team</p>
    <p style="font-size: 1.1em; color: #dcdcdc;">AI-powered paper discovery and summarization tool</p>
</div>
"""
# --- 🌟 변경된 부분 끝 🌟 ---


with gr.Blocks(css=custom_css, theme=gr.themes.Default(), title="A2A Academic Paper Summarization") as demo:
    # 🌟 메인 헤더를 새로운 디자인으로 교체 🌟
    gr.HTML(header_html)
    
    # 메인 컨텐츠 영역 (이하 코드는 원본과 동일)
    with gr.Row(equal_height=False):
        # 왼쪽 입력 패널
        with gr.Column(scale=2, min_width=400):
            # 이전에 추가한 Search Parameters 그룹
            with gr.Group(elem_id="search_box"):
                gr.Markdown("<h3 style='margin:1.5rem 0; font-size:1.1rem; align-items: center'> 📋 Search Parameters")
                
                topic_input = gr.Textbox(
                    label="🔍 Research Topic",
                    placeholder="Enter your research topic (e.g., quantum cryptography, neural networks, blockchain, computer vision)",
                    lines=2,
                    elem_id="topic-input",
                    interactive=True
                )
                
                max_input = gr.Slider(
                    label="📄 Maximum Papers",
                    minimum=1, 
                    maximum=10, 
                    value=3, 
                    step=1,
                    elem_id="max-papers-slider",
                    interactive=True
                )
                
                with gr.Row():
                    run_btn = gr.Button(
                        "🚀 Generate Summaries", 
                        variant="primary",
                        size="lg",
                        interactive=True
                    )
                    clear_btn = gr.Button(
                        "🗑️ Clear Results", 
                        variant="secondary",
                        size="lg",
                        interactive=True
                    )
            
            # 사용법 및 정보 섹션
            gr.HTML("""
            <div style="
                background: linear-gradient(145deg, #fff, #f8fafc);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1.5rem;
                margin-top: 1.5rem;
            ">
                <h3 style="margin-top: 0; color: #2d3748; font-size: 1.2rem;">
                    📖 How It Works
                </h3>
                <div style="list-style: none; padding: 0;">
                    <div style="padding: 0.5rem 0; display: flex; align-items: center;">
                        ✨ Searches arXiv for relevant academic papers
                    </div>
                    <div style="padding: 0.5rem 0; display: flex; align-items: center;">
                        ✨ Downloads and extracts text from PDFs
                    </div>
                    <div style="padding: 0.5rem 0; display: flex; align-items: center;">
                        ✨ Generates AI-powered summaries using local LLM
                    </div>
                    <div style="padding: 0.5rem 0; display: flex; align-items: center;">
                        ✨ Provides quality feedback and review
                    </div>
                    <div style="padding: 0.5rem 0; display: flex; align-items: center;">
                        ✨ Processes 1-10 papers per request
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 1rem; background: #e6fffa; border-radius: 8px; border-left: 4px solid #38b2ac;">
                    <strong>💡 Tip:</strong> Processing may take 1-3 minutes depending on the number of papers and local GPU performance.
                </div>
            </div>
            """)
            
            # 상태 표시 패널
            gr.HTML("""
            <div style="
                background: linear-gradient(145deg, #fff, #f8fafc);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1.5rem;
                margin-top: 1rem;
            ">
                <h3 style="margin-top: 0; color: #2d3748; font-size: 1.2rem;">
                    🔧 Service Status
                </h3>
                <div id="service-status">
                    <div style="padding: 0.5rem; margin: 0.5rem 0; background: #fed7d7; border-radius: 6px; color: #742a2a;">
                        ⚠️ Please ensure all Python microservices are running
                    </div>
                    <div style="font-size: 0.9rem; color: #4a5568; margin-top: 0.5rem;">
                        Required services: Coordinator (8000), Fetcher (8001), Summarizer (8002), Reviewer (8003)
                    </div>
                </div>
            </div>
            """)
    
        # 오른쪽 결과 패널
        with gr.Column(scale=3, min_width=600):
            # --- 🌟 변경된 부분: Summarization Results 박스 제거 🌟 ---
            # The gr.HTML(...) component that created the box has been removed.
            
            # 로딩 상태 표시
            with gr.Group(visible=False) as loading_indicator:
                gr.HTML("""
                <div style="
                    text-align: center;
                    padding: 3rem;
                    background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
                    border-radius: 15px;
                    margin: 1rem;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
                    <div style="font-size: 1.2rem; color: #667eea; font-weight: 600;">
                        Processing your request...
                    </div>
                    <div style="margin-top: 0.5rem; color: #718096;">
                        This may take 1-3 minutes depending on the number of papers
                    </div>
                    <div style="margin-top: 1rem;">
                        <div style="width: 100%; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden;">
                            <div style="width: 100%; height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); animation: loading 2s infinite;"></div>
                        </div>
                    </div>
                </div>
                <style>
                    @keyframes loading {
                        0% { transform: translateX(-100%); }
                        100% { transform: translateX(100%); }
                    }
                </style>
                """)
            
            # 결과 출력 영역
            output_md = gr.HTML(
                value="""
                <div style="text-align: center; padding: 3rem; color: #718096;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📚</div>
                    <h3 style="color: #2d3748; margin-bottom: 0.5rem;">Ready to Summarize</h3>
                    <p>Enter a research topic above and click "Generate Summaries" to begin</p>
                    <div style="margin-top: 2rem; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto;">
                        <h4 style="color: #4a5568; margin-bottom: 1rem;">💡 Example Topics:</h4>
                        <ul style="color: #718096; line-height: 1.6;">
                            <li>Quantum machine learning</li>
                            <li>Transformer neural networks</li>
                            <li>Blockchain consensus algorithms</li>
                            <li>Computer vision deep learning</li>
                            <li>Natural language processing</li>
                        </ul>
                    </div>
                </div>
                """,
                elem_id="results-output"
            )
    
    # 버튼 기능 추가
    def show_loading():
        return gr.update(visible=True)
    
    def hide_loading():
        return gr.update(visible=False)
    
    def clear_all():
        initial_message = """
        <div style="text-align: center; padding: 3rem; color: #718096;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📚</div>
            <h3 style="color: #2d3748; margin-bottom: 0.5rem;">Ready to Summarize</h3>
            <p>Enter a research topic above and click "Generate Summaries" to begin</p>
            <div style="margin-top: 2rem; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto;">
                <h4 style="color: #4a5568; margin-bottom: 1rem;">💡 Example Topics:</h4>
                <ul style="color: #718096; line-height: 1.6;">
                    <li>Quantum machine learning</li>
                    <li>Transformer neural networks</li>
                    <li>Blockchain consensus algorithms</li>
                    <li>Computer vision deep learning</li>
                    <li>Natural language processing</li>
                </ul>
            </div>
        </div>
        """
        return ["", gr.update(value=initial_message)]
    
    # 버튼 이벤트 연결
    run_btn.click(
        fn=show_loading,
        inputs=None,
        outputs=loading_indicator
    ).then(
        fn=run_summarization,
        inputs=[topic_input, max_input],
        outputs=output_md
    ).then(
        fn=hide_loading,
        inputs=None,
        outputs=loading_indicator
    )
    
    clear_btn.click(
        fn=clear_all,
        inputs=None,
        outputs=[topic_input, output_md]
    )
    
    # 키보드 단축키 추가
    topic_input.submit(
        fn=show_loading,
        inputs=None,
        outputs=loading_indicator
    ).then(
        fn=run_summarization,
        inputs=[topic_input, max_input],
        outputs=output_md
    ).then(
        fn=hide_loading,
        inputs=None,
        outputs=loading_indicator
    )

# Gradio 서버 실행
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)