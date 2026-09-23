const SWFR_DEFAULTS = {
  title: "Streaming Web",
  searchbox: true,
  posters_par_lot: 8,
  home_section_count: 10,
  scroll_infini: false,
  debug: false,
};

class StreamingWebFrCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = { ...SWFR_DEFAULTS };
    this._hass = null;
    this._loaded = false;
    this._loading = false;
    this._error = null;
    this._data = { providers: [], players: [], items: [] };
    this._provider = "";
    this._query = "";
    this._sort = "default";
    this._view = "home";
    this._catalogCategory = "all";
    this._visible = SWFR_DEFAULTS.posters_par_lot;
    this._searchTimer = null;
    this._popup = null;
    this._popupLoading = false;
    this._playStatus = "";
    this._observer = null;
    this._remoteLoading = false;
  }

  setConfig(config) {
    this._config = {
      ...SWFR_DEFAULTS,
      ...(config || {}),
    };
    const batch = Number(this._config.posters_par_lot);
    this._config.posters_par_lot = Number.isFinite(batch) && batch > 0 ? Math.floor(batch) : 8;
    const homeCount = Number(this._config.home_section_count);
    this._config.home_section_count = Number.isFinite(homeCount) && homeCount > 0 ? Math.floor(homeCount) : 10;
    this._config.searchbox = this._config.searchbox !== false;
    this._config.scroll_infini = this._config.scroll_infini === true;
    this._config.debug = this._config.debug === true;
    this._visible = this._config.posters_par_lot;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._loaded && !this._loading) this._load();
  }

  getCardSize() {
    return 6;
  }

  static getStubConfig() {
    return {
      title: "Streaming Web",
      searchbox: true,
      posters_par_lot: 8,
      home_section_count: 10,
      scroll_infini: false,
      debug: false,
    };
  }

  _esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  _focusSnapshot() {
    const root = this.shadowRoot;
    const input = root?.querySelector(".search");
    if (!input || root.activeElement !== input) return null;
    return {
      start: input.selectionStart,
      end: input.selectionEnd,
    };
  }

  _restoreFocus(snapshot) {
    if (!snapshot) return;
    queueMicrotask(() => {
      const input = this.shadowRoot?.querySelector(".search");
      if (!input) return;
      input.focus({ preventScroll: true });
      try {
        input.setSelectionRange(snapshot.start, snapshot.end);
      } catch (_) {}
    });
  }

  async _load({ append = false, cursor = null } = {}) {
    if (!this._hass || this._loading) return;
    const focus = this._focusSnapshot();
    this._loading = true;
    this._error = null;
    this._render();
    this._restoreFocus(focus);
    try {
      const msg = { type: "streaming_web_fr/catalog" };
      if (this._provider) msg.provider_id = this._provider;
      if (this._view === "catalog") {
        msg.category = this._catalogCategory || "all";
        msg.limit = Math.max(8, this._config.posters_par_lot);
      }
      if (this._view === "catalog" && this._query.trim()) msg.query = this._query.trim();
      if (append && cursor) msg.cursor = cursor;
      const response = await this._hass.callWS(msg);
      if (append) {
        const existing = this._data?.items || [];
        const seen = new Set(existing.map((item) => item.uid));
        const added = (response.items || []).filter((item) => {
          if (seen.has(item.uid)) return false;
          seen.add(item.uid);
          return true;
        });
        this._data = {
          ...this._data,
          ...response,
          items: [...existing, ...added],
          has_more: Boolean(response.has_more && response.next_cursor),
          next_cursor: response.has_more ? response.next_cursor : null,
        };
      } else {
        this._data = response;
      }
      this._loaded = true;
    } catch (err) {
      this._error = String(err?.message || err);
    } finally {
      const focus2 = this._focusSnapshot() || focus;
      this._loading = false;
      this._render();
      this._restoreFocus(focus2);
    }
  }

  async _advanceCatalog() {
    if (this._remoteLoading) return;
    const total = this._sortedItems().length;
    if (this._visible < total) {
      this._visible = Math.min(total, this._visible + this._config.posters_par_lot);
      this._render();
      return;
    }
    if (!this._data?.has_more || !this._data?.next_cursor) return;
    this._remoteLoading = true;
    const before = total;
    await this._load({ append: true, cursor: this._data.next_cursor });
    const after = this._sortedItems().length;
    this._visible = Math.min(after, before + this._config.posters_par_lot);
    this._remoteLoading = false;
    this._render();
  }

  async _syncRuntime() {
    if (!this._hass) return;
    const runtime = await this._hass.callWS({ type: "streaming_web_fr/runtime" });
    this._data = {
      ...(this._data || {}),
      providers: runtime.providers || [],
      players: runtime.players || [],
      config_source: runtime.config_source,
      config_path: runtime.config_path,
      config_issues: runtime.config_issues || [],
      version: runtime.version,
    };
  }

  _sortedItems() {
    const items = [...(this._data?.items || [])];
    if (this._sort === "title") {
      items.sort((a, b) => String(a.title || "").localeCompare(String(b.title || ""), "fr", { sensitivity: "base" }));
    } else if (this._sort === "year_desc") {
      items.sort((a, b) => Number(b.year || 0) - Number(a.year || 0));
    } else if (this._sort === "year_asc") {
      items.sort((a, b) => Number(a.year || 9999) - Number(b.year || 9999));
    } else if (this._sort === "provider") {
      items.sort((a, b) => String(a.provider_id || "").localeCompare(String(b.provider_id || "")));
    }
    return items;
  }

  _providerName(id) {
    return this._data?.providers?.find((p) => p.id === id)?.name || id || "Provider";
  }

  _sectionDefinitions() {
    return [
      { key: "latest", label: "Derniers ajouts" },
      { key: "featured", label: "À l'affiche" },
      { key: "animation", label: "Animations" },
      { key: "docs_shows", label: "Docs & Spectacles" },
    ];
  }

  _sectionLabel(key) {
    if (key === "all") return "Tout le catalogue";
    return this._sectionDefinitions().find((section) => section.key === key)?.label || "Catalogue";
  }

  _homeItems(key) {
    return (this._data?.items || [])
      .filter((item) => String(item?.extra?.home_section || "") === key)
      .sort((a, b) => Number(a?.extra?.home_rank ?? 9999) - Number(b?.extra?.home_rank ?? 9999));
  }

  _homeSection(section) {
    const items = this._homeItems(section.key).slice(0, this._config.home_section_count);
    if (!items.length) return "";
    return `
      <section class="home-section">
        <div class="section-head">
          <h2>${this._esc(section.label)}</h2>
          <button type="button" class="see-all" data-open-category="${this._esc(section.key)}">Voir tout <ha-icon icon="mdi:chevron-right"></ha-icon></button>
        </div>
        <div class="rail">
          ${items.map((item) => this._poster(item)).join("")}
        </div>
      </section>
    `;
  }

  _poster(item) {
    const year = item.year ? `<span class="year">${this._esc(item.year)}</span>` : "";
    const src = item.poster
      ? `<img loading="lazy" src="${this._esc(item.poster)}" alt="${this._esc(item.title)}">`
      : `<div class="poster-empty"><ha-icon icon="mdi:movie-open-outline"></ha-icon></div>`;
    return `
      <button class="poster" data-uid="${this._esc(item.uid)}" type="button">
        <div class="art">
          ${src}
          <span class="source">${this._esc(this._providerName(item.provider_id))}</span>
          ${year}
        </div>
        <div class="poster-title">${this._esc(item.title || "Sans titre")}</div>
      </button>
    `;
  }

  _popupHtml() {
    if (!this._popup && !this._popupLoading) return "";
    if (this._popupLoading) {
      return `
        <div class="overlay" data-close-popup>
          <div class="modal loading-modal">
            <ha-icon icon="mdi:loading" class="spin"></ha-icon>
            <span>Chargement…</span>
          </div>
        </div>`;
    }

    const item = this._popup || {};
    const poster = item.poster
      ? `<img class="modal-poster" src="${this._esc(item.poster)}" alt="">`
      : `<div class="modal-poster empty"><ha-icon icon="mdi:movie-open-outline"></ha-icon></div>`;
    const players = (this._data.players || []).map((player) => `
      <button class="play" type="button"
        data-play-provider="${this._esc(item.provider_id)}"
        data-play-item="${this._esc(item.provider_item_id)}"
        data-play-player="${this._esc(player.id)}">
        <ha-icon icon="mdi:vlc"></ha-icon>
        <span><strong>Voir sur VLC</strong><small>${this._esc(player.name)}</small></span>
      </button>
    `).join("");

    return `
      <div class="overlay" data-close-popup>
        <div class="modal" role="dialog" aria-modal="true">
          <button class="close" type="button" data-close-popup aria-label="Fermer">
            <ha-icon icon="mdi:close"></ha-icon>
          </button>
          <div class="modal-grid">
            ${poster}
            <div class="modal-copy">
              <div class="modal-source">${this._esc(this._providerName(item.provider_id))}</div>
              <h2>${this._esc(item.title || "")}</h2>
              ${item.year ? `<div class="modal-year">${this._esc(item.year)}</div>` : ""}
              <p>${this._esc(item.overview || "Aucun synopsis disponible.")}</p>
              ${this._config.debug ? `<div class="modal-debug">provider_item_id: ${this._esc(item.provider_item_id || "—")}<br>page_url: ${this._esc(item.page_url || "—")}</div>` : ""}
              <div class="play-list">
                ${players || '<div class="hint">Aucune destination Android TV configurée.</div>'}
              </div>
              ${this._playStatus ? `<div class="play-status">${this._esc(this._playStatus)}</div>` : ""}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _render() {
    if (!this.shadowRoot) return;
    const items = this._sortedItems();
    const visible = items.slice(0, this._visible);
    const hasLocalMore = visible.length < items.length;
    const hasRemoteMore = Boolean(this._data?.has_more && this._data?.next_cursor);
    const hasMore = hasLocalMore || hasRemoteMore;
    const providers = this._data?.providers || [];
    const catalogMode = this._view === "catalog";
    const homeSections = this._sectionDefinitions().map((section) => this._homeSection(section)).join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;font-family:var(--paper-font-body1_-_font-family,system-ui,sans-serif)}
        ha-card{overflow:hidden;border-radius:var(--ha-card-border-radius,16px);background:linear-gradient(145deg,rgba(18,18,24,.96),rgba(28,28,38,.94));color:#fff}
        .wrap{padding:16px}
        .head{display:flex;align-items:center;gap:12px;justify-content:space-between;margin-bottom:14px}
        h1{font-size:20px;line-height:1.2;margin:0;font-weight:700}
        .count{font-size:12px;color:rgba(255,255,255,.6)}
        .head-actions{display:flex;align-items:center;gap:8px}
        .refresh,.back{height:34px;border:0;border-radius:999px;background:rgba(255,255,255,.07);color:#fff;display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer}
        .refresh{width:34px}.back{padding:0 10px 0 8px}
        .home-section{margin:4px 0 22px}
        .section-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}
        .section-head h2{font-size:16px;margin:0}
        .see-all{display:flex;align-items:center;gap:2px;border:0;background:none;color:rgba(255,255,255,.72);cursor:pointer;padding:4px 0;font-size:12px}
        .see-all ha-icon{--mdc-icon-size:18px}
        .rail{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(125px,145px);gap:11px;overflow-x:auto;padding:2px 2px 8px;scrollbar-width:thin;overscroll-behavior-inline:contain}
        .explore{display:flex;justify-content:center;margin:6px 0 2px}
        .explore button{display:flex;align-items:center;gap:7px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.1);color:#fff;border-radius:999px;padding:10px 18px;cursor:pointer;font-weight:600}
        .toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
        .search-wrap{position:relative;flex:1 1 240px;min-width:180px}
        .search{box-sizing:border-box;width:100%;height:40px;border:1px solid rgba(255,255,255,.14);border-radius:12px;background:rgba(255,255,255,.07);color:#fff;padding:0 38px 0 12px;outline:none}
        .search:focus{border-color:rgba(255,255,255,.4);box-shadow:0 0 0 2px rgba(255,255,255,.08)}
        .search-icon{position:absolute;right:10px;top:9px;color:rgba(255,255,255,.55)}
        select{height:40px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.08);color:#fff;padding:0 10px}
        .providers,.categories{display:flex;gap:7px;overflow-x:auto;padding:2px 0 10px;scrollbar-width:none}
        .providers::-webkit-scrollbar,.categories::-webkit-scrollbar{display:none}
        .chip{white-space:nowrap;border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.06);color:#ddd;border-radius:999px;padding:7px 11px;cursor:pointer}
        .chip.active{background:rgba(255,255,255,.18);color:#fff;border-color:rgba(255,255,255,.35)}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(125px,1fr));gap:14px 11px}
        .poster{appearance:none;border:0;padding:0;background:none;color:inherit;text-align:left;cursor:pointer;min-width:0}
        .art{position:relative;aspect-ratio:2/3;border-radius:10px;overflow:hidden;background:rgba(255,255,255,.06);box-shadow:0 7px 20px rgba(0,0,0,.28);transition:transform .16s ease}
        .poster:hover .art{transform:translateY(-2px)}
        .art img{width:100%;height:100%;object-fit:cover;display:block}
        .poster-empty{height:100%;display:grid;place-items:center;color:rgba(255,255,255,.35)}
        .poster-empty ha-icon{--mdc-icon-size:42px}
        .source,.year{position:absolute;bottom:7px;border-radius:999px;font-size:10px;line-height:1;padding:5px 7px;background:rgba(0,0,0,.72);backdrop-filter:blur(8px)}
        .source{left:6px;max-width:68%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
        .year{right:6px}
        .poster-title{font-size:12px;font-weight:600;line-height:1.25;margin:7px 3px 0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
        .more{display:flex;justify-content:center;margin-top:18px}
        .more button{border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.08);color:#fff;border-radius:999px;padding:9px 18px;cursor:pointer}
        .state{display:flex;align-items:center;justify-content:center;gap:8px;min-height:160px;color:rgba(255,255,255,.7)}
        .error{color:#ffb4ab}
        .spin{animation:swfr-spin 1s linear infinite}
        @keyframes swfr-spin{to{transform:rotate(360deg)}}
        .overlay{position:fixed;inset:0;background:rgba(0,0,0,.72);display:grid;place-items:center;padding:16px;z-index:9999}
        .modal{position:relative;width:min(760px,96vw);max-height:88vh;overflow:auto;border:1px solid rgba(255,255,255,.14);border-radius:18px;background:linear-gradient(145deg,#18181f,#22222d);box-shadow:0 30px 80px rgba(0,0,0,.5);padding:18px}
        .loading-modal{width:auto;display:flex;align-items:center;gap:10px}
        .close{position:absolute;right:10px;top:10px;border:0;border-radius:999px;background:rgba(0,0,0,.46);color:#fff;width:38px;height:38px;display:grid;place-items:center;cursor:pointer;z-index:2}
        .modal-grid{display:grid;grid-template-columns:190px 1fr;gap:22px}
        .modal-poster{width:190px;aspect-ratio:2/3;object-fit:cover;border-radius:12px;background:rgba(255,255,255,.06)}
        .modal-poster.empty{display:grid;place-items:center}
        .modal-copy{padding:8px 6px 8px 0}
        .modal-copy h2{font-size:25px;margin:5px 0 3px}
        .modal-source{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:#aaa}
        .modal-year{color:#bbb;font-size:13px}
        .modal-copy p{color:#d0d0d6;line-height:1.5}
        .play-list{display:grid;gap:8px;margin-top:18px}
        .play{display:flex;align-items:center;gap:11px;border:1px solid rgba(246,119,55,.42);background:linear-gradient(135deg,rgba(246,119,55,.22),rgba(87,35,21,.38));color:#fff;border-radius:12px;padding:10px 12px;cursor:pointer;text-align:left}
        .play ha-icon{--mdc-icon-size:30px}
        .play span{display:flex;flex-direction:column}
        .play small{color:#cfcfd5;margin-top:2px}
        .play-status,.hint{margin-top:10px;color:#bbb;font-size:12px}
        .modal-debug{margin-top:12px;padding:8px;border:1px dashed rgba(255,255,255,.16);border-radius:8px;color:#aaa;font-size:10px;overflow-wrap:anywhere}
        .sentinel{height:1px}
        .debug{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px;padding:9px 10px;border:1px dashed rgba(255,255,255,.18);border-radius:10px;font-size:11px;color:#bbb}
        .debug strong{color:#fff}
        .debug-issue{color:#ffb4ab}
        @media(max-width:600px){
          .wrap{padding:12px}
          .grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px 7px}
          .rail{grid-auto-columns:minmax(105px,33vw)}
          .poster-title{font-size:11px}
          .modal-grid{grid-template-columns:105px 1fr;gap:14px}
          .modal-poster{width:105px}
          .modal-copy h2{font-size:20px;padding-right:28px}
        }
        @media(max-width:380px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
      </style>
      <ha-card>
        <div class="wrap">
          <div class="head">
            <div class="head-actions">
              ${catalogMode ? `<button class="back" type="button" data-home><ha-icon icon="mdi:chevron-left"></ha-icon>Accueil</button>` : ""}
              <h1>${this._esc(catalogMode ? this._sectionLabel(this._catalogCategory) : this._config.title)}</h1>
            </div>
            <div class="head-actions">
              <span class="count">${items.length} titre${items.length > 1 ? "s" : ""}</span>
              <button class="refresh" type="button" title="Rafraîchir" aria-label="Rafraîchir">
                <ha-icon icon="mdi:refresh"></ha-icon>
              </button>
            </div>
          </div>

          ${this._config.debug ? `
            <div class="debug">
              <strong>Debug</strong>
              <span>version: ${this._esc(this._data?.version || "unknown")}</span>
              <span>view: ${this._esc(this._view)}</span>
              <span>category: ${this._esc(this._catalogCategory)}</span>
              <span>source: ${this._esc(this._data?.config_source || "unknown")}</span>
              <span>items: ${items.length}</span>
              <span>page: ${this._esc(this._data?.page ?? 0)}</span>
              <span>has_more: ${hasRemoteMore}</span>
              <span>cursor: ${this._esc(this._data?.next_cursor || "—")}</span>
              <span>search: ${this._esc(this._data?.search_mode || "—")}</span>
              <span>players: ${(this._data?.players || []).length}</span>
              <span>ids: ${this._esc((this._data?.players || []).map((p) => p.id).join(", ") || "—")}</span>
              <span>config: ${this._esc(this._data?.config_path || "—")}</span>
              ${(this._data?.config_issues || []).map((issue) => `<span class="debug-issue">${this._esc(issue)}</span>`).join("")}
            </div>
          ` : ""}

          ${this._loading && !this._loaded ? `
            <div class="state"><ha-icon class="spin" icon="mdi:loading"></ha-icon>Chargement du catalogue…</div>
          ` : this._error ? `
            <div class="state error"><ha-icon icon="mdi:alert-circle-outline"></ha-icon>${this._esc(this._error)}</div>
          ` : !catalogMode ? `
            ${homeSections || `<div class="state"><ha-icon icon="mdi:movie-search-outline"></ha-icon>Aucune section détectée sur la page d'accueil.</div>`}
            <div class="explore">
              <button type="button" data-open-category="all"><ha-icon icon="mdi:view-grid-outline"></ha-icon>Explorer le catalogue</button>
            </div>
          ` : `
            <div class="categories">
              <button class="chip ${this._catalogCategory==="all"?"active":""}" type="button" data-category="all">Tout</button>
              ${this._sectionDefinitions().map((section) => `
                <button class="chip ${this._catalogCategory===section.key?"active":""}" type="button" data-category="${this._esc(section.key)}">${this._esc(section.label)}</button>
              `).join("")}
            </div>

            <div class="toolbar">
              ${this._config.searchbox ? `
                <div class="search-wrap">
                  <input class="search" type="search" value="${this._esc(this._query)}" placeholder="Rechercher un titre…">
                  <ha-icon class="search-icon" icon="mdi:magnify"></ha-icon>
                </div>` : ""}
              <select class="sort" aria-label="Tri">
                <option value="default" ${this._sort==="default"?"selected":""}>Ordre provider</option>
                <option value="title" ${this._sort==="title"?"selected":""}>Titre A–Z</option>
                <option value="year_desc" ${this._sort==="year_desc"?"selected":""}>Année ↓</option>
                <option value="year_asc" ${this._sort==="year_asc"?"selected":""}>Année ↑</option>
                <option value="provider" ${this._sort==="provider"?"selected":""}>Provider</option>
              </select>
            </div>

            <div class="providers">
              <button class="chip ${this._provider ? "" : "active"}" type="button" data-provider="">Tous</button>
              ${providers.map((p) => `
                <button class="chip ${this._provider===p.id?"active":""}" type="button" data-provider="${this._esc(p.id)}">
                  ${this._esc(p.name)}
                </button>
              `).join("")}
            </div>

            ${visible.length ? `
              <div class="grid">${visible.map((item) => this._poster(item)).join("")}</div>
              ${hasMore && !this._config.scroll_infini ? `
                <div class="more"><button type="button" data-more>${hasLocalMore ? `Voir ${Math.min(this._config.posters_par_lot, items.length-visible.length)} de plus` : "Charger la suite"}</button></div>
              ` : ""}
              ${hasMore && this._config.scroll_infini ? '<div class="sentinel"></div>' : ""}
              ${this._remoteLoading ? '<div class="state compact"><ha-icon class="spin" icon="mdi:loading"></ha-icon>Chargement de la suite…</div>' : ""}
            ` : `
              <div class="state"><ha-icon icon="mdi:movie-search-outline"></ha-icon>${hasRemoteMore ? "Recherche dans la suite du catalogue…" : "Aucun titre trouvé."}</div>
              ${hasRemoteMore && !this._config.scroll_infini ? '<div class="more"><button type="button" data-more>Rechercher dans la suite</button></div>' : ""}
              ${hasRemoteMore && this._config.scroll_infini ? '<div class="sentinel"></div>' : ""}
            `}
          `}
        </div>
      </ha-card>
      ${this._popupHtml()}
    `;

    this._wire();
  }

  _wire() {
    const root = this.shadowRoot;

    root.querySelector("[data-home]")?.addEventListener("click", () => {
      this._view = "home";
      this._catalogCategory = "all";
      this._query = "";
      this._visible = this._config.posters_par_lot;
      this._loaded = false;
      this._load();
    });

    root.querySelectorAll("[data-open-category]").forEach((button) => {
      button.addEventListener("click", () => {
        this._view = "catalog";
        this._catalogCategory = button.dataset.openCategory || "all";
        this._query = "";
        this._visible = this._config.posters_par_lot;
        this._loaded = false;
        this._load();
      });
    });

    root.querySelectorAll("[data-category]").forEach((button) => {
      button.addEventListener("click", () => {
        this._catalogCategory = button.dataset.category || "all";
        this._query = "";
        this._visible = this._config.posters_par_lot;
        this._loaded = false;
        this._load();
      });
    });

    root.querySelectorAll("[data-provider]").forEach((button) => {
      button.addEventListener("click", () => {
        this._provider = button.dataset.provider || "";
        this._visible = this._config.posters_par_lot;
        this._load();
      });
    });

    const search = root.querySelector(".search");
    if (search) {
      const block = (event) => event.stopPropagation();
      search.addEventListener("keydown", block);
      search.addEventListener("keyup", block);
      search.addEventListener("keypress", block);
      search.addEventListener("input", (event) => {
        event.stopPropagation();
        this._query = event.target.value;
        clearTimeout(this._searchTimer);
        this._searchTimer = setTimeout(() => {
          this._visible = this._config.posters_par_lot;
          this._load();
        }, 280);
      });
    }

    root.querySelector(".refresh")?.addEventListener("click", async () => {
      this._loaded = false;
      await this._load();
    });

    const sort = root.querySelector(".sort");
    sort?.addEventListener("change", () => {
      this._sort = sort.value;
      this._render();
    });

    root.querySelector("[data-more]")?.addEventListener("click", () => this._advanceCatalog());

    root.querySelectorAll("[data-uid]").forEach((button) => {
      button.addEventListener("click", () => {
        const item = (this._data.items || []).find((entry) => entry.uid === button.dataset.uid);
        if (item) this._open(item);
      });
    });

    root.querySelectorAll("[data-close-popup]").forEach((node) => {
      node.addEventListener("click", (event) => {
        if (event.target === node || node.classList.contains("close")) {
          this._popup = null;
          this._popupLoading = false;
          this._playStatus = "";
          this._render();
        }
      });
    });

    root.querySelector(".modal")?.addEventListener("click", (event) => event.stopPropagation());

    root.querySelectorAll("[data-play-player]").forEach((button) => {
      button.addEventListener("click", () => this._play(button));
    });

    if (this._observer) {
      this._observer.disconnect();
      this._observer = null;
    }
    const sentinel = root.querySelector(".sentinel");
    if (sentinel && this._config.scroll_infini) {
      this._observer = new IntersectionObserver((entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        this._advanceCatalog();
      }, { rootMargin: "240px" });
      this._observer.observe(sentinel);
    }
  }

  async _open(item) {
    this._popupLoading = true;
    this._popup = null;
    this._playStatus = "";
    this._render();
    try {
      await this._syncRuntime();
      this._popup = await this._hass.callWS({
        type: "streaming_web_fr/details",
        provider_id: item.provider_id,
        provider_item_id: String(item.provider_item_id),
        ...(item.page_url ? { page_url: item.page_url } : {}),
      });
    } catch (err) {
      this._popup = { ...item, overview: String(err?.message || err) };
    } finally {
      this._popupLoading = false;
      this._render();
    }
  }

  async _play(button) {
    if (!this._hass) return;
    const providerId = button.dataset.playProvider;
    const itemId = button.dataset.playItem;
    const playerId = button.dataset.playPlayer;
    this._playStatus = "Résolution du flux et lancement de VLC…";
    this._render();
    try {
      const msg = {
        type: "streaming_web_fr/play",
        provider_id: providerId,
        provider_item_id: String(itemId),
        player_id: playerId,
      };
      if (this._popup?.page_url) msg.page_url = this._popup.page_url;
      await this._hass.callWS(msg);
      this._playStatus = "Commande envoyée à VLC.";
    } catch (err) {
      this._playStatus = `Erreur : ${String(err?.message || err)}`;
    }
    this._render();
  }
}

customElements.define("streaming-web-fr-card", StreamingWebFrCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "streaming-web-fr-card",
  name: "Streaming Web FR",
  description: "Catalogue multi-provider avec lecture VLC sur Android TV",
  preview: true,
});
