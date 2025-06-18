from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import logging
import gc

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Reviewer Agent")

# 전역 변수
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "google/flan-t5-large"
MAX_INPUT_LENGTH = 512
MAX_OUTPUT_LENGTH = 256

# 모델 초기화
logger.info(f"Loading model: {MODEL_NAME} on {DEVICE}")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
    ).to(DEVICE)
    model.eval()
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise RuntimeError(f"Model loading failed: {e}")

class ReviewRequest(BaseModel):
    original_text: str
    summary_text: str

def truncate_text(text: str, max_tokens: int = 300) -> str:
    """토큰 기반으로 텍스트 자르기"""
    try:
        tokens = tokenizer.encode(text, add_special_tokens=False)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return tokenizer.decode(truncated_tokens, skip_special_tokens=True)
    except Exception as e:
        logger.warning(f"Token truncation failed: {e}")
        return text[:max_tokens * 3]

def create_review_prompt(original_text: str, summary_text: str) -> str:
    """상세한 리뷰 프롬프트 생성"""
    
    prompt = f"""You are an expert academic reviewer. Evaluate this research paper summary by checking if it includes these essential elements:

1. Research Problem/Objective: What problem does the paper solve?
2. Methodology: What approach or methods were used?
3. Key Results: What were the main findings or outcomes?
4. Contributions: What new knowledge or improvements does this provide?
5. Significance: Why is this work important?

ORIGINAL PAPER EXCERPT:
{original_text[:600]}

SUMMARY TO EVALUATE:
{summary_text}

TASK: Identify what important information is missing from the summary. Be specific about which elements are absent or unclear.

If the summary covers all key aspects well, respond: "Summary adequately covers the essential research elements."

If elements are missing, list them specifically like: "Missing elements: [specific items]"

Response:"""
    
    return prompt

def check_summary_basic_quality(summary_text: str) -> str:
    """기본적인 요약 품질 체크"""
    summary_lower = summary_text.lower()
    missing_elements = []
    
    # 각 핵심 요소 체크
    if not any(word in summary_lower for word in ["method", "approach", "technique", "algorithm", "framework"]):
        missing_elements.append("methodology description")
    
    if not any(word in summary_lower for word in ["result", "finding", "performance", "outcome", "achieve"]):
        missing_elements.append("key results or findings")
    
    if not any(word in summary_lower for word in ["objective", "goal", "purpose", "problem", "address"]):
        missing_elements.append("research objectives")
    
    if not any(word in summary_lower for word in ["significant", "important", "novel", "contribution", "advance"]):
        missing_elements.append("research significance")
    
    # 요약이 너무 짧은지 체크
    if len(summary_text.split()) < 25:
        missing_elements.append("sufficient detail")
    
    return missing_elements

@app.post("/review_summary")
async def review_summary(req: ReviewRequest):
    """요약 검토 API 엔드포인트"""
    
    # 입력 검증
    if not req.original_text or not req.summary_text:
        raise HTTPException(status_code=400, detail="Original text and summary are required.")
    
    if not req.original_text.strip() or not req.summary_text.strip():
        raise HTTPException(status_code=400, detail="Original text and summary cannot be empty.")
    
    if len(req.original_text) < 100:
        raise HTTPException(status_code=400, detail="Original text is too short for review.")
    
    try:
        logger.info(f"Processing review - Original: {len(req.original_text)} chars, Summary: {len(req.summary_text)} chars")
        
        # 1. 기본 품질 체크 먼저 수행
        missing_basic = check_summary_basic_quality(req.summary_text)
        
        # 2. 기본 체크에서 문제가 많다면 AI 모델 없이 응답
        if len(missing_basic) >= 3:
            feedback = f"Missing elements: {', '.join(missing_basic)}. The summary needs more comprehensive coverage of the research."
            logger.info("Basic quality check failed, returning structured feedback")
            return {"feedback": feedback}
        
        # 3. AI 모델을 사용한 상세 분석
        try:
            # 텍스트 길이 조정
            original_truncated = truncate_text(req.original_text, max_tokens=250)
            prompt = create_review_prompt(original_truncated, req.summary_text)
            
            logger.info("Using AI model for detailed review")
            
            # 토크나이징
            inputs = tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=MAX_INPUT_LENGTH, 
                truncation=True,
                padding=True
            ).to(DEVICE)
            
            logger.info(f"Input token length: {inputs['input_ids'].shape[1]}")
            
            # 모델 추론
            with torch.no_grad():
                output_ids = model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs.get('attention_mask'),
                    max_new_tokens=120,
                    num_beams=3,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.9,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
            
            # 디코딩
            ai_feedback = tokenizer.decode(output_ids[0], skip_special_tokens=True)
            
            # 프롬프트 부분 제거
            response_indicators = ["Response:", "Answer:", "Review:", "Missing elements:", "Evaluation:"]
            for indicator in response_indicators:
                if indicator in ai_feedback:
                    ai_feedback = ai_feedback.split(indicator)[-1].strip()
                    break
            
            # AI 응답 품질 체크
            if (ai_feedback and 
                len(ai_feedback.split()) > 8 and 
                len(ai_feedback) < 250 and
                not any(phrase in ai_feedback.lower() for phrase in ["i cannot", "as an ai", "original paper excerpt"])):
                
                # 기본 체크 결과와 AI 결과 결합
                if missing_basic:
                    final_feedback = f"Missing elements: {', '.join(missing_basic)}. {ai_feedback}"
                else:
                    final_feedback = ai_feedback
            else:
                # AI 응답이 부적절한 경우 기본 체크 결과 사용
                if missing_basic:
                    final_feedback = f"Missing elements: {', '.join(missing_basic)}."
                else:
                    final_feedback = "Summary covers most essential elements but could benefit from more specific details."
                    
        except Exception as e:
            logger.warning(f"AI model failed, using basic feedback: {e}")
            if missing_basic:
                final_feedback = f"Missing elements: {', '.join(missing_basic)}."
            else:
                final_feedback = "Summary appears adequate but detailed analysis unavailable."
        
        # 최종 정리 (너무 긴 경우 자르기)
        if len(final_feedback) > 200:
            sentences = final_feedback.split('.')[:2]
            final_feedback = '. '.join(s.strip() for s in sentences if s.strip())
            if final_feedback and not final_feedback.endswith('.'):
                final_feedback += '.'
        
        # GPU 메모리 정리
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
        
        logger.info(f"Review completed: {final_feedback[:80]}...")
        
        return {"feedback": final_feedback}
        
    except torch.cuda.OutOfMemoryError:
        logger.error("GPU memory insufficient")
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail="GPU memory insufficient.")
    
    except Exception as e:
        logger.error(f"Review generation failed: {e}")
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
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
        "service": "Simple Reviewer Agent",
        "model": MODEL_NAME,
        "device": DEVICE,
        "endpoints": ["/review_summary", "/health"]
    }

# 애플리케이션 시작시 로그
@app.on_event("startup")
async def startup_event():
    logger.info("Simple Reviewer Agent started")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"Device: {DEVICE}")

# 종료시 정리
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Reviewer Agent")
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
    gc.collect()