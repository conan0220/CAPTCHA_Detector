import cv2
import numpy as np
import re
import argparse
from paddleocr import PaddleOCR

def extract_text_any(r):
    if r is None:
        return ""
    if isinstance(r, str):
        return r
    if isinstance(r, (float, int)):
        return ""
    if isinstance(r, dict):
        t = r.get("text")
        return t if isinstance(t, str) else ""
    if isinstance(r, (list, tuple)):
        for item in r:
            t = extract_text_any(item)
            if t:
                return t
    return ""

def extract_conf_any(r):
    if r is None:
        return None
    if isinstance(r, (float, int)):
        v = float(r)
        return v if 0.0 <= v <= 1.0 else None
    if isinstance(r, dict):
        v = r.get("score")
        if isinstance(v, (float, int)):
            v = float(v)
            return v if 0.0 <= v <= 1.0 else None
    if isinstance(r, (list, tuple)):
        floats = []
        for item in r:
            v = extract_conf_any(item)
            if v is not None:
                floats.append(v)
        if floats:
            return floats[0]
    return None

def alnum_case_sensitive(s):
    return "".join(re.findall(r"[A-Za-z0-9]", s))

def preprocess_variants(bgr):
    h, w = bgr.shape[:2]
    scale = 4
    img = cv2.resize(bgr, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    outs = []

    th1 = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 10
    )
    outs.append(th1)

    th2 = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 7
    )
    outs.append(th2)

    _, th3 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    outs.append(th3)

    outs2 = []
    for im in outs:
        im2 = cv2.medianBlur(im, 3)
        k = np.ones((2, 2), np.uint8)
        outs2.append(cv2.morphologyEx(im2, cv2.MORPH_OPEN, k, iterations=1))
        outs2.append(cv2.morphologyEx(im2, cv2.MORPH_CLOSE, k, iterations=1))

        inv = 255 - im2
        outs2.append(inv)
        outs2.append(cv2.morphologyEx(inv, cv2.MORPH_OPEN, k, iterations=1))
        outs2.append(cv2.morphologyEx(inv, cv2.MORPH_CLOSE, k, iterations=1))

    uniq = []
    seen = set()
    for im in outs2:
        key = (im.shape[0], im.shape[1], int(np.sum(im)))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(im)
    return uniq

def recognize_sequence_with_conf(ocr, img_gray_or_bin):
    r = ocr.ocr(img_gray_or_bin, det=False, rec=True, cls=False)
    txt = extract_text_any(r)
    conf = extract_conf_any(r)
    s = alnum_case_sensitive(txt)
    return s, conf

def score_candidate(s, conf):
    if not s:
        return -1e9
    base = min(len(s), 12) * 10
    c = conf if conf is not None else 0.0
    return base + c * 100.0

def parse_args():
    parser = argparse.ArgumentParser(description="CAPTCHA alphanumeric OCR")
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the input image, e.g. test_data/test0.png",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    bgr = cv2.imread(args.image)
    if bgr is None:
        raise FileNotFoundError(f"Cannot read image: {args.image}")
    ocr = PaddleOCR(lang="en", use_angle_cls=False, show_log=False)

    best_s = ""
    best_score = -1e18

    for im in preprocess_variants(bgr):
        s, conf = recognize_sequence_with_conf(ocr, im)
        sc = score_candidate(s, conf)
        if sc > best_score:
            best_score = sc
            best_s = s

    print(best_s)

if __name__ == "__main__":
    main()
