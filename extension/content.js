// JustPressDownload (JPD) Content Script - Smart Corner-Persisted Draggable Download Panel
(function () {
  "use strict";

  if (window.__idm_clone_active) return;
  window.__idm_clone_active = true;

  let panel = null;
  let activeMediaEl = null;
  let currentTargetUrl = null;
  let currentTargetTitle = "";
  let hideTimeout = null;

  // Corner persistence: "top-right" | "top-left" | "bottom-left" | "bottom-right"
  let preferredCorner = "top-right";
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let panelStartLeft = 0;
  let panelStartTop = 0;
  let hasMoved = false;

  // Load saved corner preference from storage
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ jpd_panel_corner: "top-right" }, (items) => {
      if (items && items.jpd_panel_corner) {
        preferredCorner = items.jpd_panel_corner;
      }
    });
  }

  function getClosestCorner(pRect, mRect) {
    const pMidX = pRect.left + pRect.width / 2;
    const pMidY = pRect.top + pRect.height / 2;
    const mMidX = mRect.left + mRect.width / 2;
    const mMidY = mRect.top + mRect.height / 2;

    const isTop = pMidY < mMidY;
    const isLeft = pMidX < mMidX;

    if (isTop && !isLeft) return "top-right";
    if (isTop && isLeft) return "top-left";
    if (!isTop && isLeft) return "bottom-left";
    return "bottom-right";
  }

  function cornerToLabel(corner) {
    switch (corner) {
      case "top-left": return "Kiri Atas";
      case "bottom-left": return "Kiri Bawah";
      case "bottom-right": return "Kanan Bawah";
      case "top-right":
      default: return "Kanan Atas";
    }
  }

  function applyCornerPosition(p, rect, corner) {
    const margin = 10;
    p.style.left = "auto";
    p.style.right = "auto";
    p.style.top = "auto";
    p.style.bottom = "auto";

    switch (corner) {
      case "top-left":
        p.style.top = `${Math.max(8, rect.top + margin)}px`;
        p.style.left = `${Math.max(8, rect.left + margin)}px`;
        break;
      case "bottom-left":
        p.style.bottom = `${Math.max(8, window.innerHeight - rect.bottom + margin)}px`;
        p.style.left = `${Math.max(8, rect.left + margin)}px`;
        break;
      case "bottom-right":
        p.style.bottom = `${Math.max(8, window.innerHeight - rect.bottom + margin)}px`;
        p.style.right = `${Math.max(8, window.innerWidth - rect.right + margin)}px`;
        break;
      case "top-right":
      default:
        p.style.top = `${Math.max(8, rect.top + margin)}px`;
        p.style.right = `${Math.max(8, window.innerWidth - rect.right + margin)}px`;
        break;
    }
  }

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
      <div id="jpd-panel-container" style="
        display: inline-flex !important;
        align-items: center !important;
        background: rgba(15, 19, 29, 0.94) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 6px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(8px) !important;
        overflow: hidden !important;
      ">
        <div id="jpd-drag-handle" title="Tahan dan geser untuk memindahkan posisi tombol (Kanan Atas, Kiri Atas, Kiri Bawah, Kanan Bawah)" style="
          display: inline-flex !important;
          align-items: center !important;
          justify-content: center !important;
          padding: 6px 6px !important;
          background: rgba(255, 255, 255, 0.06) !important;
          cursor: grab !important;
          color: #94a3b8 !important;
          border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        ">
          <svg width="10" height="12" viewBox="0 0 10 12" fill="currentColor">
            <circle cx="2.5" cy="2" r="1.2"/>
            <circle cx="7.5" cy="2" r="1.2"/>
            <circle cx="2.5" cy="6" r="1.2"/>
            <circle cx="7.5" cy="6" r="1.2"/>
            <circle cx="2.5" cy="10" r="1.2"/>
            <circle cx="7.5" cy="10" r="1.2"/>
          </svg>
        </div>
        <div id="idm-dl-action-btn" style="
          display: inline-flex !important;
          align-items: center !important;
          gap: 6px !important;
          background: #2563eb !important;
          color: #ffffff !important;
          padding: 5px 11px !important;
          cursor: pointer !important;
          font-size: 11px !important;
          font-weight: 600 !important;
          line-height: 1.2 !important;
        ">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span id="idm-dl-btn-text">Download dengan JustPressDownload</span>
        </div>
      </div>
      <div id="jpd-pos-toast" style="
        display: none;
        margin-top: 4px;
        background: #0f131d;
        color: #60a5fa;
        font-size: 10px;
        font-weight: bold;
        text-align: center;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #2563eb;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
      "></div>
    `;

    panel.addEventListener("mouseenter", () => {
      if (hideTimeout) clearTimeout(hideTimeout);
    });

    panel.addEventListener("mouseleave", () => {
      if (!isDragging) scheduleHide();
    });

    const dragHandle = panel.querySelector("#jpd-drag-handle");
    const posToast = panel.querySelector("#jpd-pos-toast");

    dragHandle.addEventListener("mousedown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      isDragging = true;
      hasMoved = false;
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      const rect = panel.getBoundingClientRect();
      panelStartLeft = rect.left;
      panelStartTop = rect.top;

      dragHandle.style.cursor = "grabbing";
      panel.style.transition = "none";
      if (hideTimeout) clearTimeout(hideTimeout);
    });

    document.addEventListener("mousemove", (e) => {
      if (!isDragging || !panel) return;
      hasMoved = true;
      const dx = e.clientX - dragStartX;
      const dy = e.clientY - dragStartY;

      panel.style.left = `${panelStartLeft + dx}px`;
      panel.style.top = `${panelStartTop + dy}px`;
      panel.style.right = "auto";
      panel.style.bottom = "auto";

      if (activeMediaEl) {
        const pRect = panel.getBoundingClientRect();
        const mRect = activeMediaEl.getBoundingClientRect();
        const hoveredCorner = getClosestCorner(pRect, mRect);
        if (posToast) {
          posToast.style.display = "block";
          posToast.textContent = `Arahkan ke: ${cornerToLabel(hoveredCorner)}`;
        }
      }
    });

    document.addEventListener("mouseup", (e) => {
      if (!isDragging || !panel) return;
      isDragging = false;
      dragHandle.style.cursor = "grab";
      panel.style.transition = "opacity 0.2s ease, top 0.2s ease, left 0.2s ease, right 0.2s ease, bottom 0.2s ease";

      if (hasMoved && activeMediaEl) {
        const pRect = panel.getBoundingClientRect();
        const mRect = activeMediaEl.getBoundingClientRect();
        preferredCorner = getClosestCorner(pRect, mRect);

        // Persist preference to chrome.storage.local
        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          chrome.storage.local.set({ jpd_panel_corner: preferredCorner });
        }

        // Snap smoothly to chosen corner
        applyCornerPosition(panel, mRect, preferredCorner);

        // Show brief confirmation toast
        if (posToast) {
          posToast.style.display = "block";
          posToast.textContent = `✔ Posisi disimpan: ${cornerToLabel(preferredCorner)}`;
          setTimeout(() => {
            if (posToast) posToast.style.display = "none";
          }, 1800);
        }
      }
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
      btnText.textContent = labelText || "Download dengan JustPressDownload";
    }

    if (!isDragging) {
      applyCornerPosition(p, rect, preferredCorner);
    }
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
          <span>⚡ JustPressDownload (JPD) - Unduh Berkas</span>
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
      startBtn.textContent = "Menghubungkan ke JustPressDownload...";

      statusDiv.style.display = "block";
      statusDiv.style.background = "#cce5ff";
      statusDiv.style.color = "#004085";
      statusDiv.textContent = "Mengirim tugas unduhan ke JustPressDownload (JPD)...";

      let finished = false;
      const safetyTimer = setTimeout(() => {
        if (!finished) {
          finished = true;
          statusDiv.style.background = "#f8d7da";
          statusDiv.style.color = "#721c24";
          statusDiv.textContent = "⚠ Gagal terhubung ke port 19900. Pastikan aplikasi Desktop (JustPressDownload.exe) sudah dibuka!";
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
            statusDiv.textContent = "✔ Berhasil dikirim ke JustPressDownload (JPD)! Sedang diunduh di Desktop App...";
            startBtn.textContent = "✔ Terkirim!";
            setTimeout(closeModal, 1200);
          } else {
            statusDiv.style.background = "#f8d7da";
            statusDiv.style.color = "#721c24";
            const errMsg = (resp && resp.error) ? resp.error : "Pastikan JustPressDownload.exe sudah dibuka!";
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
          positionPanelOnElement(player, "Download dengan JustPressDownload", window.location.href, document.title);
          return;
        }
      }

      if (el.tagName === "VIDEO") {
        positionPanelOnElement(el, "Download dengan JustPressDownload", el.currentSrc || el.src, document.title);
      } else if (el.closest && el.closest("#movie_player, .html5-video-player")) {
        const player = el.closest("#movie_player, .html5-video-player");
        const video = player.querySelector("video");
        if (video) {
          positionPanelOnElement(player, "Download dengan JustPressDownload", window.location.href, document.title);
        }
      } else if (el.tagName === "AUDIO") {
        positionPanelOnElement(el, "Download dengan JustPressDownload", el.currentSrc || el.src, document.title);
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
            positionPanelOnElement(el, "Download dengan JustPressDownload", imgSrc, imgTitle);
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
        positionPanelOnElement(el, "Download dengan JustPressDownload", targetUrl, document.title);
        scheduleHide();
      } else if (el && el.tagName === "AUDIO") {
        positionPanelOnElement(el, "Download dengan JustPressDownload", el.currentSrc || el.src, document.title);
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
        positionPanelOnElement(v, "Download dengan JustPressDownload", msg.url, document.title);
        scheduleHide();
      }
      sendResponse({ status: "ok" });
    }
  });
})();
