// Popup script for JPD Integration Module (Dual Language ID & EN)
document.addEventListener("DOMContentLoaded", () => {
  const statusDiv = document.getElementById("status");
  const statusText = document.getElementById("status-text") || statusDiv;
  const urlInput = document.getElementById("urlInput");
  const downloadBtn = document.getElementById("downloadBtn");
  const downloadBtnText = document.getElementById("downloadBtnText") || downloadBtn;
  const lblUrl = document.getElementById("lblUrl");
  const hintText = document.getElementById("hintText");
  const langToggleBtn = document.getElementById("langToggleBtn");

  // Site Exclusion DOM Elements
  const siteToggleSection = document.getElementById("siteToggleSection");
  const siteDomainLabel = document.getElementById("siteDomainLabel");
  const siteToggleSwitch = document.getElementById("siteToggleSwitch");
  const exclusionAccordionHeader = document.getElementById("exclusionAccordionHeader");
  const exclusionAccordionTitle = document.getElementById("exclusionAccordionTitle");
  const exclusionCount = document.getElementById("exclusionCount");
  const accordionArrow = document.getElementById("accordionArrow");
  const exclusionList = document.getElementById("exclusionList");
  const exclusionEmptyText = document.getElementById("exclusionEmptyText");
  const exclusionItems = document.getElementById("exclusionItems");

  let currentLang = "id";
  try {
    const cached = localStorage.getItem("jpd_language");
    if (cached) currentLang = cached;
  } catch (e) {}

  let activeTab = null;
  let activeDomain = "";
  let activeCleanUrl = "";
  let blockedDomains = [];
  let blockedPages = [];

  const STRINGS = {
    id: {
      status_checking: "Memeriksa koneksi host...",
      status_connected_http: "Just Press Download (JPD) Terhubung (Port 19900)",
      status_connected_native: "Just Press Download (JPD) Host Terhubung (Native IPC)",
      status_disconnected: "Aplikasi Belum Aktif (Buka Just Press Download)",
      label_url: "Unduh Tautan Langsung:",
      btn_send: "+ Kirim ke Just Press Download",
      btn_sending: "Mengirim...",
      hint: "Otomatis mencegat unduhan dari Chromium & Firefox",
      alert_empty: "Masukkan tautan URL unduhan terlebih dahulu",
      alert_success: "Tugas unduhan berhasil dikirim ke Just Press Download (JPD)!",
      alert_fail: "Gagal mengirim tugas: Pastikan Just Press Download (JPD) aktif.",
      lang_btn: "ID 🇮🇩",
      site_toggle_active: "Tombol di ",
      site_toggle_unsupported: "Halaman Sistem Browser",
      exclusion_title: "Daftar Pengecualian",
      exclusion_empty: "Belum ada situs yang dinonaktifkan.",
      exclusion_badge_site: "Situs",
      exclusion_badge_page: "Halaman",
      exclusion_delete_tip: "Hapus dan aktifkan kembali tombol",
    },
    en: {
      status_checking: "Checking host connection...",
      status_connected_http: "Just Press Download (JPD) Connected (Port 19900)",
      status_connected_native: "Just Press Download (JPD) Host Connected (Native IPC)",
      status_disconnected: "Application Offline (Launch Just Press Download)",
      label_url: "Direct Download URL:",
      btn_send: "+ Send to Just Press Download",
      btn_sending: "Sending...",
      hint: "Automatically intercepts downloads from Chromium & Firefox",
      alert_empty: "Please enter a download URL first",
      alert_success: "Download task dispatched to Just Press Download (JPD) successfully!",
      alert_fail: "Failed to dispatch: Ensure Just Press Download (JPD) is running.",
      lang_btn: "EN 🇬🇧",
      site_toggle_active: "Button on ",
      site_toggle_unsupported: "Browser System Page",
      exclusion_title: "Excluded Sites",
      exclusion_empty: "No disabled sites yet.",
      exclusion_badge_site: "Site",
      exclusion_badge_page: "Page",
      exclusion_delete_tip: "Remove and re-enable button",
    }
  };

  function tr(key) {
    const tbl = STRINGS[currentLang] || STRINGS.id;
    return tbl[key] || STRINGS.id[key] || key;
  }

  function applyLanguage() {
    if (lblUrl) lblUrl.textContent = tr("label_url");
    if (downloadBtnText) downloadBtnText.textContent = tr("btn_send");
    if (hintText) hintText.textContent = tr("hint");
    if (langToggleBtn) langToggleBtn.textContent = tr("lang_btn");
    if (exclusionAccordionTitle) exclusionAccordionTitle.textContent = tr("exclusion_title");
    if (exclusionEmptyText) exclusionEmptyText.textContent = tr("exclusion_empty");
    updateSiteToggleUI();
    renderExclusionList();
    checkStatus();
  }

  function isCurrentSiteBlocked() {
    if (!activeDomain) return false;
    for (let d of blockedDomains) {
      if (activeDomain === d || activeDomain.endsWith("." + d)) return true;
    }
    for (let p of blockedPages) {
      if (activeCleanUrl && activeCleanUrl.toLowerCase() === p.toLowerCase()) return true;
    }
    return false;
  }

  function updateSiteToggleUI() {
    if (!siteToggleSection || !siteDomainLabel || !siteToggleSwitch) return;
    if (!activeDomain) {
      siteDomainLabel.textContent = tr("site_toggle_unsupported");
      siteToggleSwitch.disabled = true;
      siteToggleSwitch.checked = false;
      return;
    }
    siteToggleSwitch.disabled = false;
    siteDomainLabel.textContent = tr("site_toggle_active") + activeDomain;
    siteToggleSwitch.checked = !isCurrentSiteBlocked();
  }

  function saveExclusions(callback) {
    try {
      localStorage.setItem("jpd_blacklist_domains", JSON.stringify(blockedDomains));
      localStorage.setItem("jpd_blacklist_pages", JSON.stringify(blockedPages));
    } catch (e) {}

    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({
        jpd_blacklist_domains: blockedDomains,
        jpd_blacklist_pages: blockedPages,
      }, () => {
        updateSiteToggleUI();
        renderExclusionList();
        if (callback) callback();
      });
    } else {
      updateSiteToggleUI();
      renderExclusionList();
      if (callback) callback();
    }
  }

  function renderExclusionList() {
    if (!exclusionItems || !exclusionCount || !exclusionEmptyText) return;
    const total = blockedDomains.length + blockedPages.length;
    exclusionCount.textContent = total;
    exclusionItems.innerHTML = "";

    if (total === 0) {
      exclusionEmptyText.style.display = "block";
      return;
    }
    exclusionEmptyText.style.display = "none";

    // 1. Render domain blacklist
    blockedDomains.forEach((dom) => {
      const item = document.createElement("div");
      item.className = "exclusion-item";
      item.innerHTML = `
        <div class="exclusion-meta">
          <span class="badge-type site">${tr("exclusion_badge_site")}</span>
          <span class="exclusion-text" title="${dom}">${dom}</span>
        </div>
        <button class="btn-delete-exclusion" title="${tr("exclusion_delete_tip")}">✕</button>
      `;
      const btnDel = item.querySelector(".btn-delete-exclusion");
      btnDel.addEventListener("click", () => {
        blockedDomains = blockedDomains.filter((d) => d !== dom);
        saveExclusions(() => {
          if (activeDomain && (activeDomain === dom || activeDomain.endsWith("." + dom))) {
            if (activeTab && activeTab.id && chrome.tabs && chrome.tabs.sendMessage) {
              chrome.tabs.sendMessage(activeTab.id, { action: "jpd_unblock_and_show" });
            }
          }
        });
      });
      exclusionItems.appendChild(item);
    });

    // 2. Render page blacklist
    blockedPages.forEach((pageUrl) => {
      const item = document.createElement("div");
      item.className = "exclusion-item";
      item.innerHTML = `
        <div class="exclusion-meta">
          <span class="badge-type page">${tr("exclusion_badge_page")}</span>
          <span class="exclusion-text" title="${pageUrl}">${pageUrl}</span>
        </div>
        <button class="btn-delete-exclusion" title="${tr("exclusion_delete_tip")}">✕</button>
      `;
      const btnDel = item.querySelector(".btn-delete-exclusion");
      btnDel.addEventListener("click", () => {
        blockedPages = blockedPages.filter((p) => p !== pageUrl);
        saveExclusions(() => {
          if (activeCleanUrl && activeCleanUrl.toLowerCase() === pageUrl.toLowerCase()) {
            if (activeTab && activeTab.id && chrome.tabs && chrome.tabs.sendMessage) {
              chrome.tabs.sendMessage(activeTab.id, { action: "jpd_unblock_and_show" });
            }
          }
        });
      });
      exclusionItems.appendChild(item);
    });
  }

  // Accordion Expand/Collapse
  if (exclusionAccordionHeader && exclusionList) {
    exclusionAccordionHeader.addEventListener("click", () => {
      const isClosed = exclusionList.style.display === "none";
      exclusionList.style.display = isClosed ? "block" : "none";
      if (accordionArrow) accordionArrow.style.transform = isClosed ? "rotate(180deg)" : "rotate(0deg)";
    });
  }

  // Toggle Switch Event
  if (siteToggleSwitch) {
    siteToggleSwitch.addEventListener("change", () => {
      if (!activeDomain) return;
      const isNowEnabled = siteToggleSwitch.checked;
      if (isNowEnabled) {
        // Unblock: remove domain from blockedDomains and activeCleanUrl from blockedPages
        blockedDomains = blockedDomains.filter((d) => d !== activeDomain && !activeDomain.endsWith("." + d));
        if (activeCleanUrl) {
          blockedPages = blockedPages.filter((p) => p.toLowerCase() !== activeCleanUrl.toLowerCase());
        }
        saveExclusions(() => {
          if (activeTab && activeTab.id && chrome.tabs && chrome.tabs.sendMessage) {
            chrome.tabs.sendMessage(activeTab.id, { action: "jpd_unblock_and_show" });
          }
        });
      } else {
        // Block: add domain to blockedDomains
        if (!blockedDomains.includes(activeDomain)) {
          blockedDomains.push(activeDomain);
          saveExclusions();
        }
      }
    });
  }

  // Load exclusions from storage
  try {
    const cd = localStorage.getItem("jpd_blacklist_domains");
    if (cd) blockedDomains = JSON.parse(cd);
  } catch (e) {}
  try {
    const cp = localStorage.getItem("jpd_blacklist_pages");
    if (cp) blockedPages = JSON.parse(cp);
  } catch (e) {}

  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["jpd_blacklist_domains", "jpd_blacklist_pages"], (res) => {
      if (res && res.jpd_blacklist_domains) {
        blockedDomains = res.jpd_blacklist_domains;
      }
      if (res && res.jpd_blacklist_pages) {
        blockedPages = res.jpd_blacklist_pages;
      }
      updateSiteToggleUI();
      renderExclusionList();
    });
  }

  // Query active tab URL & domain
  if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.query) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs && tabs[0] && tabs[0].url) {
        activeTab = tabs[0];
        try {
          const u = new URL(activeTab.url);
          if (u.protocol === "http:" || u.protocol === "https:") {
            activeDomain = u.hostname.toLowerCase();
            activeCleanUrl = u.origin + u.pathname;
          } else {
            activeDomain = "";
          }
        } catch (e) {
          activeDomain = "";
        }
      }
      updateSiteToggleUI();
    });
  }

  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ jpd_language: currentLang }, (items) => {
      if (items && items.jpd_language) {
        currentLang = items.jpd_language;
        try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
        applyLanguage();
      }
    });
  }

  if (langToggleBtn) {
    langToggleBtn.addEventListener("click", () => {
      currentLang = (currentLang === "id") ? "en" : "id";
      try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
      if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ jpd_language: currentLang });
      }
      applyLanguage();
    });
  }

  function setStatus(online, text) {
    if (online) {
      statusDiv.classList.add("online");
      statusDiv.classList.remove("offline");
      statusText.textContent = text || tr("status_connected_http");
    } else {
      statusDiv.classList.remove("online");
      statusDiv.classList.add("offline");
      statusText.textContent = text || tr("status_disconnected");
    }
  }

  function checkStatus() {
    fetch("http://127.0.0.1:19900/api/ping")
      .then((r) => r.json())
      .then((data) => {
        if (data && data.status === "ok") {
          setStatus(true, tr("status_connected_http"));
          if (data.language && data.language !== currentLang) {
            currentLang = data.language;
            try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
            if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
              chrome.storage.local.set({ jpd_language: currentLang });
            }
            applyLanguage();
          }
        } else {
          throw new Error("Invalid ping response");
        }
      })
      .catch(() => {
        if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendNativeMessage) {
          chrome.runtime.sendNativeMessage("com.justpressdownload.host", { action: "ping" }, (response) => {
            if (!chrome.runtime.lastError && response && response.status === "ok") {
              setStatus(true, tr("status_connected_native"));
            } else {
              chrome.runtime.sendNativeMessage("com.idmclone.host", { action: "ping" }, (resp2) => {
                if (!chrome.runtime.lastError && resp2 && resp2.status === "ok") {
                  setStatus(true, tr("status_connected_native"));
                } else {
                  setStatus(false, tr("status_disconnected"));
                }
              });
            }
          });
        } else {
          setStatus(false, tr("status_disconnected"));
        }
      });
  }

  downloadBtn.addEventListener("click", () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert(tr("alert_empty"));
      urlInput.focus();
      return;
    }

    downloadBtnText.textContent = tr("btn_sending");
    downloadBtn.disabled = true;

    // Send task via native messaging or loopback server
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendNativeMessage) {
      chrome.runtime.sendNativeMessage(
        "com.justpressdownload.host",
        { action: "download", url: url },
        (response) => {
          downloadBtn.disabled = false;
          downloadBtnText.textContent = tr("btn_send");
          if (chrome.runtime.lastError || (response && response.status === "error")) {
            // Fallback to local HTTP loopback server
            fetch("http://127.0.0.1:19900/api/download", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ url: url }),
            })
              .then((r) => r.json())
              .then((data) => {
                urlInput.value = "";
                alert(tr("alert_success"));
              })
              .catch((err) => {
                alert(tr("alert_fail"));
              });
          } else {
            urlInput.value = "";
            alert(tr("alert_success"));
          }
        }
      );
    } else {
      fetch("http://127.0.0.1:19900/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      })
        .then((r) => r.json())
        .then((data) => {
          downloadBtn.disabled = false;
          downloadBtnText.textContent = tr("btn_send");
          urlInput.value = "";
          alert(tr("alert_success"));
        })
        .catch((err) => {
          downloadBtn.disabled = false;
          downloadBtnText.textContent = tr("btn_send");
          alert(tr("alert_fail"));
        });
    }
  });

  applyLanguage();
});
