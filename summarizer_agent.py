import fitz  # PyMuPDF
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Summarizer Agent")

# --- Model and Device Setup ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "facebook/bart-large-cnn"
MAX_INPUT_LENGTH = 1024
MAX_OUTPUT_LENGTH = 512

logger.info(f"Loading model: {MODEL_NAME} on {DEVICE}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
).to(DEVICE)
model.eval()
logger.info("Model loaded successfully")

# --- Request Body Models ---
class PathRequest(BaseModel):
    pdf_path: str

def clean_text(text: str) -> str:
    """기본적인 텍스트 정리"""
    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    # 페이지 번호 제거
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    # 참조 섹션 제거
    text = re.sub(r'\bREFERENCES\b.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\bBibliography\b.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    return text.strip()

def extract_main_content(text: str) -> str:
    """Abstract와 주요 내용 추출"""
    
    # Abstract 찾기
    abstract_match = re.search(
        r'(?i)abstract\s*[:\-]?\s*(.*?)(?=\b(?:introduction|keywords|1\.|I\.)\b)', 
        text, re.DOTALL
    )
    abstract = abstract_match.group(1).strip() if abstract_match else ""
    
    # Introduction부터 Conclusion까지 추출 (References 전까지)
    main_match = re.search(
        r'(?i)(?:introduction|1\.\s*introduction).*?(?=(?:references|bibliography|acknowledgment)\b)',
        text, re.DOTALL
    )
    main_content = main_match.group(0) if main_match else ""
    
    # Abstract + Main Content 결합
    if abstract and main_content:
        combined = f"Abstract: {abstract}\n\nMain Content: {main_content}"
    elif abstract:
        combined = f"Abstract: {abstract}"
    elif main_content:
        combined = main_content
    else:
        # fallback: 전체 텍스트의 첫 부분
        combined = text[:3000]
    
    return combined

def smart_truncate(text: str, max_tokens: int = 900) -> str:
    """토큰 기반으로 텍스트 자르기"""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    if len(tokens) <= max_tokens:
        return text
    
    # 문장 단위로 자르기
    sentences = text.split('.')
    truncated_text = ""
    current_tokens = 0
    
    for sentence in sentences:
        sentence_tokens = len(tokenizer.encode(sentence, add_special_tokens=False))
        if current_tokens + sentence_tokens > max_tokens:
            break
        truncated_text += sentence + "."
        current_tokens += sentence_tokens
    
    return truncated_text

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF에서 텍스트 추출 및 전처리"""
    try:
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        raw_text = ""
        
        for page in doc:
            raw_text += page.get_text() + "\n"
        
        doc.close()
        
        logger.info(f"Raw text length: {len(raw_text)} characters")
        
        # 텍스트 정리
        cleaned_text = clean_text(raw_text)
        main_content = extract_main_content(cleaned_text)
        
        logger.info(f"Processed text length: {len(main_content)} characters")
        
        if len(main_content.strip()) < 100:
            raise HTTPException(status_code=400, detail="Extracted text is too short")
        
        return main_content
        
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

@app.post("/extract_text")
async def extract_text_endpoint(req: PathRequest):
    """PDF에서 텍스트 추출"""
    if not req.pdf_path or not req.pdf_path.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Valid PDF path required")
    
    text = extract_text_from_pdf(req.pdf_path)
    return {"text": text}

@app.post("/summarize_paper")
async def summarize_paper(req: PathRequest):
    """논문 요약 생성"""
    if not req.pdf_path or not req.pdf_path.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Valid PDF path required")
    
    try:
        # 1. 텍스트 추출
        doc_text = extract_text_from_pdf(req.pdf_path)
        
        # 2. 토큰 길이에 맞게 조정
        truncated_text = smart_truncate(doc_text)
        
        logger.info(f"Input text length: {len(truncated_text)} characters")
        
        # 3. 토크나이징
        inputs = tokenizer(
            truncated_text, 
            return_tensors="pt", 
            max_length=MAX_INPUT_LENGTH, 
            truncation=True,
            padding=True
        ).to(DEVICE)
        
        # 4. 요약 생성
        with torch.no_grad():
            summary_ids = model.generate(
                inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_length=MAX_OUTPUT_LENGTH,
                min_length=150,  # 충분한 길이 보장
                num_beams=4,
                length_penalty=1.2,
                early_stopping=True,
                do_sample=False,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3
            )
        
        # 5. 디코딩
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summary = summary.strip()
        
        # 6. 품질 체크
        if not summary or len(summary.split()) < 30:
            logger.warning("Generated summary too short")
            summary = "Unable to generate meaningful summary. The paper content may be too complex or insufficient."
        
        # GPU 메모리 정리
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
        
        logger.info(f"Summary generated: {len(summary)} characters")
        
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
            
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": DEVICE,
        "cuda_available": torch.cuda.is_available()
    }

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Simple Summarizer Agent",
        "model": MODEL_NAME,
        "device": DEVICE,
        "endpoints": ["/summarize_paper", "/extract_text", "/health"]
    }

# 시작시 로그
@app.on_event("startup")
async def startup_event():
    logger.info("Simple Summarizer Agent started")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"Device: {DEVICE}")