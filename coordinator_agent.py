from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="Coordinator Agent")

FETCHER_URL = "http://127.0.0.1:8001/fetch_papers"
SUMMARIZER_URL_SUM = "http://127.0.0.1:8002/summarize_paper"
SUMMARIZER_URL_TEXT = "http://127.0.0.1:8002/extract_text"
REVIEWER_URL = "http://127.0.0.1:8003/review_summary"

class CoordinatorRequest(BaseModel):
    topic: str
    max_results: int = 3

@app.post("/summarization_workflow")
async def summarization_workflow(req: CoordinatorRequest):
    try:
        fetch_resp = requests.post(FETCHER_URL, json={"topic": req.topic, "max_results": req.max_results}, timeout=30)
        fetch_resp.raise_for_status()
        papers = fetch_resp.json().get("papers", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetcher agent failed: {e}")

    if not papers:
        return {"report": "No papers found for the given topic."}

    report = []
    for idx, paper in enumerate(papers, start=1):
        title = paper.get("title", "Unknown Title")
        pdf_path = paper.get("local_path", "")
        summary, feedback = "",""
        try:
            sum_resp = requests.post(SUMMARIZER_URL_SUM, json={"pdf_path": pdf_path}, timeout=180)
            sum_resp.raise_for_status()
            summary = sum_resp.json().get("summary", "")
        except Exception as e:
            summary = f"❌ Summary generation failed: {e}"

        try:
            if "failed" not in summary:
                text_resp = requests.post(SUMMARIZER_URL_TEXT, json={"pdf_path": pdf_path}, timeout=60)
                text_resp.raise_for_status()
                original_text = text_resp.json().get("text", "")

                # --- 🌟 변경된 부분: 리뷰어 타임아웃을 10분(600초)으로 늘림 🌟 ---
                rev_resp = requests.post(
                    REVIEWER_URL,
                    json={"original_text": original_text, "summary_text": summary},
                    timeout=600
                )
                # --- 🌟 변경된 부분 끝 🌟 ---

                rev_resp.raise_for_status()
                feedback = rev_resp.json().get("feedback", "")
            else:
                feedback = "❌ Review skipped due to summary failure."
        except Exception as e:
            feedback = f"❌ Review generation failed: {e}"

        report.append({
            "paper_index": idx,
            "title": title,
            "summary": summary,
            "feedback": feedback
        })
    return {"report": report}