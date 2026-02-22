# CAPTCHA 數字辨識（CPU 版本）

本專案使用 **PaddleOCR（僅 CPU）** 進行數字型 CAPTCHA 圖片辨識。

本程式特點：

- 多種影像前處理（縮放、灰階化、二值化、形態學處理）
- 採用序列辨識模式（不切割單一字元）
- 自動過濾非數字字元
- 支援動態長度數字（不固定 6 碼）
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

目前主程式為 `detector.py`，請使用 `--image` 參數指定圖片路徑：

```bash
# 指令格式
python detector.py --image <圖片路徑>

# 範例 (測試資料夾內的 test0.png)
python detector.py --image test_data/test0.png
```

執行後會輸出一行純數字，例如：

```text
895537
```

程式僅會輸出辨識結果（不含其他 log）。

---

## 專案結構

```text
CAPTCHA_Detector/
├── environment.yml
├── detector.py
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
5. 只保留數字字元
6. 自動選擇最佳結果

此方法可避免切字錯誤問題，特別適合：

- 數字黏在一起
- 字元重疊
- 有干擾線
- 背景雜訊多的 CAPTCHA

---

## 特點

- 僅使用 CPU（不需 GPU）
- 無固定數字長度限制
- 完全本地執行
- 適用於重疊與干擾型驗證碼

---

## 使用用途

僅供學術研究與技術測試使用。
