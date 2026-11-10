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

  // Position persistence: free-form relative coordinates { relX, relY } + fallback corner
  // Synchronously initialize preferredPos & preferredCorner from localStorage to prevent any 1ms default flash
  let preferredPos = { relX: 1.0, relY: 0.0 };
  let preferredCorner = "top-right";
  let currentLang = "id";

  // Exclusion & Blacklist State
  let blockedDomains = [];
  let blockedPages = [];

  function cleanUrlForCompare(rawUrl) {
    if (!rawUrl) return "";
    try {
      const u = new URL(rawUrl);
      return u.origin + u.pathname;
    } catch (e) {
      return rawUrl.split("#")[0].split("?")[0];
    }
  }

  function isSiteOrPageBlocked() {
    // 1. Per-tab session dismissal via sessionStorage
    try {
      if (sessionStorage.getItem("jpd_session_dismissed") === "true") {
        return true;
      }
    } catch (e) {}

    const host = window.location.hostname.toLowerCase();
    const currentClean = cleanUrlForCompare(window.location.href).toLowerCase();

    // 2. Check domain blacklist
    if (blockedDomains && blockedDomains.length > 0) {
      for (let d of blockedDomains) {
        if (!d) continue;
        const dom = d.toLowerCase().trim();
        if (host === dom || host.endsWith("." + dom)) {
          return true;
        }
      }
    }

    // 3. Check page blacklist
    if (blockedPages && blockedPages.length > 0) {
      for (let p of blockedPages) {
        if (!p) continue;
        if (currentClean === cleanUrlForCompare(p).toLowerCase()) {
          return true;
        }
      }
    }

    return false;
  }

  try {
    const cachedDomains = localStorage.getItem("jpd_blacklist_domains");
    if (cachedDomains) blockedDomains = JSON.parse(cachedDomains);
  } catch (e) {}
  try {
    const cachedPages = localStorage.getItem("jpd_blacklist_pages");
    if (cachedPages) blockedPages = JSON.parse(cachedPages);
  } catch (e) {}

  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["jpd_blacklist_domains", "jpd_blacklist_pages"], (res) => {
      if (res && res.jpd_blacklist_domains) {
        blockedDomains = res.jpd_blacklist_domains;
        try { localStorage.setItem("jpd_blacklist_domains", JSON.stringify(blockedDomains)); } catch (e) {}
      }
      if (res && res.jpd_blacklist_pages) {
        blockedPages = res.jpd_blacklist_pages;
        try { localStorage.setItem("jpd_blacklist_pages", JSON.stringify(blockedPages)); } catch (e) {}
      }
    });
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === "local") {
        if (changes.jpd_blacklist_domains) {
          blockedDomains = changes.jpd_blacklist_domains.newValue || [];
          try { localStorage.setItem("jpd_blacklist_domains", JSON.stringify(blockedDomains)); } catch (e) {}
        }
        if (changes.jpd_blacklist_pages) {
          blockedPages = changes.jpd_blacklist_pages.newValue || [];
          try { localStorage.setItem("jpd_blacklist_pages", JSON.stringify(blockedPages)); } catch (e) {}
        }
        if (changes.jpd_language) {
          currentLang = changes.jpd_language.newValue || "id";
          try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
          updatePanelTexts();
        }
      }
    });
  }

  // Live Unblock & Re-appearance Message Listener from Popup
  if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg && msg.action === "jpd_unblock_and_show") {
        try {
          sessionStorage.removeItem("jpd_session_dismissed");
        } catch (e) {}

        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          chrome.storage.local.get(["jpd_blacklist_domains", "jpd_blacklist_pages"], (res) => {
            if (res && res.jpd_blacklist_domains) blockedDomains = res.jpd_blacklist_domains;
            if (res && res.jpd_blacklist_pages) blockedPages = res.jpd_blacklist_pages;
            checkShortsAndVideos();
          });
        } else {
          checkShortsAndVideos();
        }
        if (sendResponse) sendResponse({ status: "ok" });
      }

      if (msg && msg.action === "jpd_set_language" && msg.language) {
        currentLang = msg.language;
        try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
        updatePanelTexts();
        if (sendResponse) sendResponse({ status: "ok" });
      }
    });
  }

  try {
    const cachedLang = localStorage.getItem("jpd_language");
    if (cachedLang) currentLang = cachedLang;
  } catch (e) {}

  const STRINGS = {
    id: {
      btn_download: "Download dengan JPD",
      toast_dragging: "Lepas untuk menyimpan posisi",
      toast_saved: "✔ Posisi tombol disimpan",
      drag_tooltip: "Tahan dan geser untuk memindahkan posisi tombol secara bebas ke mana saja",
      sending: "✔ Mengirim ke JPD...",
      error: "✕ Gagal membuka JPD",
      dismiss_title: "Opsi Sembunyikan Tombol",
      dismiss_session: "Sembunyikan kali ini saja",
      dismiss_page: "Jangan tampilkan di halaman ini",
      dismiss_domain: "Jangan tampilkan di seluruh website",
      toast_dismissed_session: "✔ Tombol disembunyikan untuk sesi ini",
      toast_dismissed_page: "✔ Tombol dinonaktifkan di halaman ini",
      toast_dismissed_domain: "✔ Tombol dinonaktifkan untuk "
    },
    en: {
      btn_download: "Download with JPD",
      toast_dragging: "Release to save position",
      toast_saved: "✔ Button position saved",
      drag_tooltip: "Click and drag to move download button freely anywhere",
      sending: "✔ Sending to JPD...",
      error: "✕ Failed to open JPD",
      dismiss_title: "Hide Button Options",
      dismiss_session: "Hide for this session",
      dismiss_page: "Never show on this page",
      dismiss_domain: "Never show on this website",
      toast_dismissed_session: "✔ Button hidden for this session",
      toast_dismissed_page: "✔ Button disabled on this page",
      toast_dismissed_domain: "✔ Button disabled for "
    }
  };

  function tr(key) {
    const tbl = STRINGS[currentLang] || STRINGS.id;
    return tbl[key] || STRINGS.id[key] || key;
  }

  function updatePanelTexts() {
    if (!panel) return;
    const btnText = panel.querySelector("#idm-dl-btn-text");
    if (btnText) {
      btnText.textContent = tr("btn_download");
    }
    const dragHandle = panel.querySelector("#jpd-drag-handle");
    if (dragHandle) dragHandle.title = tr("drag_tooltip");
    const closeBtn = panel.querySelector("#jpd-close-btn");
    if (closeBtn) closeBtn.title = tr("dismiss_title");

    const popHeader = panel.querySelector("#jpd-popover-header-title");
    if (popHeader) popHeader.textContent = tr("dismiss_title");

    const optSession = panel.querySelector("#jpd-opt-session span:last-child");
    if (optSession) optSession.textContent = tr("dismiss_session");

    const optPage = panel.querySelector("#jpd-opt-page span:last-child");
    if (optPage) optPage.textContent = tr("dismiss_page");

    const optDomain = panel.querySelector("#jpd-opt-domain span:last-child");
    if (optDomain) {
      const h = window.location.hostname;
      optDomain.textContent = tr("dismiss_domain") + (h ? ` (${h})` : "");
    }

    const btnId = panel.querySelector("#jpd-popover-lang-id");
    const btnEn = panel.querySelector("#jpd-popover-lang-en");
    if (btnId) btnId.style.background = currentLang === "id" ? "#2563eb" : "rgba(255,255,255,0.08)";
    if (btnEn) btnEn.style.background = currentLang === "en" ? "#2563eb" : "rgba(255,255,255,0.08)";
  }

  function cornerToPos(corner) {
    switch (corner) {
      case "top-left": return { relX: 0.0, relY: 0.0 };
      case "bottom-left": return { relX: 0.0, relY: 1.0 };
      case "bottom-right": return { relX: 1.0, relY: 1.0 };
      case "top-right":
      default: return { relX: 1.0, relY: 0.0 };
    }
  }

  try {
    const cachedPos = localStorage.getItem("jpd_panel_position");
    if (cachedPos) {
      const parsed = JSON.parse(cachedPos);
      if (parsed && typeof parsed.relX === "number" && typeof parsed.relY === "number") {
        preferredPos = parsed;
      }
    } else {
      const cachedCorner = localStorage.getItem("jpd_panel_corner");
      if (cachedCorner) {
        preferredCorner = cachedCorner;
        preferredPos = cornerToPos(cachedCorner);
      }
    }
  } catch (e) {}

  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let panelStartLeft = 0;
  let panelStartTop = 0;
  let hasMoved = false;

  // Asynchronously sync across browser tabs/domains via chrome.storage.local
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ jpd_panel_position: null, jpd_panel_corner: preferredCorner, jpd_language: currentLang }, (items) => {
      if (items && items.jpd_language) {
        currentLang = items.jpd_language;
        try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
      }
      if (items && items.jpd_panel_position) {
        preferredPos = items.jpd_panel_position;
        try {
          localStorage.setItem("jpd_panel_position", JSON.stringify(preferredPos));
        } catch (e) {}
      } else if (items && items.jpd_panel_corner) {
        preferredCorner = items.jpd_panel_corner;
        preferredPos = cornerToPos(preferredCorner);
        try {
          localStorage.setItem("jpd_panel_corner", preferredCorner);
        } catch (e) {}
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

  function applyPanelPosition(p, rect, pos) {
    const pWidth = p.offsetWidth || 160;
    const pHeight = p.offsetHeight || 34;
    const margin = 10;

    const minLeft = rect.left + margin;
    const maxLeft = rect.left + rect.width - pWidth - margin;
    const minTop = rect.top + margin;
    const maxTop = rect.top + rect.height - pHeight - margin;

    let targetLeft;
    let targetTop;

    const effectivePos = (pos && typeof pos.relX === "number") ? pos : preferredPos;

    if (maxLeft >= minLeft) {
      targetLeft = minLeft + effectivePos.relX * (maxLeft - minLeft);
    } else {
      targetLeft = rect.left + margin;
    }

    if (maxTop >= minTop) {
      targetTop = minTop + effectivePos.relY * (maxTop - minTop);
    } else {
      targetTop = rect.top + margin;
    }

    const viewportLeft = Math.max(8, Math.min(window.innerWidth - pWidth - 8, targetLeft));
    const viewportTop = Math.max(8, Math.min(window.innerHeight - pHeight - 8, targetTop));

    p.style.left = `${Math.round(viewportLeft)}px`;
    p.style.top = `${Math.round(viewportTop)}px`;
    p.style.right = "auto";
    p.style.bottom = "auto";
  }

  function applyCornerPosition(p, rect, corner) {
    if (corner && typeof corner === "object" && typeof corner.relX === "number") {
      applyPanelPosition(p, rect, corner);
      return;
    }
    if (corner && typeof corner === "string") {
      applyPanelPosition(p, rect, cornerToPos(corner));
      return;
    }
    applyPanelPosition(p, rect, preferredPos);
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
        <div id="jpd-drag-handle" title="${tr("drag_tooltip")}" style="
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
          <span id="idm-dl-btn-text">${tr("btn_download")}</span>
        </div>
        <div id="jpd-close-btn" class="jpd-close-btn" title="${tr("dismiss_title")}" style="
          display: inline-flex !important;
          align-items: center !important;
          justify-content: center !important;
          padding: 6px 7px !important;
          background: rgba(255, 255, 255, 0.08) !important;
          cursor: pointer !important;
          color: #cbd5e1 !important;
          border-left: 1px solid rgba(255, 255, 255, 0.12) !important;
          transition: background 0.15s ease, color 0.15s ease !important;
        ">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </div>
      </div>
      <div id="jpd-dismiss-popover" class="jpd-dismiss-popover" style="
        display: none;
        position: absolute !important;
        top: calc(100% + 6px) !important;
        right: 0 !important;
        min-width: 220px !important;
        background: #0f131d !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        padding: 5px !important;
        z-index: 2147483647 !important;
        font-size: 11px !important;
      ">
        <div id="jpd-popover-header-title" style="padding: 4px 8px 6px; font-weight: 700; color: #94a3b8; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 4px;">
          ${tr("dismiss_title")}
        </div>
        <div id="jpd-opt-session" class="jpd-popover-item" style="
          display: flex !important;
          align-items: center !important;
          gap: 7px !important;
          padding: 6px 8px !important;
          color: #f1f5f9 !important;
          border-radius: 5px !important;
          cursor: pointer !important;
          transition: background 0.15s ease !important;
        ">
          <span style="color: #38bdf8;">⏳</span>
          <span>${tr("dismiss_session")}</span>
        </div>
        <div id="jpd-opt-page" class="jpd-popover-item" style="
          display: flex !important;
          align-items: center !important;
          gap: 7px !important;
          padding: 6px 8px !important;
          color: #f1f5f9 !important;
          border-radius: 5px !important;
          cursor: pointer !important;
          transition: background 0.15s ease !important;
        ">
          <span style="color: #f59e0b;">📄</span>
          <span>${tr("dismiss_page")}</span>
        </div>
        <div id="jpd-opt-domain" class="jpd-popover-item" style="
          display: flex !important;
          align-items: center !important;
          gap: 7px !important;
          padding: 6px 8px !important;
          color: #f1f5f9 !important;
          border-radius: 5px !important;
          cursor: pointer !important;
          transition: background 0.15s ease !important;
        ">
          <span style="color: #ef4444;">🌐</span>
          <span>${tr("dismiss_domain")}</span>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 8px 3px; border-top: 1px solid rgba(255,255,255,0.08); margin-top: 5px;">
          <span style="font-size: 10px; color: #94a3b8; font-weight: 600;">🌐 Bahasa / Lang:</span>
          <div style="display: inline-flex; gap: 4px;">
            <button type="button" id="jpd-popover-lang-id" class="jpd-popover-lang-btn" style="background: ${currentLang === 'id' ? '#2563eb' : 'rgba(255,255,255,0.08)'}; color: #ffffff; border: none; border-radius: 4px; padding: 2px 7px; font-size: 9px; font-weight: bold; cursor: pointer;">ID 🇮🇩</button>
            <button type="button" id="jpd-popover-lang-en" class="jpd-popover-lang-btn" style="background: ${currentLang === 'en' ? '#2563eb' : 'rgba(255,255,255,0.08)'}; color: #ffffff; border: none; border-radius: 4px; padding: 2px 7px; font-size: 9px; font-weight: bold; cursor: pointer;">EN 🇬🇧</button>
          </div>
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

      if (posToast) {
        posToast.style.display = "block";
        posToast.textContent = tr("toast_dragging");
      }
    });

    document.addEventListener("mouseup", (e) => {
      if (!isDragging || !panel) return;
      isDragging = false;
      dragHandle.style.cursor = "grab";
      panel.style.transition = "none";

      if (hasMoved && activeMediaEl) {
        const pRect = panel.getBoundingClientRect();
        const mRect = activeMediaEl.getBoundingClientRect();
        const margin = 10;
        const minLeft = mRect.left + margin;
        const maxLeft = mRect.left + mRect.width - pRect.width - margin;
        const minTop = mRect.top + margin;
        const maxTop = mRect.top + mRect.height - pRect.height - margin;

        let relX = 1.0;
        if (maxLeft > minLeft) {
          relX = (pRect.left - minLeft) / (maxLeft - minLeft);
        }
        relX = Math.max(0, Math.min(1, relX));

        let relY = 0.0;
        if (maxTop > minTop) {
          relY = (pRect.top - minTop) / (maxTop - minTop);
        }
        relY = Math.max(0, Math.min(1, relY));

        preferredPos = {
          relX: Math.round(relX * 1000) / 1000,
          relY: Math.round(relY * 1000) / 1000
        };
        preferredCorner = getClosestCorner(pRect, mRect);

        // Instantly save to synchronous localStorage and sync to chrome.storage.local
        try {
          localStorage.setItem("jpd_panel_position", JSON.stringify(preferredPos));
          localStorage.setItem("jpd_panel_corner", preferredCorner);
        } catch (e) {}
        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          chrome.storage.local.set({
            jpd_panel_position: preferredPos,
            jpd_panel_corner: preferredCorner
          });
        }

        // Apply chosen position exactly where dropped (free-form placement anywhere)
        applyPanelPosition(panel, mRect, preferredPos);

        // Show brief confirmation toast
        if (posToast) {
          posToast.style.display = "block";
          posToast.textContent = tr("toast_saved");
          setTimeout(() => {
            if (posToast) posToast.style.display = "none";
          }, 1500);
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

      // If on TikTok Web, resolve the exact permalink using video ID from DOM container
      if (window.location.hostname.includes("tiktok.com")) {
        const video = activeMediaEl ? (activeMediaEl.tagName === "VIDEO" ? activeMediaEl : activeMediaEl.querySelector("video")) : document.querySelector("video");
        const container = video ? (video.closest('section, article, [data-e2e*="item"], div[class*="DivItemContainer"], [data-e2e="feed-video"]') || video.parentElement) : null;
        if (video) {
          const resolved = getTikTokVideoUrl(video, container);
          if (resolved && !resolved.startsWith("blob:") && resolved !== "https://www.tiktok.com/" && resolved !== "https://www.tiktok.com/foryou") {
            targetUrl = resolved;
          }
          if (container) {
            targetTitle = getTikTokVideoTitle(container) || targetTitle;
          }
        }
      }

      if (!targetUrl || targetUrl.startsWith("blob:")) {
        if (activeMediaEl) {
          targetUrl = activeMediaEl.currentSrc || activeMediaEl.src;
        } else {
          targetUrl = window.location.href;
        }
      }

      // Visual feedback on the floating button (Green flash: Sent!)
      const oldBg = btn.style.background;
      btn.style.background = "#10b981";
      const btnSpan = btn.querySelector("#idm-dl-btn-text");
      const oldText = btnSpan ? btnSpan.textContent : tr("btn_download");
      if (btnSpan) btnSpan.textContent = tr("sending");

      // Directly dispatch download task to Just Press Download desktop app (NO double popups!)
      chrome.runtime.sendMessage(
        {
          action: "download",
          url: targetUrl,
          title: targetTitle,
          referer: window.location.href,
        },
        (resp) => {
          if (resp && resp.action === "launch_protocol" && resp.uri) {
            const a = document.createElement("a");
            a.href = resp.uri;
            a.style.display = "none";
            document.body.appendChild(a);
            a.click();
            setTimeout(() => a.remove(), 1000);
          }
          if (resp && resp.status === "error") {
            btn.style.background = "#ef4444";
            if (btnSpan) btnSpan.textContent = tr("error");
          }
          setTimeout(() => {
            btn.style.background = oldBg || "#2563eb";
            if (btnSpan) btnSpan.textContent = oldText;
          }, 1500);
        }
      );
    });

    const closeBtn = panel.querySelector("#jpd-close-btn");
    const dismissPopover = panel.querySelector("#jpd-dismiss-popover");

    function showToast(msg) {
      let t = document.getElementById("jpd-toast-pill");
      if (!t) {
        t = document.createElement("div");
        t.id = "jpd-toast-pill";
        t.className = "jpd-toast-pill";
        t.style.cssText = `
          position: fixed !important;
          bottom: 24px !important;
          right: 24px !important;
          z-index: 2147483647 !important;
          background: rgba(15, 19, 29, 0.95) !important;
          color: #f1f5f9 !important;
          border: 1px solid #2563eb !important;
          border-radius: 8px !important;
          padding: 8px 14px !important;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
          font-size: 11px !important;
          font-weight: 600 !important;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
          backdrop-filter: blur(8px) !important;
          pointer-events: none !important;
          transition: opacity 0.25s ease !important;
          opacity: 0;
        `;
        document.documentElement.appendChild(t);
      }
      t.textContent = msg;
      t.style.display = "block";
      requestAnimationFrame(() => {
        t.style.opacity = "1";
      });
      setTimeout(() => {
        t.style.opacity = "0";
        setTimeout(() => {
          if (t && t.parentNode) t.parentNode.removeChild(t);
        }, 250);
      }, 1500);
    }

    function dismissWithAnimation(toastMessage) {
      if (dismissPopover) dismissPopover.style.display = "none";
      if (panel) {
        panel.style.transition = "opacity 0.22s ease";
        panel.style.opacity = "0";
        setTimeout(() => {
          panel.style.display = "none";
        }, 230);
      }
      if (toastMessage) {
        showToast(toastMessage);
      }
    }

    if (closeBtn && dismissPopover) {
      closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();
        const isOpen = dismissPopover.style.display === "block";
        dismissPopover.style.display = isOpen ? "none" : "block";
      });

      // Hover styles on close button
      closeBtn.addEventListener("mouseenter", () => {
        closeBtn.style.background = "rgba(239, 68, 68, 0.25)";
        closeBtn.style.color = "#f87171";
      });
      closeBtn.addEventListener("mouseleave", () => {
        closeBtn.style.background = "rgba(255, 255, 255, 0.08)";
        closeBtn.style.color = "#cbd5e1";
      });

      // Option 1: Sembunyikan kali ini saja (Session per-tab)
      const optSession = panel.querySelector("#jpd-opt-session");
      if (optSession) {
        optSession.addEventListener("click", (e) => {
          e.stopPropagation();
          e.preventDefault();
          try {
            sessionStorage.setItem("jpd_session_dismissed", "true");
          } catch (err) {}
          dismissWithAnimation(tr("toast_dismissed_session"));
        });
        optSession.addEventListener("mouseenter", () => { optSession.style.background = "rgba(56, 189, 248, 0.15)"; });
        optSession.addEventListener("mouseleave", () => { optSession.style.background = "transparent"; });
      }

      // Option 2: Jangan tampilkan di halaman ini (Page URL)
      const optPage = panel.querySelector("#jpd-opt-page");
      if (optPage) {
        optPage.addEventListener("click", (e) => {
          e.stopPropagation();
          e.preventDefault();
          const cleanUrl = cleanUrlForCompare(window.location.href);
          if (!blockedPages.includes(cleanUrl)) {
            blockedPages.push(cleanUrl);
            try { localStorage.setItem("jpd_blacklist_pages", JSON.stringify(blockedPages)); } catch (err) {}
            if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
              chrome.storage.local.set({ jpd_blacklist_pages: blockedPages });
            }
          }
          try {
            sessionStorage.setItem("jpd_session_dismissed", "true");
          } catch (err) {}
          dismissWithAnimation(tr("toast_dismissed_page"));
        });
        optPage.addEventListener("mouseenter", () => { optPage.style.background = "rgba(245, 158, 11, 0.15)"; });
        optPage.addEventListener("mouseleave", () => { optPage.style.background = "transparent"; });
      }

      // Option 3: Jangan tampilkan di seluruh website (Hostname/domain)
      const optDomain = panel.querySelector("#jpd-opt-domain");
      if (optDomain) {
        optDomain.addEventListener("click", (e) => {
          e.stopPropagation();
          e.preventDefault();
          const dom = window.location.hostname.toLowerCase();
          if (!blockedDomains.includes(dom)) {
            blockedDomains.push(dom);
            try { localStorage.setItem("jpd_blacklist_domains", JSON.stringify(blockedDomains)); } catch (err) {}
            if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
              chrome.storage.local.set({ jpd_blacklist_domains: blockedDomains });
            }
          }
          try {
            sessionStorage.setItem("jpd_session_dismissed", "true");
          } catch (err) {}
          dismissWithAnimation(tr("toast_dismissed_domain") + dom);
        });
        optDomain.addEventListener("mouseenter", () => { optDomain.style.background = "rgba(239, 68, 68, 0.15)"; });
        optDomain.addEventListener("mouseleave", () => { optDomain.style.background = "transparent"; });
      }

      // Popover Quick Language Toggle Buttons (ID / EN)
      const popLangId = panel.querySelector("#jpd-popover-lang-id");
      const popLangEn = panel.querySelector("#jpd-popover-lang-en");
      if (popLangId) {
        popLangId.addEventListener("click", (e) => {
          e.stopPropagation();
          e.preventDefault();
          currentLang = "id";
          try { localStorage.setItem("jpd_language", "id"); } catch (err) {}
          if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
            chrome.storage.local.set({ jpd_language: "id" });
          }
          updatePanelTexts();
        });
      }
      if (popLangEn) {
        popLangEn.addEventListener("click", (e) => {
          e.stopPropagation();
          e.preventDefault();
          currentLang = "en";
          try { localStorage.setItem("jpd_language", "en"); } catch (err) {}
          if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
            chrome.storage.local.set({ jpd_language: "en" });
          }
          updatePanelTexts();
        });
      }

      // Close popover when clicking anywhere else
      document.addEventListener("click", (e) => {
        if (dismissPopover && dismissPopover.style.display === "block") {
          if (!dismissPopover.contains(e.target) && !closeBtn.contains(e.target)) {
            dismissPopover.style.display = "none";
          }
        }
      });
    }

    document.documentElement.appendChild(panel);
    return panel;
  }

  function scheduleHide() {
    // If the active media is a video that is visible in the viewport, keep it visible!
    if (activeMediaEl) {
      const isVideo = activeMediaEl.tagName === "VIDEO" || (activeMediaEl.closest && activeMediaEl.closest("video, #movie_player, .html5-video-player, ytd-reel-video-renderer, ytd-shorts"));
      if (isVideo) {
        const rect = activeMediaEl.getBoundingClientRect();
        if (rect.bottom > 0 && rect.top < window.innerHeight && rect.width > 60 && rect.height > 60) {
          // Video is visible on screen — do not hide!
          return;
        }
      }
    }

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

  function syncPanelPosition() {
    if (!panel || panel.style.display === "none" || isDragging) return;
    if (!activeMediaEl) return;

    if (!document.documentElement.contains(activeMediaEl)) {
      activeMediaEl = null;
      panel.style.display = "none";
      return;
    }

    const rect = activeMediaEl.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > window.innerHeight) {
      panel.style.opacity = "0";
      return;
    }

    panel.style.transition = "none";
    applyCornerPosition(panel, rect, preferredPos);
    panel.style.display = "block";
    panel.style.opacity = "1";
  }

  window.addEventListener("scroll", syncPanelPosition, { passive: true });
  window.addEventListener("resize", syncPanelPosition, { passive: true });

  function positionPanelOnElement(el, labelText, url, title) {
    if (!el) return;
    if (isSiteOrPageBlocked()) {
      if (panel) panel.style.display = "none";
      return;
    }
    const rect = el.getBoundingClientRect();
    if (rect.width < 100 || rect.height < 60) return;
    if (rect.bottom < 0 || rect.top > window.innerHeight) return;

    activeMediaEl = el;
    currentTargetUrl = url || el.currentSrc || el.src || window.location.href;
    currentTargetTitle = title || el.getAttribute("alt") || el.getAttribute("title") || document.title;

    const p = getOrCreatePanel();
    const btnText = p.querySelector("#idm-dl-btn-text");
    if (btnText) {
      btnText.textContent = labelText || tr("btn_download");
    }

    if (!isDragging) {
      // Disable transition so panel does NOT slide or flash at previous/default coordinates
      p.style.transition = "none";
      applyCornerPosition(p, rect, preferredPos);
    }
    p.style.display = "block";

    requestAnimationFrame(() => {
      p.style.transition = "opacity 0.18s ease";
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

  function getTikTokVideoUrl(videoEl, container) {
    if (!videoEl) return window.location.href;

    if (window.location.pathname.includes("/video/")) {
      return window.location.href;
    }

    // 1. Direct permalink anchor in container
    if (container) {
      const link = container.querySelector('a[href*="/video/"]');
      if (link && link.href) return link.href;
    }
    const nearest =
      (videoEl.closest && videoEl.closest('a[href*="/video/"]')) ||
      (videoEl.parentElement && videoEl.parentElement.querySelector('a[href*="/video/"]'));
    if (nearest && nearest.href) return nearest.href;

    // 2. Extract author and 19-digit videoId from player container ID (xgwrapper-*-7...)
    let cur = videoEl;
    let videoId = null;
    while (cur && cur !== document.body) {
      if (cur.id) {
        const m = cur.id.match(/\b(7\d{16,20})\b/);
        if (m) {
          videoId = m[1];
          break;
        }
      }
      cur = cur.parentElement;
    }

    if (videoId) {
      let author = "user";
      const card =
        (container ||
          (videoEl.closest &&
            videoEl.closest(
              'section, article, [data-e2e*="item"], div[class*="DivItemContainer"], [data-e2e="feed-video"]'
            ))) ||
        videoEl.parentElement;
      if (card) {
        const authorA = card.querySelector('a[href*="/@"]');
        if (authorA) {
          const parts = authorA.href.split("/@");
          if (parts[1]) author = parts[1].split("/")[0].split("?")[0];
        }
      }
      return `https://www.tiktok.com/@${author}/video/${videoId}`;
    }

    if (videoEl.currentSrc && !videoEl.currentSrc.startsWith("blob:")) {
      return videoEl.currentSrc;
    }
    if (videoEl.src && !videoEl.src.startsWith("blob:")) {
      return videoEl.src;
    }
    return window.location.href;
  }

  function getTikTokVideoTitle(container) {
    if (container) {
      const textEl = container.querySelector(
        '[data-e2e="video-desc"], [class*="DivTextContainer"], [class*="video-meta-caption"], [class*="desc"], h1'
      );
      if (textEl && textEl.textContent.trim()) {
        const clean = textEl.textContent.trim().replace(/[\\/:*?"<>|]/g, "_").slice(0, 60);
        if (clean.length > 2) return clean;
      }
      const authorEl = container.querySelector('[data-e2e="video-author-uniqueid"], [data-e2e="user-title"], a[href*="/@"]');
      if (authorEl && authorEl.textContent.trim()) {
        const author = authorEl.textContent.trim().replace("@", "").slice(0, 30);
        return `TikTok_${author}_${Date.now() % 100000}`;
      }
    }
    let docTitle = document.title || "";
    docTitle = docTitle.replace(/^\(\d+\)\s*/, "").replace(/\s*\|\s*TikTok.*$/i, "").trim();
    if (!docTitle || docTitle.toLowerCase().includes("watch trending") || docTitle.toLowerCase().includes("tiktok")) {
      return `TikTok_Video_${Date.now() % 100000}`;
    }
    return docTitle.replace(/[\\/:*?"<>|]/g, "_").slice(0, 60);
  }

  // 1. Mouseover listener: attach panel to media/player on hover (IDM behavior)
  document.addEventListener(
    "mouseover",
    (e) => {
      const el = e.target;
      if (!el) return;

      // Special handling for YouTube
      if (window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be")) {
        if (el.tagName === "VIDEO" || (el.closest && el.closest("#movie_player, .html5-video-player"))) {
          const player = el.closest("#movie_player, .html5-video-player") || el;
          positionPanelOnElement(player, "Download dengan JPD", window.location.href, document.title);
          return;
        }
      }

      // Special handling for TikTok Web
      if (window.location.hostname.includes("tiktok.com")) {
        const tiktokContainer =
          el.closest &&
          el.closest(
            'div[data-e2e="feed-item"], div[data-e2e="recommend-list-item-container"], div[class*="DivVideoContainer"], div[class*="DivPlayerContainer"], div[data-e2e="user-post-item"], div[class*="DivBasicPlayerWrapper"], div[data-e2e="feed-video"]'
          );
        if (tiktokContainer) {
          const video = tiktokContainer.querySelector("video");
          if (video) {
            const targetUrl = getTikTokVideoUrl(video, tiktokContainer);
            const title = getTikTokVideoTitle(tiktokContainer);
            positionPanelOnElement(video, "Download dengan JPD", targetUrl, title);
            return;
          }
        }
      }

      // Generic container containing video (handles transparent overlay masks on video players)
      if (el.tagName !== "VIDEO" && el.closest) {
        const videoWrapper = el.closest('div[class*="video"], div[class*="player"], div[data-e2e*="video"], [class*="video-container"]');
        if (videoWrapper) {
          const video = videoWrapper.querySelector("video");
          if (video && video.getBoundingClientRect().width > 100) {
            const targetUrl = (window.location.hostname.includes("tiktok.com"))
              ? getTikTokVideoUrl(video, videoWrapper)
              : (video.currentSrc || video.src || window.location.href);
            positionPanelOnElement(video, "Download dengan JPD", targetUrl, document.title);
            return;
          }
        }
      }

      if (el.tagName === "VIDEO") {
        positionPanelOnElement(el, "Download dengan JPD", el.currentSrc || el.src, document.title);
      } else if (el.closest && el.closest("#movie_player, .html5-video-player")) {
        const player = el.closest("#movie_player, .html5-video-player");
        const video = player.querySelector("video");
        if (video) {
          positionPanelOnElement(player, "Download dengan JPD", window.location.href, document.title);
        }
      } else if (el.tagName === "AUDIO") {
        positionPanelOnElement(el, "Download dengan JPD", el.currentSrc || el.src, document.title);
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
            positionPanelOnElement(el, "Download dengan JPD", imgSrc, imgTitle);
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
        positionPanelOnElement(el, "Download dengan JPD", targetUrl, document.title);
      } else if (el && el.tagName === "AUDIO") {
        positionPanelOnElement(el, "Download dengan JPD", el.currentSrc || el.src, document.title);
      }
    },
    true
  );

  // 3. Listener from background network sniffer (HLS/MP4 streams detected)
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "media_detected" && msg.url) {
      const v = document.querySelector("video");
      if (v && v.getBoundingClientRect().width > 120) {
        positionPanelOnElement(v, "Download dengan JPD", msg.url, document.title);
      }
      sendResponse({ status: "ok" });
    }
  });

  // 4. Dedicated active tracker for YouTube Shorts, Reels, and ongoing video playback
  function checkShortsAndVideos() {
    if (isDragging) return;

    // A. TikTok Web active feed & single video handling
    if (window.location.hostname.includes("tiktok.com")) {
      const tiktokVideos = Array.from(document.querySelectorAll("video")).filter((v) => {
        const r = v.getBoundingClientRect();
        return r.width > 80 && r.height > 100 && r.bottom > 60 && r.top < window.innerHeight - 60;
      });
      const activeTiktok = tiktokVideos.find((v) => !v.paused && v.currentTime > 0) || tiktokVideos[0];
      if (activeTiktok) {
        const container =
          activeTiktok.closest(
            'div[data-e2e="feed-item"], div[data-e2e="recommend-list-item-container"], div[class*="DivVideoContainer"], div[class*="DivPlayerContainer"], div[data-e2e="user-post-item"], div[class*="DivBasicPlayerWrapper"]'
          ) || activeTiktok.parentElement;
        const targetUrl = getTikTokVideoUrl(activeTiktok, container);
        const title = getTikTokVideoTitle(container);
        positionPanelOnElement(activeTiktok, "Download dengan JPD", targetUrl, title);
        return;
      }
    }

    // B. YouTube Shorts handling (dynamic reel feed)
    if (window.location.pathname.includes("/shorts/")) {
      const activeReel =
        document.querySelector("ytd-reel-video-renderer[is-active]") ||
        document.querySelector("ytd-shorts [is-active]") ||
        document.querySelector("ytd-reel-video-renderer");
      const video = activeReel ? activeReel.querySelector("video") : document.querySelector("ytd-shorts video");
      if (video) {
        const rect = video.getBoundingClientRect();
        if (rect.width > 80 && rect.height > 80 && rect.bottom > 0 && rect.top < window.innerHeight) {
          positionPanelOnElement(video, "Download dengan JPD", window.location.href, document.title);
          return;
        }
      }
    }

    // B. General YouTube main player
    if (window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be")) {
      const player = document.querySelector("#movie_player, .html5-video-player");
      const video = player ? player.querySelector("video") : null;
      if (video && !video.paused) {
        const rect = player.getBoundingClientRect();
        if (rect.width > 100 && rect.height > 100 && rect.bottom > 0 && rect.top < window.innerHeight) {
          positionPanelOnElement(player, "Download dengan JPD", window.location.href, document.title);
          return;
        }
      }
    }

    // C. Any video actively playing on screen
    const allVideos = Array.from(document.querySelectorAll("video"));
    const playingVideo = allVideos.find((v) => !v.paused && v.currentTime > 0);
    if (playingVideo) {
      const rect = playingVideo.getBoundingClientRect();
      if (rect.width > 120 && rect.height > 80 && rect.bottom > 0 && rect.top < window.innerHeight) {
        const targetUrl = playingVideo.currentSrc || playingVideo.src || window.location.href;
        positionPanelOnElement(playingVideo, "Download dengan JPD", targetUrl, document.title);
      }
    }
  }

  // Poll every 600ms to keep button permanently attached to active media without auto-hiding
  setInterval(checkShortsAndVideos, 600);
})();
