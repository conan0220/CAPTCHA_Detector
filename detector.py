import cv2
import numpy as np
import re
import argparse
from paddleocr import PaddleOCR

VALID_MODES = ("numeric", "alpha", "alnum")

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

def filter_by_mode(s, mode):
    if mode == "numeric":
        return "".join(re.findall(r"\d", s))
    if mode == "alpha":
        return "".join(re.findall(r"[A-Za-z]", s))
    if mode == "alnum":
        return "".join(re.findall(r"[A-Za-z0-9]", s))
    raise ValueError(f"Unsupported mode: {mode}")

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

def recognize_sequence_with_conf(ocr, img_gray_or_bin, mode):
    r = ocr.ocr(img_gray_or_bin, det=False, rec=True, cls=False)
    txt = extract_text_any(r)
    conf = extract_conf_any(r)
    s = filter_by_mode(txt, mode)
    return s, conf

def score_candidate(s, conf, expected_length=None):
    if not s:
        return -1e9
    base = min(len(s), 12) * 10
    if expected_length is not None:
        # Prioritize candidates matching the expected CAPTCHA length.
        if len(s) == expected_length:
            base += 500
        else:
            base -= abs(len(s) - expected_length) * 120
    c = conf if conf is not None else 0.0
    return base + c * 100.0


def solve_captcha_bgr(ocr, bgr, mode="alnum", expected_length=None):
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode}. Use one of: {', '.join(VALID_MODES)}")
    if expected_length is not None and expected_length <= 0:
        raise ValueError("expected_length must be a positive integer")

    best_s = ""
    best_conf = None
    best_score = -1e18

    for im in preprocess_variants(bgr):
        s, conf = recognize_sequence_with_conf(ocr, im, mode)
        sc = score_candidate(s, conf, expected_length=expected_length)
        if sc > best_score:
            best_score = sc
            best_s = s
            best_conf = conf

    return best_s, best_conf


def solve_captcha_image_path(ocr, image_path, mode="alnum", expected_length=None):
    bgr = cv2.imread(image_path)
    if bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    return solve_captcha_bgr(ocr, bgr, mode=mode, expected_length=expected_length)

def parse_args():
    parser = argparse.ArgumentParser(description="CAPTCHA OCR")
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the input image, e.g. test_data/test0.png",
    )
    parser.add_argument(
        "--mode",
        default="alnum",
        choices=VALID_MODES,
        help="Recognition mode: numeric (digits), alpha (letters), alnum (letters+digits)",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=0,
        help="Expected CAPTCHA length; 0 means auto (no fixed length)",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    ocr = PaddleOCR(lang="en", use_angle_cls=False, show_log=False)
    expected_length = args.length if args.length > 0 else None
    best_s, _ = solve_captcha_image_path(
        ocr, args.image, mode=args.mode, expected_length=expected_length
    )

    print(best_s)

if __name__ == "__main__":
    main()
