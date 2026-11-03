// JustPressDownload (JPD) Background Service Worker - Dual Bridge (Local HTTP Server + Native Messaging)
const LOCAL_SERVER_URL = "http://127.0.0.1:19900";
const NATIVE_HOST = "com.justpressdownload.host";
const FALLBACK_NATIVE_HOST = "com.idmclone.host";

// Per-tab detected media cache
const tabMedia = {};

// Setup Context Menus on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "idm_download_link",
    title: "Download dengan JPD",
    contexts: ["link", "video", "audio", "image"]
  });

  chrome.contextMenus.create({
    id: "idm_download_page",
    title: "Download semua tautan dengan JPD",
    contexts: ["page"]
  });
});

// Clean up tab media on tab close
chrome.tabs.onRemoved.addListener((tabId) => {
  delete tabMedia[tabId];
});

// Whitelist of downloadable extensions to intercept automatically (matching IDM Options -> File Types)
const INTERCEPT_EXTENSIONS = new Set([
  // Archives
  "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso", "img", "bin",
  // Installers & Programs
  "exe", "msi", "apk", "dmg", "pkg", "deb", "rpm",
  // Video & Audio
  "mp4", "mkv", "webm", "avi", "mov", "flv", "wmv", "mp3", "m4a", "wav", "flac", "aac", "ogg",
  // Documents
  "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "epub", "csv",
  // Images
  "jpg", "jpeg", "png", "webp", "gif", "svg", "bmp", "ico", "tif", "tiff", "psd"
]);

// Double-extension adware & scam detector (e.g. invoice.pdf.exe)
function checkDoubleExtension(filename) {
  if (!filename) return { isSuspicious: false, warning: "" };
  const parts = filename.toLowerCase().split(".");
  if (parts.length >= 3) {
    const last = parts[parts.length - 1];
    const prev = parts[parts.length - 2];
    const execs = ["exe", "scr", "vbs", "bat", "cmd", "pif", "hta", "jar", "ps1"];
    const docImgs = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg", "png", "mp4", "mp3", "zip"];
    if (execs.includes(last) && docImgs.includes(prev)) {
      return {
        isSuspicious: true,
        warning: `Peringatan: Berkas memiliki ekstensi ganda (.${prev}.${last}) yang umum dipakai adware/malware!`
      };
    }
  }
  const dangerousScripts = ["vbs", "scr", "pif", "hta"];
  if (parts.length >= 2 && dangerousScripts.includes(parts[parts.length - 1])) {
    return {
      isSuspicious: true,
      warning: `Peringatan: Berkas .${parts[parts.length - 1]} merupakan skrip berisiko tinggi!`
    };
  }
  return { isSuspicious: false, warning: "" };
}

// Intercept browser downloads automatically (IDM Signature Browser Integration)
if (chrome.downloads && chrome.downloads.onDeterminingFilename) {
  chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
    // Ignore internal or non-HTTP downloads
    if (!item.url || item.url.startsWith("blob:") || item.url.startsWith("data:") || item.url.startsWith("chrome://")) {
      suggest();
      return;
    }

    const filename = item.filename ? item.filename.split(/[\\/]/).pop() : "";
    const ext = filename.split(".").pop().toLowerCase();

    // Check if filename matches downloadable whitelist
    if (ext && INTERCEPT_EXTENSIONS.has(ext)) {
      // 1. Cancel Chrome's slow built-in download immediately
      try {
        chrome.downloads.cancel(item.id, () => {
          chrome.downloads.erase({ id: item.id });
        });
      } catch (e) {}

      // 2. Perform security scan
      const sec = checkDoubleExtension(filename);
      const downloadUrl = item.finalUrl || item.url;
      const fileSize = (item.fileSize && item.fileSize > 0) ? item.fileSize : (item.totalBytes || 0);

      const dispatch = (cookieStr) => {
        sendDownloadToHost(
          downloadUrl,
          filename,
          false,
          item.referrer || "",
          null,
          sec.isSuspicious,
          sec.warning,
          fileSize,
          cookieStr
        );
      };

      // 3. Extract browser cookies for the download domain to preserve Cloudflare clearance & token
      try {
        if (chrome.cookies && chrome.cookies.getAll) {
          chrome.cookies.getAll({ url: downloadUrl }, (cookies) => {
            if (chrome.runtime.lastError || !cookies) {
              dispatch("");
            } else {
              const cookieHeader = cookies.map(c => `${c.name}=${c.value}`).join("; ");
              dispatch(cookieHeader);
            }
          });
        } else {
          dispatch("");
        }
      } catch (err) {
        dispatch("");
      }
      suggest();
      return true;
    }

    // Unmatched extensions (HTML, PHP, JS, CSS) proceed normally in browser
    suggest();
  });
}

// Sniff network responses for video / streaming manifests (mimicking IDM network monitoring)
const STREAM_EXTS = [".m3u8", ".mpd", ".mp4", ".webm"];

