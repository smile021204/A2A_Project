import re
import os
import traceback
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Fetcher Agent")
ARXIV_API = "http://export.arxiv.org/api/query"

# Add a User-Agent header to mimic a web browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class FetchRequest(BaseModel):
    topic: str
    max_results: int = 3

@app.post("/fetch_papers")
async def fetch_papers(req: FetchRequest):
    params = {"search_query": f"all:{req.topic}", "start": 0, "max_results": req.max_results}
    try:
        # Add the 'headers=HEADERS' argument to the request call
        resp = requests.get(ARXIV_API, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"arXiv API request failed: {e}")

    content = resp.text
    entries = content.split("<entry>")
    os.makedirs("downloaded_papers", exist_ok=True)
    downloaded = []

    for entry in entries[1 : req.max_results + 1]:
        try:
            title_tag = entry.split("<title>")[1].split("</title>")[0].strip().replace("\n", " ")
            id_match = re.search(r'<id>http://arxiv\.org/abs/([^<]+)</id>', entry)
            if not id_match: continue
            arxiv_id = id_match.group(1)
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            filename = "".join(c for c in title_tag.replace(" ", "_")[:50] if c.isalnum() or c in ["_", "."]) + ".pdf"
            local_path = os.path.join("downloaded_papers", filename)

            # Also add headers when downloading the PDF
            pdf_data = requests.get(pdf_url, headers=HEADERS, timeout=60)
            pdf_data.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(pdf_data.content)

            downloaded.append({
                "title": title_tag,
                "pdf_url": pdf_url,
                "local_path": os.path.abspath(local_path)
            })
        except Exception:
            # If one paper fails, skip it and continue with the others
            continue
            
    return {"papers": downloaded}