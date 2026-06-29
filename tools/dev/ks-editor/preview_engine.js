(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.KSPreview = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const VIRTUAL_WIDTH = 1440;
  const VIRTUAL_HEIGHT = 1080;
  const LAYER_ORDER = ["torso", "brow", "cheek", "eye", "mouth", "effect", "accessory"];
  const FACE_PARTS = new Set(["brow", "cheek", "eye", "mouth"]);
  const CHAR_CODES = { "桃子": "MMK", "沙那子": "SNK", "サナコ": "SNK", "増田": "MST" };

  function number(value, fallback) {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function normalizeSpace(value) {
    return String(value || "").replace(/\u3000/g, " ").trim();
  }

  function parseTag(source) {
    let inner = normalizeSpace(source);
    if (inner.startsWith("[") && inner.endsWith("]")) inner = inner.slice(1, -1).trim();
    if (inner.startsWith("@")) inner = inner.slice(1).trim();
    if (!inner) return null;
    const nameMatch = inner.match(/^([^\s]+)/);
    if (!nameMatch) return null;
    let name = nameMatch[1].toLowerCase().replace(/-/g, "_");
    if (/^choice_\d+$/.test(name)) name = "choice";
    const params = {};
    const rest = inner.slice(nameMatch[0].length);
    const attr = /([^\s=]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s]+))/g;
    let match;
    while ((match = attr.exec(rest))) {
      params[match[1].toLowerCase()] = match[2] ?? match[3] ?? match[4] ?? "";
    }
    const bare = rest.replace(attr, " ").trim();
    if (bare) params.value = bare;
    return { type: name, params, raw: source };
  }

  function parseScenario(text) {
    const lines = String(text || "").replace(/\r\n?/g, "\n").split("\n");
    const steps = [];
    let speaker = "";
    let pendingActions = [];
    let pendingStart = null;

    const emit = (line, body, actions, extra = {}) => {
      steps.push({
        index: steps.length,
        sourceLine: line,
        startLine: pendingStart == null ? line : Math.min(pendingStart, line),
        speaker,
        body: body || "",
        actions: actions || [],
        scrollStop: !!extra.scrollStop,
        memo: extra.memo || "",
      });
      pendingStart = null;
    };

    for (let index = 0; index < lines.length; index += 1) {
      const trimmed = normalizeSpace(lines[index]);
      if (!trimmed || trimmed.startsWith(";")) continue;

      const speakerMatch = trimmed.match(/^\/\/(.*?)\/\/$/);
      if (speakerMatch) {
        speaker = speakerMatch[1].trim();
        if (pendingStart == null) pendingStart = index;
        continue;
      }

      if (trimmed.startsWith("*")) {
        pendingActions.push({ type: "label", params: { value: trimmed.slice(1) }, raw: trimmed });
        if (pendingStart == null) pendingStart = index;
        continue;
      }

      const dialogueMatch = trimmed.match(/「([\s\S]*)」/);
      if (dialogueMatch) {
        const inlineTags = [...trimmed.matchAll(/\[[^\]]+\]/g)].map((m) => parseTag(m[0])).filter(Boolean);
        const scrollStop = inlineTags.some((tag) => tag.type === "scroll_stop");
        const actions = pendingActions.concat(inlineTags.filter((tag) => tag.type !== "scroll_stop"));
        emit(index, dialogueMatch[1], actions, { scrollStop });
        pendingActions = [];
        continue;
      }

      if ((trimmed.startsWith("[") && trimmed.endsWith("]")) || trimmed.startsWith("@")) {
        const tag = parseTag(trimmed);
        if (!tag) continue;
        if (tag.type === "scroll_stop") {
          if (steps.length) steps[steps.length - 1].scrollStop = true;
          else pendingActions.push(tag);
          continue;
        }
        if (pendingStart == null) pendingStart = index;
        pendingActions.push(tag);
        if (tag.type === "choice") {
          emit(index, "", pendingActions);
          pendingActions = [];
        }
      }
    }

    if (pendingActions.length) emit(lines.length - 1, "", pendingActions);
    return { lines, steps };
  }

  function initialState() {
    return {
      background: null,
      characters: {},
      text: { speaker: "", body: "" },
      choices: [],
      fade: { color: "black", opacity: 0 },
      audio: { bgm: "", se: "" },
      labels: [],
      warnings: [],
    };
  }

  function applyAction(state, action) {
    const type = action.type;
    const p = action.params || {};
    if (type === "label") {
      state.labels.push(p.value || "");
      return;
    }
    if (type === "bg" || type === "bg_show" || type === "background") {
      state.background = {
        storage: p.storage || p.value || "",
        x: number(p.bg_x ?? p.x, 0.5),
        y: number(p.bg_y ?? p.y, 0.5),
        zoom: number(p.bg_zoom ?? p.zoom, 1),
      };
      return;
    }
    if (type === "bg_move") {
      const old = state.background || { storage: "", x: 0.5, y: 0.5, zoom: 1 };
      state.background = {
        storage: p.storage || old.storage,
        x: old.x + number(p.bg_left ?? p.left, 0),
        y: old.y + number(p.bg_top ?? p.top, 0),
        zoom: number(p.bg_zoom ?? p.zoom, old.zoom),
      };
      return;
    }
    if (type === "resetlaypos") {
      state.characters = {};
      return;
    }
    if (type === "chara_show") {
      const name = p.name || p.target || p.torso || "character";
      state.characters[name] = {
        name,
        torso: p.torso || "",
        brow: p.brow || "",
        cheek: p.cheek || "",
        eye: p.eye || "",
        mouth: p.mouth || "",
        effect: p.effect || "",
        accessory: p.accessory || "",
        x: number(p.x, 0.5),
        y: number(p.y, 0.5),
        size: number(p.size, 1),
        blink: String(p.blink ?? "true").toLowerCase() !== "false",
      };
      return;
    }
    if (type === "chara_shift") {
      const name = p.name || p.target || Object.keys(state.characters)[0] || "character";
      const current = state.characters[name] || { name, x: 0.5, y: 0.5, size: 1 };
      for (const key of LAYER_ORDER) {
        if (Object.prototype.hasOwnProperty.call(p, key) && p[key] !== "") current[key] = p[key];
      }
      for (const key of ["x", "y", "size"]) {
        if (Object.prototype.hasOwnProperty.call(p, key) && p[key] !== "") current[key] = number(p[key], current[key]);
      }
      state.characters[name] = current;
      return;
    }
    if (type === "chara_move") {
      const name = p.name || p.target || Object.keys(state.characters)[0];
      if (!name || !state.characters[name]) return;
      const current = state.characters[name];
      current.x += number(p.left, 0);
      current.y += number(p.top, 0);
      current.size = number(p.zoom, current.size);
      return;
    }
    if (type === "chara_hide") {
      const name = p.name || p.target || Object.keys(state.characters)[0];
      if (name) delete state.characters[name];
      return;
    }
    if (type === "fadeout") {
      state.fade = { color: p.color || "black", opacity: 1 };
      return;
    }
    if (type === "fadein") {
      state.fade.opacity = 0;
      return;
    }
    if (type === "choice") {
      state.choices = Object.keys(p).filter((key) => /^option\d+$/i.test(key)).sort().map((key) => p[key]);
      return;
    }
    if (type === "bgm" || type === "bgmstart") {
      state.audio.bgm = p.bgm || p.storage || p.value || "";
      return;
    }
    if (type === "bgmstop") {
      state.audio.bgm = "";
      return;
    }
    if (type === "se") {
      state.audio.se = p.se || p.storage || p.value || "";
      return;
    }
    if (!["if", "endif", "flag_set", "event_control"].includes(type)) {
      state.warnings.push(`未対応タグ: ${type}`);
    }
  }

  function buildState(parsed, stepIndex) {
    const state = initialState();
    const last = Math.min(Math.max(number(stepIndex, 0), 0), Math.max(parsed.steps.length - 1, 0));
    for (let index = 0; index <= last && index < parsed.steps.length; index += 1) {
      const step = parsed.steps[index];
      state.choices = [];
      for (const action of step.actions) applyAction(state, action);
      if (step.body) state.text = { speaker: step.speaker || "", body: step.body };
    }
    state.stepIndex = last;
    return state;
  }

  function classifyStem(stem) {
    if (stem.includes("_CGF")) {
      if (stem.includes("_BRO")) return "brow";
      if (stem.includes("_EYE")) return "eye";
      if (stem.includes("_MOU")) return "mouth";
      if (stem.includes("_CHE")) return "cheek";
    }
    if (stem.includes("_T")) return "torso";
    if (stem.includes("_F")) {
      if (stem.includes("_BRO")) return "brow";
      if (stem.includes("_EYE")) return "eye";
      if (stem.includes("_MOU")) return "mouth";
      if (stem.includes("_CHE")) return "cheek";
    }
    if (/_E\d/.test(stem)) return "effect";
    if (/_A\d/.test(stem)) return "accessory";
    return null;
  }

  class AssetIndex {
    constructor(options = {}) {
      this.repo = options.repo || "pikupiku-official/mo-kiss";
      this.branch = options.branch || "main";
      this.apiBase = options.apiBase || `https://api.github.com/repos/${this.repo}/contents/`;
      this.rawBase = options.rawBase || `https://raw.githubusercontent.com/${this.repo}/${this.branch}/`;
      this.fetch = options.fetch || (typeof fetch !== "undefined" ? fetch.bind(globalThis) : null);
      this.backgrounds = null;
      this.charDirs = null;
      this.characters = new Map();
      this.images = new Map();
    }

    async list(path) {
      if (!this.fetch) throw new Error("fetch is unavailable");
      const separator = this.apiBase.includes("?") ? "&" : "?";
      const response = await this.fetch(`${this.apiBase}${path}${separator}ref=${encodeURIComponent(this.branch)}`, {
        headers: { Accept: "application/vnd.github+json" },
      });
      if (!response.ok) throw new Error(`asset list HTTP ${response.status}`);
      return response.json();
    }

    async loadBackgrounds() {
      if (!this.backgrounds) {
        const items = await this.list("images/BG");
        this.backgrounds = items.filter((item) => item.type === "file").map((item) => ({
          name: item.name,
          stem: item.name.replace(/\.[^.]+$/, ""),
          url: item.download_url || `${this.rawBase}${item.path}`,
        }));
      }
      return this.backgrounds;
    }

    async loadCharDirs() {
      if (!this.charDirs) {
        const items = await this.list("images");
        this.charDirs = items.filter((item) => item.type === "dir" && /^\d{2}[A-Z]{3}$/.test(item.name));
      }
      return this.charDirs;
    }

    codeFor(character) {
      const explicit = LAYER_ORDER.map((key) => character && character[key]).find((value) => /^[A-Z]{3}_/.test(value || ""));
      if (explicit) return explicit.slice(0, 3);
      return CHAR_CODES[character && character.name] || "";
    }

    async loadCharacter(code) {
      if (!code) return [];
      if (!this.characters.has(code)) {
        const dirs = await this.loadCharDirs();
        const dir = dirs.find((item) => item.name.endsWith(code));
        if (!dir) {
          this.characters.set(code, []);
        } else {
          const items = await this.list(dir.path);
          this.characters.set(code, items.filter((item) => item.type === "file").map((item) => {
            const stem = item.name.replace(/\.[^.]+$/, "");
            return { name: item.name, stem, part: classifyStem(stem), url: item.download_url || `${this.rawBase}${item.path}` };
          }));
        }
      }
      return this.characters.get(code);
    }

    async resolveBackground(storage) {
      if (!storage) return null;
      const items = await this.loadBackgrounds();
      const wanted = storage.toLowerCase().replace(/\.[^.]+$/, "");
      return items.find((item) => item.stem.toLowerCase() === wanted)
        || items.find((item) => item.stem.toLowerCase().endsWith(`.${wanted}`))
        || items.find((item) => item.stem.toLowerCase().includes(wanted))
        || null;
    }

    async partOptions(code, part, torso = "") {
      const items = (await this.loadCharacter(code)).filter((item) => item.part === part);
      const match = String(torso).match(/_T(\d+)/);
      if (!match || part === "torso") return items;
      const token = FACE_PARTS.has(part) ? `_F${match[1]}_` : part === "effect" ? `_E${match[1]}_` : `_A${match[1]}_`;
      const filtered = items.filter((item) => item.stem.includes(token));
      return filtered.length ? filtered : items;
    }

    async resolvePart(code, part, id, torso = "") {
      const options = await this.partOptions(code, part, torso);
      if (!options.length) return null;
      if (!id && part === "torso") return options[0];
      if (!id) return null;
      const wanted = id.toLowerCase().replace(/\.[^.]+$/, "");
      const exact = options.find((item) => item.stem.toLowerCase() === wanted);
      if (exact) return exact;
      const legacyNumber = wanted.match(/(\d+)$/)?.[1]?.padStart(2, "0");
      const token = part === "eye" ? "EYE" : part === "mouth" ? "MOU" : part === "brow" ? "BRO" : part === "cheek" ? "CHE" : "";
      if (legacyNumber && token) {
        return options.find((item) => item.stem.includes(`_${token}${legacyNumber}_00`))
          || options.find((item) => item.stem.includes(`_${token}${legacyNumber}_`))
          || null;
      }
      return options.find((item) => item.stem.toLowerCase().includes(wanted)) || null;
    }

    async image(url) {
      if (!url) return null;
      if (!this.images.has(url)) {
        this.images.set(url, new Promise((resolve, reject) => {
          const image = new Image();
          image.crossOrigin = "anonymous";
          image.onload = () => resolve(image);
          image.onerror = () => reject(new Error(`画像を読み込めません: ${url}`));
          image.src = url;
        }));
      }
      return this.images.get(url);
    }
  }

  class CanvasRenderer {
    constructor(canvas, assets) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.assets = assets;
      this.canvas.width = VIRTUAL_WIDTH;
      this.canvas.height = VIRTUAL_HEIGHT;
    }

    async draw(state) {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
      ctx.fillStyle = "#141428";
      ctx.fillRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
      await this.drawBackground(state.background);
      for (const character of Object.values(state.characters)) await this.drawCharacter(character);
      this.drawText(state.text, state.choices);
      if (state.fade.opacity) {
        ctx.globalAlpha = state.fade.opacity;
        ctx.fillStyle = state.fade.color || "black";
        ctx.fillRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
        ctx.globalAlpha = 1;
      }
    }

    async drawBackground(background) {
      if (!background || !background.storage) return;
      const item = await this.assets.resolveBackground(background.storage);
      if (!item) return;
      const image = await this.assets.image(item.url);
      const cover = Math.max(VIRTUAL_WIDTH / image.width, VIRTUAL_HEIGHT / image.height) * background.zoom;
      const width = image.width * cover;
      const height = image.height * cover;
      const x = VIRTUAL_WIDTH * background.x - width / 2;
      const y = VIRTUAL_HEIGHT * background.y - height / 2;
      this.ctx.drawImage(image, x, y, width, height);
    }

    async drawCharacter(character) {
      const code = this.assets.codeFor(character);
      if (!code) return;
      const resolved = {};
      for (const part of LAYER_ORDER) resolved[part] = await this.assets.resolvePart(code, part, character[part], character.torso);
      const torsoItem = resolved.torso;
      if (!torsoItem) return;
      const torsoImage = await this.assets.image(torsoItem.url);
      const height = VIRTUAL_HEIGHT * number(character.size, 1);
      const width = torsoImage.width / torsoImage.height * height;
      const left = VIRTUAL_WIDTH * number(character.x, 0.5) - width / 2;
      const top = VIRTUAL_HEIGHT * number(character.y, 0.5) - height / 2;
      for (const part of LAYER_ORDER) {
        const item = resolved[part];
        if (!item) continue;
        const image = part === "torso" ? torsoImage : await this.assets.image(item.url);
        const partWidth = image.width / torsoImage.width * width;
        const partHeight = image.height / torsoImage.height * height;
        this.ctx.drawImage(image, left + (width - partWidth) / 2, top + (height - partHeight) / 2, partWidth, partHeight);
      }
    }

    drawText(text, choices) {
      const ctx = this.ctx;
      if ((!text || !text.body) && !(choices && choices.length)) return;
      const x = 50;
      const y = 742;
      const width = 1340;
      const height = 288;
      ctx.fillStyle = "rgba(18, 43, 70, .88)";
      ctx.fillRect(x, y, width, height);
      ctx.strokeStyle = "rgba(130, 185, 230, .7)";
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, width, height);
      ctx.fillStyle = "#fff";
      ctx.font = '45px "Yu Gothic", "Meiryo", sans-serif';
      if (text && text.speaker) ctx.fillText(text.speaker, 92, 814);
      const body = choices && choices.length ? choices.map((value, index) => `${index + 1}. ${value}`).join("　") : text.body;
      this.wrapText(body, 294, 814, 1040, 62, 3);
    }

    wrapText(text, x, y, maxWidth, lineHeight, maxLines) {
      const ctx = this.ctx;
      let line = "";
      let row = 0;
      for (const char of String(text || "")) {
        const candidate = line + char;
        if (ctx.measureText(candidate).width > maxWidth && line) {
          ctx.fillText(line, x, y + row * lineHeight);
          row += 1;
          if (row >= maxLines) return;
          line = char;
        } else line = candidate;
      }
      if (line && row < maxLines) ctx.fillText(line, x, y + row * lineHeight);
    }

    async drawComposite(fields, code) {
      const character = { name: "", x: 0.5, y: 0.5, size: 0.92, ...fields };
      if (!this.assets.codeFor(character) && code) character.torso = character.torso || `${code}_`;
      this.ctx.clearRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
      this.ctx.fillStyle = "#1e1e1e";
      this.ctx.fillRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
      await this.drawCharacter(character);
    }
  }

  return {
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    LAYER_ORDER,
    CHAR_CODES,
    parseTag,
    parseScenario,
    buildState,
    applyAction,
    classifyStem,
    AssetIndex,
    CanvasRenderer,
  };
});
