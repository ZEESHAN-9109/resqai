/* ============================================================
   RESQAI core client: API abstraction, auth, toasts, nav, transitions.
   ============================================================ */
(function () {
  "use strict";
  const CFG = window.RESQAI_CONFIG || { API_BASE_URL: "/api" };
  const TOKEN_KEY = "resqai_token";
  const USER_KEY = "resqai_user";

  /* ---------------- Auth token storage ---------------- */
  const Auth = {
    token: () => localStorage.getItem(TOKEN_KEY),
    user: () => { try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch (e) { return null; } },
    set: (token, user) => { localStorage.setItem(TOKEN_KEY, token); localStorage.setItem(USER_KEY, JSON.stringify(user || {})); },
    clear: () => { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); },
    isAuthed: () => !!localStorage.getItem(TOKEN_KEY),
  };

  /* ---------------- Centralised API client ---------------- */
  async function request(method, path, body, isForm) {
    const headers = {};
    const token = Auth.token();
    if (token) headers["Authorization"] = "Token " + token;
    let payload;
    if (isForm) { payload = body; }
    else if (body !== undefined) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }

    let resp;
    try {
      resp = await fetch(CFG.API_BASE_URL + path, { method, headers, body: payload });
    } catch (netErr) {
      Toast.error("Connection error", "Unable to reach the Django API.");
      throw { status: 0, detail: "Network failure" };
    }

    if (resp.status === 204) return null;
    let data = null;
    const ct = resp.headers.get("content-type") || "";
    if (ct.includes("application/json")) { try { data = await resp.json(); } catch (e) { data = null; } }

    if (!resp.ok) {
      if (resp.status === 401) {
        Auth.clear();
        if (!/\/login\/?$/.test(location.pathname)) location.href = "/login/";
      }
      const detail = (data && (data.detail || firstError(data))) || httpMessage(resp.status);
      throw { status: resp.status, detail, data };
    }
    return data;
  }

  function firstError(data) {
    if (!data || typeof data !== "object") return null;
    const k = Object.keys(data)[0];
    if (!k) return null;
    const v = data[k];
    return Array.isArray(v) ? `${k}: ${v[0]}` : `${k}: ${v}`;
  }
  function httpMessage(s) {
    return ({
      400: "Invalid request.", 403: "You do not have permission for this action.",
      404: "Resource not found.", 409: "Conflict with existing data.",
      422: "The submitted data could not be processed.", 429: "Too many requests — slow down.",
      500: "The server encountered an error.",
    })[s] || ("Request failed (" + s + ").");
  }

  const API = {
    get: (p) => request("GET", p),
    post: (p, b) => request("POST", p, b),
    postForm: (p, form) => request("POST", p, form, true),
    patch: (p, b) => request("PATCH", p, b),
    del: (p) => request("DELETE", p),
  };

  /* ---------------- Toasts ---------------- */
  function ensureToastContainer() {
    let c = document.querySelector(".toast-container");
    if (!c) { c = document.createElement("div"); c.className = "toast-container"; document.body.appendChild(c); }
    return c;
  }
  const ICONS = {
    success: '<i class="fa-solid fa-circle-check"></i>',
    error: '<i class="fa-solid fa-circle-exclamation"></i>',
    warning: '<i class="fa-solid fa-triangle-exclamation"></i>',
    info: '<i class="fa-solid fa-circle-info"></i>',
  };
  function showToast(type, title, msg) {
    const c = ensureToastContainer();
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.innerHTML = `<div style="color:var(--${type === 'success' ? 'green' : type === 'error' ? 'red' : type === 'warning' ? 'amber' : 'blue'})">${ICONS[type] || ''}</div>
      <div><div class="t-title">${escapeHtml(title || '')}</div>${msg ? `<div class="t-msg">${escapeHtml(msg)}</div>` : ''}</div>`;
    c.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(20px)"; el.style.transition = "all .25s"; setTimeout(() => el.remove(), 260); }, 3800);
  }
  const Toast = {
    success: (t, m) => showToast("success", t, m),
    error: (t, m) => showToast("error", t, m),
    warning: (t, m) => showToast("warning", t, m),
    info: (t, m) => showToast("info", t, m),
  };

  /* ---------------- Utilities ---------------- */
  function escapeHtml(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
  function timeAgo(iso) {
    if (!iso) return "—";
    const then = new Date(iso).getTime(); if (isNaN(then)) return "—";
    const s = Math.max(0, Math.floor((Date.now() - then) / 1000));
    if (s < 60) return s + "s ago";
    if (s < 3600) return Math.floor(s / 60) + "m ago";
    if (s < 86400) return Math.floor(s / 3600) + "h ago";
    return Math.floor(s / 86400) + "d ago";
  }
  function fmtNum(n) { return (n == null) ? "—" : Number(n).toLocaleString(); }
  function titleCase(s) { return String(s || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()); }
  function debounce(fn, wait) { let t; return function (...a) { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), wait); }; }
  function qp(name) { return new URLSearchParams(location.search).get(name); }
  function confidencePct(c) { return Math.round((c || 0) * 100); }

  function severityBadge(sev) { return `<span class="badge severity-${sev}">${titleCase(sev)}</span>`; }
  function statusBadge(st) { return `<span class="status-badge ${st}">${titleCase(st)}</span>`; }
  function verifBadge(v) { return `<span class="badge ${v}">${titleCase(v)}</span>`; }

  function loadingBlock(lines) {
    let h = '<div class="card card-pad">';
    for (let i = 0; i < (lines || 3); i++) h += `<div class="skeleton skeleton-line" style="width:${70 + Math.random() * 25}%"></div>`;
    return h + "</div>";
  }
  function emptyState(title, msg, icon) {
    return `<div class="empty-state"><div class="icon"><i class="fa-solid ${icon || 'fa-inbox'}"></i></div><h4>${escapeHtml(title)}</h4><p>${escapeHtml(msg || '')}</p></div>`;
  }
  function errorState(msg) {
    return `<div class="error-state"><div class="icon"><i class="fa-solid fa-plug-circle-xmark"></i></div><h4>Unable to load</h4><p>${escapeHtml(msg || 'Please try again.')}</p></div>`;
  }

  /* ---------------- Modal helper ---------------- */
  function openModal(title, bodyHtml, footHtml) {
    let overlay = document.getElementById("global-modal");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "global-modal"; overlay.className = "modal-overlay";
      document.body.appendChild(overlay);
      overlay.addEventListener("click", (e) => { if (e.target === overlay) closeModal(); });
    }
    overlay.innerHTML = `<div class="modal" role="dialog" aria-modal="true" data-testid="modal">
      <div class="modal-head"><h3>${escapeHtml(title)}</h3>
      <button class="icon-btn" data-testid="modal-close" onclick="RESQAI.closeModal()"><i class="fa-solid fa-xmark"></i></button></div>
      <div class="modal-body">${bodyHtml}</div>
      ${footHtml ? `<div class="modal-foot">${footHtml}</div>` : ""}</div>`;
    overlay.classList.add("open");
    return overlay;
  }
  function closeModal() { const o = document.getElementById("global-modal"); if (o) o.classList.remove("open"); }

  /* ---------------- Sidebar drawer (mobile) ---------------- */
  function initShell() {
    const sidebar = document.querySelector(".sidebar");
    const hamburger = document.getElementById("hamburger");
    const overlay = document.getElementById("drawer-overlay");
    if (hamburger && sidebar) {
      hamburger.addEventListener("click", () => { sidebar.classList.toggle("open"); if (overlay) overlay.classList.toggle("open"); });
    }
    if (overlay && sidebar) overlay.addEventListener("click", () => { sidebar.classList.remove("open"); overlay.classList.remove("open"); });
    document.querySelectorAll(".nav-item").forEach(a => a.addEventListener("click", () => {
      if (window.innerWidth <= 860 && sidebar) { sidebar.classList.remove("open"); if (overlay) overlay.classList.remove("open"); }
    }));
    // highlight active nav
    const path = location.pathname;
    document.querySelectorAll(".nav-item").forEach(a => {
      const href = a.getAttribute("href");
      if (href && (href === path || (href !== "/" && path.startsWith(href)))) a.classList.add("active");
    });
    // logout
    const lo = document.getElementById("logout-btn");
    if (lo) lo.addEventListener("click", async (e) => {
      e.preventDefault();
      try { await API.post("/auth/logout/"); } catch (_) {}
      Auth.clear(); location.href = "/login/";
    });
    // populate user chip
    const u = Auth.user();
    if (u) {
      document.querySelectorAll("[data-user-name]").forEach(el => el.textContent = u.full_name || u.email || "User");
      document.querySelectorAll("[data-user-role]").forEach(el => el.textContent = titleCase(u.role || ""));
      document.querySelectorAll("[data-user-initial]").forEach(el => el.textContent = (u.full_name || u.email || "U").charAt(0).toUpperCase());
    }
  }

  /* ---------------- Auth guard for protected pages ---------------- */
  function guard() {
    if (document.body.dataset.protected === "true" && !Auth.isAuthed()) {
      location.href = "/login/";
      return false;
    }
    return true;
  }

  /* ---------------- Expose ---------------- */
  window.RESQAI = {
    CFG, API, Auth, Toast,
    escapeHtml, timeAgo, fmtNum, titleCase, debounce, qp, confidencePct,
    severityBadge, statusBadge, verifBadge,
    loadingBlock, emptyState, errorState,
    openModal, closeModal, guard,
  };

  document.addEventListener("DOMContentLoaded", function () {
    if (!guard()) return;
    initShell();
    if (window.RESQAI_PAGE_INIT) { try { window.RESQAI_PAGE_INIT(); } catch (e) { console.error(e); } }
  });
})();
