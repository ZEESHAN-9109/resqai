/* ============================================================
   RESQAI live data: USGS earthquakes + free GDACS/NASA EONET fires.
   Handles polling, last-updated, data-age, connection status, and
   stops polling when the page/tab is hidden or unloaded.
   ============================================================ */
(function () {
  "use strict";
  const API = window.RESQAI.API;
  const timers = [];

  function connBadge(status, connection) {
    const map = {
      LIVE: ["dot-green", "LIVE"], "NEAR REAL-TIME": ["dot-green", "NEAR REAL-TIME"],
      RECENT: ["dot-amber", "RECENT"], STALE: ["dot-amber", "STALE"],
      UNAVAILABLE: ["dot-red", "UNAVAILABLE"], OPTIONAL: ["dot-grey", "OPTIONAL"],
    };
    const [cls, label] = map[connection] || (status === "connected" ? ["dot-green", "CONNECTED"] : ["dot-red", "UNAVAILABLE"]);
    return `<span class="dot ${cls} ${cls === 'dot-green' ? 'pulse' : ''}"></span> ${label}`;
  }

  const LiveData = {
    connBadge,

    async fetchEarthquakes(minMag) {
      const q = minMag ? ("?min_magnitude=" + minMag) : "";
      return API.get("/live/earthquakes/" + q);
    },
    async fetchFires() {
      // Free public GDACS feed with NASA EONET fallback; no API key required.
      return API.get("/live/fires/");
    },
    async fetchSystemStatus() { return API.get("/system/status/"); },

    poll(fn, intervalMs) {
      let stopped = false;
      const tick = async () => {
        if (stopped || document.hidden) return;
        try { await fn(); } catch (e) { /* handled by callers */ }
      };
      tick();
      const id = setInterval(tick, intervalMs);
      timers.push(id);
      const onVis = () => { if (!document.hidden) tick(); };
      document.addEventListener("visibilitychange", onVis);
      return () => { stopped = true; clearInterval(id); document.removeEventListener("visibilitychange", onVis); };
    },

    stopAll() { timers.forEach(clearInterval); timers.length = 0; },
  };

  window.addEventListener("beforeunload", () => LiveData.stopAll());
  window.RESQAI.LiveData = LiveData;
})();
