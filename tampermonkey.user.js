// ==UserScript==
// @name         Local CAPTCHA Autofill
// @namespace    local.captcha.helper
// @version      0.1.0
// @description  Detect CAPTCHA image/canvas, call local OCR API, and fill input.
// @match        https://www.ccxp.nthu.edu.tw/ccxp/INQUIRE/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// ==/UserScript==

(function () {
  "use strict";
  console.log("CAPTCHA script is running");

  const CONFIG = {
    captchaImageSelector:
      "body > table:nth-child(2) > tbody > tr > td:nth-child(1) > table > tbody > tr > td > div > div:nth-child(1) > form > img",
    captchaCanvasSelector: "canvas.captcha",
    captchaInputSelector:
      "body > table:nth-child(2) > tbody > tr > td:nth-child(1) > table > tbody > tr > td > div > div:nth-child(1) > form > input:nth-child(13)",
    captchaRefreshSelector: "",
    submitSelector: "",
    apiUrl: "http://127.0.0.1:65435/solve",
    ocrMode: "alnum", // numeric | alpha | alnum
    captchaLength: 0, // 0 means auto, e.g. 6 for fixed-length CAPTCHA
    maxRetries: 3,
    retryDelayMs: 1000,
    minTextLength: 3,
    maxTextLength: 12,
    autoSubmit: false,
    debug: true,
  };

  let solving = false;

  function log(...args) {
    if (CONFIG.debug) {
      console.log("[captcha-helper]", ...args);
    }
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function isReasonableCaptchaText(text) {
    if (!text) return false;
    if (text.length < CONFIG.minTextLength) return false;
    if (text.length > CONFIG.maxTextLength) return false;
    return /^[A-Za-z0-9]+$/.test(text);
  }

  async function blobFromImageElement(imgEl) {
    const src = imgEl.currentSrc || imgEl.src;
    if (!src) {
      throw new Error("CAPTCHA image src is empty");
    }
    const response = await fetch(src, { cache: "no-store", credentials: "include" });
    if (!response.ok) {
      throw new Error(`Fetch CAPTCHA image failed: ${response.status}`);
    }
    return await response.blob();
  }

  async function blobFromCanvasElement(canvasEl) {
    return await new Promise((resolve, reject) => {
      canvasEl.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error("Canvas toBlob failed"));
            return;
          }
          resolve(blob);
        },
        "image/png"
      );
    });
  }

  function callLocalOcr(blob) {
    const formData = new FormData();
    formData.append("file", blob, "captcha.png");
    formData.append("mode", CONFIG.ocrMode);
    formData.append("length", String(CONFIG.captchaLength || 0));

    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "POST",
        url: CONFIG.apiUrl,
        data: formData,
        responseType: "json",
        timeout: 15000,
        onload: (resp) => {
          if (resp.status < 200 || resp.status >= 300) {
            reject(new Error(`OCR API error: HTTP ${resp.status}`));
            return;
          }

          const data = resp.response;
          if (!data) {
            reject(new Error("OCR API returned empty response"));
            return;
          }

          const text = (data.text || "").trim();
          resolve(text);
        },
        ontimeout: () => reject(new Error("OCR API request timeout")),
        onerror: () => reject(new Error("OCR API request failed")),
      });
    });
  }

  function getCaptchaSourceElement() {
    const img = document.querySelector(CONFIG.captchaImageSelector);
    if (img) return { type: "img", element: img };

    const canvas = document.querySelector(CONFIG.captchaCanvasSelector);
    if (canvas) return { type: "canvas", element: canvas };

    return null;
  }

  function triggerInputEvents(inputEl) {
    inputEl.dispatchEvent(new Event("input", { bubbles: true }));
    inputEl.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function refreshCaptchaIfPossible() {
    if (!CONFIG.captchaRefreshSelector) return;
    const refreshEl = document.querySelector(CONFIG.captchaRefreshSelector);
    if (refreshEl) refreshEl.click();
  }

  function maybeSubmit() {
    if (!CONFIG.autoSubmit || !CONFIG.submitSelector) return;
    const submitEl = document.querySelector(CONFIG.submitSelector);
    if (submitEl) submitEl.click();
  }

  async function solveCaptchaOnce() {
    const source = getCaptchaSourceElement();
    const inputEl = document.querySelector(CONFIG.captchaInputSelector);
    if (!source || !inputEl) return false;

    const blob =
      source.type === "img"
        ? await blobFromImageElement(source.element)
        : await blobFromCanvasElement(source.element);

    const text = await callLocalOcr(blob);
    log("OCR result:", text);

    if (!isReasonableCaptchaText(text)) return false;

    inputEl.value = text;
    triggerInputEvents(inputEl);
    maybeSubmit();
    return true;
  }

  async function solveWithRetries() {
    if (solving) return;
    solving = true;
    try {
      for (let i = 0; i < CONFIG.maxRetries; i += 1) {
        try {
          const ok = await solveCaptchaOnce();
          if (ok) {
            log("CAPTCHA filled");
            return;
          }
        } catch (err) {
          log("Solve attempt failed:", err);
        }
        refreshCaptchaIfPossible();
        await sleep(CONFIG.retryDelayMs);
      }
      log("CAPTCHA solve stopped after max retries");
    } finally {
      solving = false;
    }
  }

  function setupAutoDetection() {
    const observer = new MutationObserver(() => {
      solveWithRetries();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  solveWithRetries();
  setupAutoDetection();
})();
