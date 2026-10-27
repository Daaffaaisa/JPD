// IDM Clone Content Script - Pure Event-Driven, Non-Blocking, 0% CPU Overhead
(function () {
  "use strict";

  if (window.__idm_clone_active) return;
  window.__idm_clone_active = true;

  let panel = null;
  let activeMediaEl = null;
  let currentTargetUrl = null;
  let currentTargetTitle = "";
  let hideTimeout = null;

  function getOrCreatePanel() {
    if (panel && document.documentElement.contains(panel)) {
      return panel;
    }

    panel = document.createElement("div");
    panel.id = "idm-clone-overlay-panel";
    panel.style.cssText = `
      position: fixed !important;
      z-index: 2147483647 !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
      display: none;
      pointer-events: auto !important;
      user-select: none !important;
      transition: opacity 0.2s ease !important;
      opacity: 0;
    `;

    panel.innerHTML = `
      <div id="idm-dl-action-btn" style="
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        background: linear-gradient(180deg, #2b78e4 0%, #1555b5 100%) !important;
        color: #ffffff !important;
        padding: 5px 11px !important;
        border-radius: 4px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.45) !important;
        cursor: pointer !important;
        font-size: 11px !important;
        font-weight: bold !important;
        border: 1px solid #0e3d82 !important;
        line-height: 1.2 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
      ">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span id="idm-dl-btn-text">Download dengan IDM Clone</span>
      </div>
    `;

    panel.addEventListener("mouseenter", () => {
      if (hideTimeout) clearTimeout(hideTimeout);
    });

    panel.addEventListener("mouseleave", () => {
      scheduleHide();
    });

    const btn = panel.querySelector("#idm-dl-action-btn");
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();

      let targetUrl = currentTargetUrl;
      let targetTitle = currentTargetTitle || document.title || "berkas_unduhan";

      if (!targetUrl) {
        if (activeMediaEl) {
          targetUrl = activeMediaEl.currentSrc || activeMediaEl.src;
        } else {
          targetUrl = window.location.href;
        }
      }

      openIDMDownloadDialog(targetUrl, targetTitle);
    });

    document.documentElement.appendChild(panel);
    return panel;
  }

  function scheduleHide() {
    if (hideTimeout) clearTimeout(hideTimeout);
    hideTimeout = setTimeout(() => {
      if (panel) {
        panel.style.opacity = "0";
        setTimeout(() => {
          if (panel && panel.style.opacity === "0") {
            panel.style.display = "none";
          }
        }, 200);
      }
    }, 2800);
  }

  function positionPanelOnElement(el, labelText, url, title) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    if (rect.width < 100 || rect.height < 60) return;
    if (rect.bottom < 0 || rect.top > window.innerHeight) return;

    activeMediaEl = el;
    currentTargetUrl = url || el.currentSrc || el.src || window.location.href;
    currentTargetTitle = title || el.getAttribute("alt") || el.getAttribute("title") || document.title;

    const p = getOrCreatePanel();
    const btnText = p.querySelector("#idm-dl-btn-text");
    if (btnText) {
      btnText.textContent = "Download dengan IDM Clone";
    }

    const topPos = Math.max(8, rect.top + 8);
    const rightPos = Math.max(8, window.innerWidth - rect.right + 8);

    p.style.top = `${topPos}px`;
    p.style.right = `${rightPos}px`;
    p.style.left = "auto";
    p.style.display = "block";

    requestAnimationFrame(() => {
      p.style.opacity = "1";
    });

    if (hideTimeout) clearTimeout(hideTimeout);
  }

  function openIDMDownloadDialog(url, title) {
    const existing = document.getElementById("idm-modal-container");
    if (existing) existing.remove();

    const modal = document.createElement("div");
    modal.id = "idm-modal-container";
    modal.style.cssText = `
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      background: rgba(0, 0, 0, 0.45) !important;
      z-index: 2147483647 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
      user-select: none !important;
    `;

    modal.innerHTML = `
      <div style="
        background: #ffffff !important;
        width: 480px !important;
        max-width: 90vw !important;
        border-radius: 8px !important;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.5) !important;
        overflow: hidden !important;
        border: 1px solid #c0c6cc !important;
        color: #212529 !important;
      ">
        <div style="
          background: linear-gradient(180deg, #2b78e4 0%, #1555b5 100%) !important;
          color: white !important;
          padding: 10px 16px !important;
          display: flex !important;
          justify-content: space-between !important;
          align-items: center !important;
          font-weight: bold !important;
          font-size: 14px !important;
        ">
          <span>⚡ IDM Clone - Unduh Berkas</span>
          <span id="idm-close-modal" style="cursor: pointer; font-size: 18px; line-height: 1;">&times;</span>
        </div>
        <div style="padding: 18px 20px !important; font-size: 13px !important;">
          <div style="margin-bottom: 12px !important;">
            <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #495057;">Judul / Nama Berkas:</label>
            <input type="text" id="idm-modal-title" value="${(title || "").replace(/"/g, '&quot;')}" style="
              width: 100%; box-sizing: border-box; padding: 7px 10px; border: 1px solid #ced4da; border-radius: 4px; font-size: 13px;\
            "/>
          </div>
          <div style="margin-bottom: 14px !important;">
            <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #495057;">Alamat Sumber (URL):</label>
            <input type="text" id="idm-modal-url" value="${(url || "").replace(/"/g, '&quot;')}" readonly style="
              width: 100%; box-sizing: border-box; padding: 6px 10px; border: 1px solid #e9ecef; background: #f8f9fa; border-radius: 4px; font-size: 12px; color: #6c757d;\
            "/>
          </div>
          <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 16px; font-size: 12px; color: #495057;">
            <span>⚡ Mode Akselerasi: <b>Multi-Koneksi Paralel (Maks. 32 Jalur)</b></span>
            <span style="color: #28a745; font-weight: bold;">● Kecepatan Maksimum</span>
          </div>
          <div id="idm-modal-status" style="display: none; padding: 8px 12px; border-radius: 4px; margin-bottom: 14px; font-size: 12px;"></div>
          <div style="display: flex; justify-content: flex-end; gap: 10px;">
            <button id="idm-modal-cancel-btn" style="
              padding: 7px 16px; border: 1px solid #ced4da; background: #e9ecef; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 600; color: #495057;\
            ">Batal</button>
            <button id="idm-modal-start-btn" style="
              padding: 7px 20px; border: 1px solid #1555b5; background: linear-gradient(180deg, #2b78e4 0%, #1555b5 100%); color: white; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: bold; box-shadow: 0 2px 6px rgba(0,0,0,0.2);\
            ">Mulai Unduh</button>
          </div>
        </div>
      </div>
    `;

    document.documentElement.appendChild(modal);

    const closeBtn = modal.querySelector("#idm-close-modal");
    const cancelBtn = modal.querySelector("#idm-modal-cancel-btn");
    const startBtn = modal.querySelector("#idm-modal-start-btn");
    const statusDiv = modal.querySelector("#idm-modal-status");

    function closeModal() {
      modal.remove();
    }

    closeBtn.addEventListener("click", closeModal);
    cancelBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });

    startBtn.addEventListener("click", () => {
      const finalTitle = modal.querySelector("#idm-modal-title").value.trim() || title;
      const finalUrl = modal.querySelector("#idm-modal-url").value.trim() || url;

      startBtn.disabled = true;
      startBtn.textContent = "Menghubungkan ke IDM...";

      statusDiv.style.display = "block";
      statusDiv.style.background = "#cce5ff";
      statusDiv.style.color = "#004085";
      statusDiv.textContent = "Mengirim tugas unduhan ke IDM Clone Desktop App...";

      let finished = false;
      const safetyTimer = setTimeout(() => {
        if (!finished) {
          finished = true;
          statusDiv.style.background = "#f8d7da";
          statusDiv.style.color = "#721c24";
          statusDiv.textContent = "⚠ Gagal terhubung ke port 19900. Pastikan aplikasi Desktop (run_gui.bat) sudah dibuka!";
          startBtn.disabled = false;
          startBtn.textContent = "Coba Lagi";
        }
      }, 3500);

      chrome.runtime.sendMessage(
        {
          action: "download",
          url: finalUrl,
          title: finalTitle,
          referer: window.location.href,
        },
        (resp) => {
          if (finished) return;
          finished = true;
          clearTimeout(safetyTimer);

          if (resp && resp.status === "ok") {
            statusDiv.style.background = "#d4edda";
            statusDiv.style.color = "#155724";
            statusDiv.textContent = "✔ Berhasil dikirim ke IDM Clone! Sedang diunduh di Desktop App...";
            startBtn.textContent = "✔ Terkirim!";
            setTimeout(closeModal, 1200);
          } else {
            statusDiv.style.background = "#f8d7da";
            statusDiv.style.color = "#721c24";
            const errMsg = (resp && resp.error) ? resp.error : "Pastikan run_gui.bat sudah terbuka!";
            statusDiv.textContent = `⚠ ${errMsg}`;
            startBtn.disabled = false;
            startBtn.textContent = "Coba Lagi";
          }
        }
      );
    });
  }

  function getHighestResImageUrl(imgEl) {
    if (!imgEl) return null;

    // 1. Check parent <a> link (Google Images search results or direct image links)
    const parentA = imgEl.closest("a");
    if (parentA && parentA.href) {
      // 1a. Google Images: anchor href="/imgres?imgurl=https%3A%2F%2F...&imgrefurl=..."
      if (parentA.href.includes("imgurl=")) {
        try {
          const u = new URL(parentA.href);
          const imgurl = u.searchParams.get("imgurl");
          if (imgurl && !imgurl.startsWith("data:")) {
            return decodeURIComponent(imgurl);
          }
        } catch (e) {}
      }

      // 1b. Direct full-res image link
      const href = parentA.href.toLowerCase();
      if (
        href.includes(".jpg") ||
        href.includes(".jpeg") ||
        href.includes(".png") ||
        href.includes(".webp") ||
        href.includes(".bmp") ||
        href.includes(".gif")
      ) {
        return parentA.href;
      }
    }

    // 2. Check high-res data attributes (lazy-load, zoom, galleries)
    const dataAttrs = [
      "data-original",
      "data-full-url",
      "data-full-src",
      "data-highres",
      "data-high-res",
      "data-high-res-src",
      "data-zoom-image",
      "data-zoom-src",
      "data-large-file",
      "data-large",
      "data-actualsrc",
      "data-src"
    ];
    for (const attr of dataAttrs) {
      const val = imgEl.getAttribute(attr);
      if (val && !val.startsWith("data:") && val.length > 10) {
        return val;
      }
    }

    // 3. Check srcset for maximum resolution candidate
    const srcset = imgEl.getAttribute("srcset");
    if (srcset) {
      try {
        const candidates = srcset.split(",").map((s) => s.trim()).filter(Boolean);
        let bestUrl = null;
        let maxVal = -1;
        for (const cand of candidates) {
          const parts = cand.split(/\s+/);
          const url = parts[0];
          let val = 1;
          if (parts[1]) {
            if (parts[1].endsWith("w")) {
              val = parseInt(parts[1], 10) || 1;
            } else if (parts[1].endsWith("x")) {
              val = (parseFloat(parts[1]) || 1) * 1000;
            }
          }
          if (val > maxVal) {
            maxVal = val;
            bestUrl = url;
          }
        }
        if (bestUrl && !bestUrl.startsWith("data:")) {
          return bestUrl;
        }
      } catch (err) {}
    }

    // 4. Default to currentSrc or src
    let src = imgEl.currentSrc || imgEl.src;
    if (!src || src.startsWith("data:")) return null;

    // 5. Platform-specific CDN upgrades to get original full resolution
    try {
      const u = new URL(src);

      // Twitter / X: replace name=small/medium/900x900 with name=orig
      if (u.hostname.includes("twimg.com") && u.searchParams.has("name")) {
        u.searchParams.set("name", "orig");
        return u.href;
      }

      // Pinterest: replace /236x/ or /474x/ or /736x/ with /originals/
      if (u.hostname.includes("pinimg.com")) {
        const pMatch = u.pathname.match(/\/\d+x\//);
        if (pMatch) {
          u.pathname = u.pathname.replace(pMatch[0], "/originals/");
          return u.href;
        }
      }

      // Reddit: replace preview.redd.it with i.redd.it and strip query params
      if (u.hostname.includes("preview.redd.it") || u.hostname.includes("external-preview.redd.it")) {
        u.hostname = "i.redd.it";
        u.search = "";
        return u.href;
      }

      // Wikimedia / Wikipedia: strip /thumb/ and thumbnail filename
      if (u.hostname.includes("upload.wikimedia.org") && u.pathname.includes("/thumb/")) {
        const parts = u.pathname.split("/");
        const thumbIdx = parts.indexOf("thumb");
        if (thumbIdx !== -1) {
          parts.splice(thumbIdx, 1);
          parts.pop();
          u.pathname = parts.join("/");
          return u.href;
        }
      }

      // Unsplash: remove &w=... and &h=... limits, keep full quality
      if (u.hostname.includes("images.unsplash.com")) {
        u.searchParams.delete("w");
        u.searchParams.delete("h");
        u.searchParams.set("q", "100");
        return u.href;
      }

      // WordPress / Jetpack: remove resize query params
      if (u.searchParams.has("resize") || u.searchParams.has("w")) {
        u.searchParams.delete("resize");
        u.searchParams.delete("w");
        u.searchParams.delete("h");
        return u.href;
      }

      // WordPress thumbnail suffix in path (e.g. image-300x200.jpg -> image.jpg)
      const wpThumbMatch = u.pathname.match(/^(.+)-\d+x\d+(\.[a-zA-Z0-9]+)$/);
      if (wpThumbMatch) {
        u.pathname = wpThumbMatch[1] + wpThumbMatch[2];
        return u.href;
      }

      // Google / Blogspot (e.g. /s320/ or /w400-h300/ -> /s0/ for original)
      const gMatch = u.pathname.match(/\/(s\d+|w\d+-h\d+)(-c)?\//);
      if (gMatch && (u.hostname.includes("googleusercontent.com") || u.hostname.includes("ggpht.com") || u.hostname.includes("blogger.com"))) {
        u.pathname = u.pathname.replace(gMatch[0], "/s0/");
        return u.href;
      }
    } catch (e) {}

    return src;
  }

  // 1. Mouseover listener: attach panel to media/player on hover (IDM behavior)
  document.addEventListener(
    "mouseover",
    (e) => {
      const el = e.target;
      if (!el) return;

      // Special handling for YouTube (videos are MSE blob: streams, use page URL for yt-dlp)
      if (window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be")) {
        if (el.tagName === "VIDEO" || (el.closest && el.closest("#movie_player, .html5-video-player"))) {
          const player = el.closest("#movie_player, .html5-video-player") || el;
          positionPanelOnElement(player, "Download dengan IDM Clone", window.location.href, document.title);
          return;
        }
      }

      if (el.tagName === "VIDEO") {
        positionPanelOnElement(el, "Download dengan IDM Clone", el.currentSrc || el.src, document.title);
      } else if (el.closest && el.closest("#movie_player, .html5-video-player")) {
        const player = el.closest("#movie_player, .html5-video-player");
        const video = player.querySelector("video");
        if (video) {
          positionPanelOnElement(player, "Download dengan IDM Clone", window.location.href, document.title);
        }
      } else if (el.tagName === "AUDIO") {
        positionPanelOnElement(el, "Download dengan IDM Clone", el.currentSrc || el.src, document.title);
      } else if (el.tagName === "IMG") {
        const rect = el.getBoundingClientRect();
        if (rect.width >= 160 && rect.height >= 120) {
          const imgSrc = getHighestResImageUrl(el);
          if (imgSrc) {
            let imgTitle = (el.alt || el.title || "").trim();
            if (!imgTitle || imgTitle.length < 3) {
              try {
                const u = new URL(imgSrc);
                const pathPart = u.pathname.split("/").filter(Boolean).pop();
                if (pathPart) imgTitle = decodeURIComponent(pathPart.split("?")[0]);
              } catch (err) {}
            }
            if (!imgTitle) imgTitle = "gambar";
            positionPanelOnElement(el, "Download dengan IDM Clone", imgSrc, imgTitle);
          }
        }
      }
    },
    true
  );

  document.addEventListener(
    "mouseout",
    (e) => {
      const el = e.target;
      if (
        el &&
        (el.tagName === "VIDEO" ||
          el.tagName === "AUDIO" ||
          el.tagName === "IMG" ||
          (el.closest && el.closest("#movie_player, .html5-video-player")))
      ) {
        scheduleHide();
      }
    },
    true
  );

  // 2. Event listener when media starts playing
  document.addEventListener(
    "play",
    (e) => {
      const el = e.target;
      if (el && el.tagName === "VIDEO") {
        const targetUrl = (window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be"))
          ? window.location.href
          : (el.currentSrc || el.src);
        positionPanelOnElement(el, "Download dengan IDM Clone", targetUrl, document.title);
        scheduleHide();
      } else if (el && el.tagName === "AUDIO") {
        positionPanelOnElement(el, "Download dengan IDM Clone", el.currentSrc || el.src, document.title);
        scheduleHide();
      }
    },
    true
  );

  // 3. Listener from background network sniffer (HLS/MP4 streams detected)
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "media_detected" && msg.url) {
      const v = document.querySelector("video");
      if (v && v.getBoundingClientRect().width > 120) {
        positionPanelOnElement(v, "Download dengan IDM Clone", msg.url, document.title);
        scheduleHide();
      }
      sendResponse({ status: "ok" });
    }
  });
})();
