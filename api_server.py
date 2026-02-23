import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR

from detector import VALID_MODES, solve_captcha_bgr

app = FastAPI(title="Local CAPTCHA OCR API")

# Limit this to your authorized domain(s) in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

ocr = PaddleOCR(lang="en", use_angle_cls=False, show_log=False)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/solve")
async def solve(
    file: UploadFile = File(...), mode: str = Form("alnum"), length: int = Form(0)
):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {mode}. Use one of: {', '.join(VALID_MODES)}",
        )
    if length < 0:
        raise HTTPException(status_code=400, detail="length must be >= 0")

    arr = np.frombuffer(raw, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image data")

    expected_length = length if length > 0 else None
    text, confidence = solve_captcha_bgr(ocr, bgr, mode=mode, expected_length=expected_length)
    return {"text": text, "confidence": confidence, "mode": mode, "length": length}