chrome.webRequest.onResponseStarted.addListener(
  (details) => {
    // Only capture top-level requests, ignore tiny range chunks to avoid flooding
    if (details.tabId <= 0 || details.type === "image" || details.type === "stylesheet") return;
    const url = details.url;

    // Filter out micro-chunks and analytics
    if (url.includes("/analytics") || url.includes("/telemetry") || url.includes("segment") || url.includes(".ts")) {
      return;
    }

    const lowerUrl = url.toLowerCase();
    const isStreamManifest = STREAM_EXTS.some((ext) => lowerUrl.includes(ext)) ||
                             lowerUrl.includes("mime_type=video") ||
                             lowerUrl.includes("tiktokcdn.com") ||
                             lowerUrl.includes("byteoversea.com") ||
                             lowerUrl.includes("ibytedtos.com");
    if (!isStreamManifest) return;

    if (!tabMedia[details.tabId]) tabMedia[details.tabId] = [];
    const list = tabMedia[details.tabId];

    // Limit to max 5 distinct streams per tab
    if (list.length < 5 && !list.some((item) => item.url === url)) {
      list.push({ url, mediaType: lowerUrl.includes(".m3u8") ? "HLS" : "MP4", title: "Media Stream" });
      chrome.tabs.sendMessage(details.tabId, {
        action: "media_detected",
        url: url
      }).catch(() => {});
    }
  },
  { urls: ["<all_urls>"] }
);

// Handle Context Menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  let targetUrl = null;

  // On Google Images search results: extract full-resolution source image from imgurl parameter
  if (info.linkUrl && info.linkUrl.includes("imgurl=")) {
    try {
      const u = new URL(info.linkUrl);
      const imgurl = u.searchParams.get("imgurl");
      if (imgurl) targetUrl = decodeURIComponent(imgurl);
    } catch (e) {}
  }

  if (!targetUrl) {
    if (info.mediaType === "image" || info.mediaType === "video" || info.mediaType === "audio") {
      targetUrl = info.srcUrl || info.linkUrl;
    } else {
      targetUrl = info.linkUrl || info.srcUrl || info.pageUrl;
    }
  }

  if (targetUrl) {
    sendDownloadToHost(targetUrl, tab ? tab.title : "download", false, tab ? tab.url : "");
  }
});

// Handle messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "download") {
    sendDownloadToHost(request.url, request.title, request.auto_start, request.referer || "", sendResponse);
    return true;
  }
  if (request.action === "get_media") {
    const tabId = sender.tab ? sender.tab.id : null;
    sendResponse({ streams: tabId ? (tabMedia[tabId] || []) : [] });
    return false;
  }
});

async function sendDownloadToHost(url, title, autoStart = false, referer = "", callback = null, isSuspicious = false, securityWarning = "", fileSize = 0, cookie = "") {
  if (typeof autoStart === "function") {
    callback = autoStart;
    autoStart = false;
  }
  if (typeof referer === "function") {
    callback = referer;
    referer = "";
  }
  const payload = {
    url: url,
    title: title || "media_file",
    parts: 32,
    auto_start: autoStart || false,
    referer: referer || "",
    is_suspicious: isSuspicious,
    security_warning: securityWarning || "",
    file_size: fileSize || 0,
    cookie: cookie || "",
    user_agent: navigator.userAgent
  };

  let responded = false;
  function reply(data) {
    if (!responded) {
      responded = true;
      if (callback) callback(data);
    }
  }

  // Safety fallback timer to prevent infinite hang
  const timer = setTimeout(() => {
    reply({ status: "error", error: "Connection to Desktop App timed out. Pastikan JustPressDownload.exe atau run_gui.bat terbuka!" });
  }, 3500);

  // Primary path: Direct HTTP Loopback to JustPressDownload (JPD) Desktop App
  try {
    const controller = new AbortController();
    const abortTimeout = setTimeout(() => controller.abort(), 3000);

    const resp = await fetch(`${LOCAL_SERVER_URL}/api/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    clearTimeout(abortTimeout);
    clearTimeout(timer);

    if (resp.ok) {
      const data = await resp.json();
      console.log("[JustPressDownload] Successfully dispatched to desktop app:", data);
      showNotification("JustPressDownload (JPD)", `Unduhan dimulai: ${title || url.slice(0, 40)}`);
      reply({ status: "ok", taskId: data.taskId });
      return;
    } else {
      reply({ status: "error", error: `Server error ${resp.status}` });
      return;
    }
  } catch (err) {
    console.log("[JustPressDownload] Local server not active, trying Native Messaging fallback...", err);
  }

  // Fallback path: Native Messaging (Auto-launches JustPressDownload.exe if closed!)
  const tryNative = (hostName, onFail) => {
    try {
      chrome.runtime.sendNativeMessage(hostName, { action: "download", ...payload }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn(`[JustPressDownload] Native host (${hostName}) error:`, chrome.runtime.lastError.message);
          if (onFail) onFail();
        } else {
          clearTimeout(timer);
          showNotification("JustPressDownload (JPD)", `Membuka aplikasi & mengirim: ${title || "berkas"}`);
          reply(response || { status: "ok" });
        }
      });
    } catch (err) {
      if (onFail) onFail();
    }
  };

  tryNative(NATIVE_HOST, () => {
    tryNative(FALLBACK_NATIVE_HOST, () => {
      clearTimeout(timer);
      reply({ status: "error", error: "Gagal menghubungkan ke JustPressDownload. Pastikan JustPressDownload terpasang!" });
    });
  });
}

function showNotification(title, message) {
  try {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "images/logo48.png",
      title: title,
      message: message,
      priority: 2
    });
  } catch (e) {}
}
