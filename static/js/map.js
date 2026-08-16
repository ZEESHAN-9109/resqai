/* ============================================================
   RESQAI map layer. Uses Leaflet (OpenStreetMap) as the default free map.
   If a Google Maps key is present in config it is noted, but the operational
   map runs on Leaflet so the platform always works without a paid key.
   Prevents duplicate initialisation on a page.
   ============================================================ */
(function () {
  "use strict";
  const R = window.RESQAI;

  const COLORS = {
    earthquake: "#f2a63b", fire: "#ef5350", incident: "#4f8ff0",
    priority: "#c084fc", route: "#35c98a", team: "#7fd1e0",
    hospital: "#ff8a87", shelter: "#6fe0ac", relief: "#f7bd6b",
  };

  function makeIcon(color) {
    return L.divIcon({
      className: "resqai-marker",
      html: `<span style="display:block;width:14px;height:14px;border-radius:50%;background:${color};border:2px solid #0a0f1c;box-shadow:0 0 0 2px ${color}55"></span>`,
      iconSize: [14, 14], iconAnchor: [7, 7],
    });
  }

  const MapManager = {
    map: null,
    layers: {},

    init(elId, center, zoom) {
      if (this.map) return this.map;
      const el = document.getElementById(elId);
      if (!el || typeof L === "undefined") return null;
      this.map = L.map(elId, { zoomControl: true, attributionControl: true })
        .setView(center || [22.5, 80], zoom || 5);
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: "abcd", maxZoom: 19,
      }).addTo(this.map);
      ["earthquake", "fire", "incident", "priority", "route", "team", "hospital", "shelter", "relief"].forEach(k => {
        this.layers[k] = L.layerGroup().addTo(this.map);
      });
      return this.map;
    },

    color: (k) => COLORS[k],

    clear(layerKey) { if (this.layers[layerKey]) this.layers[layerKey].clearLayers(); },

    toggle(layerKey, on) {
      const lyr = this.layers[layerKey];
      if (!lyr) return;
      if (on) { if (!this.map.hasLayer(lyr)) lyr.addTo(this.map); }
      else { if (this.map.hasLayer(lyr)) this.map.removeLayer(lyr); }
    },

    addMarker(layerKey, lat, lng, popupHtml) {
      if (!this.map || !this.layers[layerKey] || lat == null || lng == null) return null;
      const m = L.marker([lat, lng], { icon: makeIcon(COLORS[layerKey] || "#4f8ff0") });
      if (popupHtml) m.bindPopup(popupHtml);
      m.addTo(this.layers[layerKey]);
      return m;
    },

    addCircle(layerKey, lat, lng, radius, popupHtml) {
      if (!this.map || !this.layers[layerKey]) return null;
      const c = L.circle([lat, lng], { radius: radius || 400, color: COLORS[layerKey], fillColor: COLORS[layerKey], fillOpacity: 0.18, weight: 1 });
      if (popupHtml) c.bindPopup(popupHtml);
      c.addTo(this.layers[layerKey]);
      return c;
    },

    drawRoute(coords, color) {
      const line = L.polyline(coords, { color: color || COLORS.route, weight: 4, opacity: 0.85, dashArray: "6 6" });
      line.addTo(this.layers.route);
      this.map.fitBounds(line.getBounds(), { padding: [40, 40] });
      return line;
    },

    fit(points) {
      if (!this.map || !points.length) return;
      this.map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 12 });
    },

    destroy() { if (this.map) { this.map.remove(); this.map = null; this.layers = {}; } },
  };

  window.RESQAI.MapManager = MapManager;
})();
