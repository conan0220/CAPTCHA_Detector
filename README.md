# CAPTCHA 英數辨識（CPU 版本）

本專案使用 **PaddleOCR（僅 CPU）** 進行 CAPTCHA 圖片辨識，支援三種模式：

- `numeric`：純數字（0-9）
- `alpha`：純英文（A-Z、a-z）
- `alnum`：英文數字混合（A-Z、a-z、0-9）

本程式特點：

- 多種影像前處理（縮放、灰階化、二值化、形態學處理）
- 採用序列辨識模式（不切割單一字元）
- 可選擇純數字 / 純英文 / 英數混合
- 支援動態長度字串（不固定長度）
- 完全離線執行

---

## 系統需求

- Windows / Linux
- 已安裝 Conda（建議 Miniconda）
- Python 3.9（建議）

Miniconda（Windows x86_64）下載：

- <https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe>

---

## 環境建立

打開 `Anaconda Prompt`

```bash
cd <專案資料夾路徑> # 例如：cd D:\repos\CAPTCHA_Detector

# 根據環境檔建立 Conda 環境 (包括 Python 3.9 和 PaddleOCR CPU 版本)
conda env create -f environment.yml

# 啟動環境
conda activate paddleocr_cpu
```

---

## 執行方式

目前主程式為 `detector.py`，請使用 `--image` 指定圖片，`--mode` 指定辨識模式，`--length` 指定位數：

```bash
# 指令格式
python detector.py --image <圖片路徑> --mode <numeric|alpha|alnum> --length <位數>

# 範例：純數字 + 固定 6 碼
python detector.py --image test_data/test0.png --mode numeric --length 6

# 範例：純英文 + 固定 5 碼
python detector.py --image test_data/test1.png --mode alpha --length 5

# 範例：英數混合（預設模式，位數自動）
python detector.py --image test_data/test2.png --mode alnum
```

執行後會輸出一行符合模式的字串，例如：

```text
aB95x7
```

程式僅會輸出辨識結果（不含其他 log）。

---

## 專案結構

```text
CAPTCHA_Detector/
├── environment.yml
├── detector.py
├── api_server.py
├── tampermonkey.user.js
├── test_data/
│   ├── test0.png
│   ├── test1.png
│   ├── test2.png
│   ├── test3.png
│   └── test4.png
└── README.md
```

---

## 技術說明

本專案流程如下：

1. 圖片放大，提高辨識解析度
2. 灰階化與模糊處理
3. 產生多種二值化版本
4. 進行序列辨識（`det=False`）
5. 依模式過濾字元（數字 / 英文 / 英數混合）
6. 自動選擇最佳結果

此方法可避免切字錯誤問題，特別適合：

- 字元黏在一起
- 字元重疊
- 有干擾線
- 背景雜訊多的 CAPTCHA

---

## 特點

- 僅使用 CPU（不需 GPU）
- 無固定字串長度限制
- 完全本地執行
- 適用於重疊與干擾型驗證碼

---

## 本機 OCR API（給自動化腳本使用）

新增檔案：

- `api_server.py`：提供 `POST /solve`，上傳圖片後回傳辨識文字（支援 `mode`、`length`）。
- `tampermonkey.user.js`：在指定網域偵測 CAPTCHA，呼叫本機 API，自動回填欄位。

先安裝 API 需要套件：

```bash
conda activate paddleocr_cpu
pip install fastapi uvicorn python-multipart
```

啟動 API：

```bash
uvicorn api_server:app --host 127.0.0.1 --port 65435
```

測試健康檢查：

```bash
curl http://127.0.0.1:65435/health
```

測試辨識 API（可指定 `mode` 與 `length`）：

```bash
curl -X POST "http://127.0.0.1:65435/solve" ^
  -F "file=@test_data/test0.png" ^
  -F "mode=numeric" ^
  -F "length=6"
```

在 Tampermonkey 匯入 `tampermonkey.user.js` 後，請先修改：

- `@match`（只填你授權的網站網域）
- `CONFIG.captchaImageSelector` / `CONFIG.captchaCanvasSelector`
- `CONFIG.captchaInputSelector`
- `CONFIG.captchaRefreshSelector`（若頁面有刷新按鈕）
- `CONFIG.ocrMode`（`numeric` / `alpha` / `alnum`）
- `CONFIG.captchaLength`（0 為自動；例如 6 代表固定 6 碼）

---

## 使用用途

僅供學術研究與技術測試使用。
