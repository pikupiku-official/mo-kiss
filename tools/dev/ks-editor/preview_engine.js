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
  const FEMALE_CHARACTERS = new Set(["桃子", "サナコ", "沙那子", "烏丸神無", "桔梗美鈴", "宮月深依里", "伊織紅"]);
  const RENDER_CONFIG = Object.freeze({
    textStartX: 298,
    textStartY: 798,
    nameStartX: 95,
    nameStartY: 798,
    fontSize: 45,
    dateFontSize: 43,
    maxCharsPerLine: 20,
    maxDisplayLines: 3,
    charSpacing: 2,
    glyphHeight: 63,
    lineHeight: 69,
    rubyFontSize: 18,
    rubyHeight: 9,
    stretchFactor: 1.05,
    pixelateFactor: 2,
    shadowOffsetX: 6,
    shadowOffsetY: 6,
    textColor: "rgb(255,255,255)",
    femaleTextColor: "rgb(255,200,255)",
    textBoxX: 50,
    textBoxY: 742,
    textBoxWidth: 1340,
    textBoxHeight: 288,
  });

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
    let hasDialogueSinceStop = false;

    const emit = (line, body, actions, extra = {}) => {
      steps.push({
        index: steps.length,
        sourceLine: line,
        startLine: pendingStart == null ? line : Math.min(pendingStart, line),
        speaker,
        body: body || "",
        actions: actions || [],
        scrollStop: !!extra.scrollStop,
        scroll: !!extra.scroll,
        forceFemale: !!extra.forceFemale,
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
        const forceFemale = inlineTags.some((tag) => tag.type === "female");
        const actions = pendingActions.concat(inlineTags.filter((tag) => !["scroll_stop", "female"].includes(tag.type)));
        emit(index, dialogueMatch[1], actions, {
          scrollStop,
          scroll: hasDialogueSinceStop && !scrollStop,
          forceFemale,
        });
        pendingActions = [];
        hasDialogueSinceStop = !scrollStop;
        continue;
      }

      if ((trimmed.startsWith("[") && trimmed.endsWith("]")) || trimmed.startsWith("@")) {
        const tag = parseTag(trimmed);
        if (!tag) continue;
        if (tag.type === "scroll_stop") {
          if (steps.length) steps[steps.length - 1].scrollStop = true;
          else pendingActions.push(tag);
          hasDialogueSinceStop = false;
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
      textBlocks: [],
      previousText: null,
      scrollMode: false,
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
      const zoom = Math.max(0.5, Math.min(3, number(p.bg_zoom ?? p.zoom, 1)));
      const x = Math.max(0, Math.min(1, number(p.bg_x ?? p.x, 0.5)));
      const y = Math.max(0, Math.min(1, number(p.bg_y ?? p.y, 0.5)));
      const maxOffsetX = zoom >= 1 ? VIRTUAL_WIDTH * (zoom - 1) / 2 : VIRTUAL_WIDTH * (1 - zoom) / 4;
      const maxOffsetY = zoom >= 1 ? VIRTUAL_HEIGHT * (zoom - 1) / 2 : VIRTUAL_HEIGHT * (1 - zoom) / 4;
      state.background = {
        storage: p.storage || p.value || "",
        x,
        y,
        offsetX: (x - 0.5) * maxOffsetX * 2,
        offsetY: (y - 0.5) * maxOffsetY * 2,
        zoom,
      };
      return;
    }
    if (type === "bg_move") {
      const old = state.background || { storage: "", x: 0.5, y: 0.5, offsetX: 0, offsetY: 0, zoom: 1 };
      const zoom = Math.max(0.5, Math.min(3, number(p.bg_zoom ?? p.zoom, old.zoom)));
      const left = Math.max(-0.3, Math.min(0.3, number(p.bg_left ?? p.left, 0)));
      const top = Math.max(-0.3, Math.min(0.3, number(p.bg_top ?? p.top, 0)));
      const maxMoveX = zoom >= 1 ? VIRTUAL_WIDTH * (zoom - 1) / 2 : VIRTUAL_WIDTH * (1 - zoom) / 4;
      const maxMoveY = zoom >= 1 ? VIRTUAL_HEIGHT * (zoom - 1) / 2 : VIRTUAL_HEIGHT * (1 - zoom) / 4;
      const maxFinalX = zoom >= 1 ? VIRTUAL_WIDTH * (zoom - 1) / 2 : VIRTUAL_WIDTH * (1 - zoom) / 4;
      const maxFinalY = zoom >= 1 ? VIRTUAL_HEIGHT * (zoom - 1) / 2 : VIRTUAL_HEIGHT * (1 - zoom) / 4;
      state.background = {
        storage: p.storage || old.storage,
        x: old.x,
        y: old.y,
        offsetX: Math.max(-maxFinalX, Math.min(maxFinalX, (old.offsetX || 0) + left * maxMoveX * 2)),
        offsetY: Math.max(-maxFinalY, Math.min(maxFinalY, (old.offsetY || 0) + top * maxMoveY * 2)),
        zoom,
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
      current.effect = p.effect || "";
      for (const key of LAYER_ORDER) {
        if (key === "effect") continue;
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
      if (index > 0 && parsed.steps[index - 1].scrollStop) {
        state.scrollMode = false;
        state.textBlocks = [];
        state.previousText = null;
      }
      state.choices = [];
      for (const action of step.actions) applyAction(state, action);
      if (step.body) {
        const block = {
          speaker: step.speaker || "",
          body: step.body,
          forceFemale: !!step.forceFemale,
        };
        if (state.scrollMode) {
          state.textBlocks.push(block);
        } else if (step.scroll && state.previousText) {
          state.textBlocks = [state.previousText, block];
          state.scrollMode = true;
        } else {
          state.textBlocks = [block];
        }
        if (state.textBlocks.length > 3) state.textBlocks = state.textBlocks.slice(-3);
        state.previousText = block;
        state.text = block;
      }
    }
    state.stepIndex = last;
    return state;
  }

  function findStepForSourceLine(parsed, sourceLine) {
    const steps = parsed && Array.isArray(parsed.steps) ? parsed.steps : [];
    if (!steps.length) return 0;
    const line = Math.max(0, number(sourceLine, 0));
    const exact = steps.findIndex((step) => step.sourceLine === line);
    if (exact >= 0) return exact;
    const containing = steps
      .map((step, index) => ({ step, index }))
      .filter(({ step }) => step.startLine <= line && line <= step.sourceLine)
      .sort((a, b) => (a.step.sourceLine - a.step.startLine) - (b.step.sourceLine - b.step.startLine));
    if (containing.length) return containing[0].index;
    let best = 0;
    let distance = Infinity;
    steps.forEach((step, index) => {
      const nextDistance = Math.abs(step.sourceLine - line);
      if (nextDistance < distance) {
        best = index;
        distance = nextDistance;
      }
    });
    return best;
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
      this.ui = null;
      this.charDirs = null;
      this.characters = new Map();
      this.images = new Map();
      this.timeTextPromise = null;
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

    async loadUI() {
      if (!this.ui) {
        const directories = ["images/UI", "images/legacy"];
        const collected = [];
        for (const directory of directories) {
          try {
            const items = await this.list(directory);
            collected.push(...items);
          } catch (error) {
            // Legacy UI assets are optional.
          }
        }
        this.ui = collected.filter((item) => item.type === "file").map((item) => ({
          name: item.name,
          stem: item.name.replace(/\.[^.]+$/, ""),
          url: item.download_url || `${this.rawBase}${item.path}`,
        }));
      }
      return this.ui;
    }

    async resolveUI(key) {
      const items = await this.loadUI();
      const wanted = String(key || "").toLowerCase();
      return items.find((item) => item.stem.toLowerCase() === wanted)
        || items.find((item) => item.stem.toLowerCase() === `ui.${wanted}`)
        || null;
    }

    fontUrl(fileName) {
      return `${this.rawBase}fonts/${encodeURIComponent(fileName)}`;
    }

    async loadTimeText() {
      if (!this.timeTextPromise) {
        this.timeTextPromise = (async () => {
          const response = await this.fetch(`${this.rawBase}data/current_state/time_state.json`);
          if (!response.ok) throw new Error(`time state HTTP ${response.status}`);
          const value = await response.json();
          const weekdays = ["月", "火", "水", "木", "金", "土", "日"];
          return `${value.year || 1999}年${value.month || 5}月${value.day || 31}日(${weekdays[value.weekday || 0]}) ${value.period || "朝"}`;
        })().catch(() => "1999年5月31日(月) 朝");
      }
      return this.timeTextPromise;
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
      const raw = storage.toLowerCase().trim();
      // KSの背景ID自体にドットを含む（例: test.bg.9901）。
      // 画像拡張子だけを除き、数値末尾を拡張子と誤認しない。
      const wanted = raw.replace(/\.(?:png|jpe?g|webp)$/i, "");
      return items.find((item) => item.stem.toLowerCase() === raw)
        || items.find((item) => item.stem.toLowerCase() === wanted)
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
      this.fontReady = null;
      this.glyphCache = new Map();
      this.tintedTextBox = null;
    }

    createCanvas(width, height) {
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.ceil(width));
      canvas.height = Math.max(1, Math.ceil(height));
      return canvas;
    }

    async ready() {
      if (this.fontReady) return this.fontReady;
      this.fontReady = (async () => {
        if (typeof FontFace === "undefined" || typeof document === "undefined") return;
        const definitions = [
          ["MokissText", "MPLUS1p-Medium.ttf", "500"],
          ["MokissName", "MPLUS1p-Bold.ttf", "700"],
          ["MokissDate", "MPLUS1p-Regular.ttf", "400"],
        ];
        for (const [family, file, weight] of definitions) {
          const face = new FontFace(family, `url("${this.assets.fontUrl(file)}")`, { weight });
          await face.load();
          document.fonts.add(face);
        }
        await document.fonts.ready;
      })().catch((error) => {
        console.warn("プレビューフォントの読み込みに失敗しました", error);
      });
      return this.fontReady;
    }

    async draw(state) {
      await this.ready();
      const ctx = this.ctx;
      ctx.clearRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
      ctx.fillStyle = "#000";
      ctx.fillRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
      await this.drawBackground(state.background);
      for (const character of Object.values(state.characters)) await this.drawCharacter(character);
      if (state.fade.opacity) {
        ctx.globalAlpha = state.fade.opacity;
        ctx.fillStyle = state.fade.color || "black";
        ctx.fillRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
        ctx.globalAlpha = 1;
      }
      await this.drawUI();
      if (state.choices && state.choices.length) this.drawChoices(state.choices);
      else this.drawDialogue(state.textBlocks && state.textBlocks.length ? state.textBlocks : [state.text]);
      this.drawDate(state.timeText || await this.assets.loadTimeText());
    }

    async drawBackground(background) {
      if (!background || !background.storage) return;
      const item = await this.assets.resolveBackground(background.storage);
      if (!item) return;
      const image = await this.assets.image(item.url);
      const zoom = number(background.zoom, 1);
      const width = VIRTUAL_WIDTH * zoom;
      const height = VIRTUAL_HEIGHT * zoom;
      if (zoom < 1) {
        this.ctx.fillStyle = "rgb(20,20,40)";
        this.ctx.fillRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);
      }
      const x = VIRTUAL_WIDTH / 2 - width / 2 + number(background.offsetX, 0);
      const y = VIRTUAL_HEIGHT / 2 - height / 2 + number(background.offsetY, 0);
      // ImageManager は背景を先に画面サイズへ変形してからズームする。
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

    async drawUI() {
      const [textBoxItem, autoItem, skipItem] = await Promise.all([
        this.assets.resolveUI("text-box"),
        this.assets.resolveUI("auto"),
        this.assets.resolveUI("skip"),
      ]);
      if (textBoxItem) {
        const image = await this.assets.image(textBoxItem.url);
        if (!this.tintedTextBox) {
          const tint = this.createCanvas(RENDER_CONFIG.textBoxWidth, RENDER_CONFIG.textBoxHeight);
          const tctx = tint.getContext("2d");
          tctx.drawImage(image, 0, 0, tint.width, tint.height);
          tctx.globalCompositeOperation = "multiply";
          tctx.fillStyle = "rgb(40,83,120)";
          tctx.fillRect(0, 0, tint.width, tint.height);
          tctx.globalCompositeOperation = "destination-in";
          tctx.drawImage(image, 0, 0, tint.width, tint.height);
          tctx.globalCompositeOperation = "source-over";
          this.tintedTextBox = tint;
        }
        this.ctx.drawImage(this.tintedTextBox, RENDER_CONFIG.textBoxX, RENDER_CONFIG.textBoxY);
      }
      if (autoItem) {
        const image = await this.assets.image(autoItem.url);
        this.ctx.drawImage(image, 1162, 750, 99, 27);
      }
      if (skipItem) {
        const image = await this.assets.image(skipItem.url);
        this.ctx.drawImage(image, 1284, 750, 81, 27);
      }
    }

    font(family, size, weight) {
      return `${weight || 500} ${size}px "${family}", "M PLUS 1p", sans-serif`;
    }

    gridWidth(family = "MokissText", weight = 500) {
      this.ctx.font = this.font(family, RENDER_CONFIG.fontSize, weight);
      return Math.floor(this.ctx.measureText("あ").width * RENDER_CONFIG.stretchFactor) + RENDER_CONFIG.charSpacing;
    }

    renderGlyph(char, color, family = "MokissText", size = RENDER_CONFIG.fontSize, weight = 500) {
      const key = `${char}|${color}|${family}|${size}|${weight}`;
      if (this.glyphCache.has(key)) return this.glyphCache.get(key);
      const probe = this.createCanvas(size * 2, RENDER_CONFIG.glyphHeight);
      const pctx = probe.getContext("2d");
      pctx.font = this.font(family, size, weight);
      pctx.textBaseline = "top";
      const width = Math.max(1, Math.ceil(pctx.measureText(char).width + 3));
      const height = size === RENDER_CONFIG.fontSize ? RENDER_CONFIG.glyphHeight : Math.ceil(size * 1.2);
      probe.width = width;
      probe.height = height;
      pctx.font = this.font(family, size, weight);
      pctx.textBaseline = "top";
      pctx.fillStyle = color;
      pctx.fillText(char, 0, 0);

      const small = this.createCanvas(Math.max(1, Math.floor(width / RENDER_CONFIG.pixelateFactor)), Math.max(1, Math.floor(height / RENDER_CONFIG.pixelateFactor)));
      const sctx = small.getContext("2d");
      sctx.imageSmoothingEnabled = true;
      sctx.drawImage(probe, 0, 0, small.width, small.height);
      const output = this.createCanvas(Math.round(width * RENDER_CONFIG.stretchFactor), height);
      const octx = output.getContext("2d");
      octx.imageSmoothingEnabled = true;
      octx.drawImage(small, 0, 0, output.width, output.height);
      this.glyphCache.set(key, output);
      return output;
    }

    drawEffectGlyph(char, x, y, color, family = "MokissText", size = RENDER_CONFIG.fontSize, weight = 500) {
      const shadow = this.renderGlyph(char, "rgb(0,0,0)", family, size, weight);
      const glyph = this.renderGlyph(char, color, family, size, weight);
      this.ctx.drawImage(shadow, x + RENDER_CONFIG.shadowOffsetX, y + RENDER_CONFIG.shadowOffsetY);
      this.ctx.drawImage(glyph, x, y);
    }

    parseMarkup(text) {
      const tokens = [];
      const pattern = /\{([^}|]+)\|([^}]+)\}|\{boten:([^}]+)\}/g;
      let last = 0;
      let match;
      while ((match = pattern.exec(String(text || "")))) {
        for (const char of text.slice(last, match.index)) tokens.push({ type: "plain", char, length: 1 });
        if (match[1] != null) tokens.push({ type: "ruby", base: match[1], ruby: match[2], length: [...match[1]].length });
        else tokens.push({ type: "boten", base: match[3], length: [...match[3]].length });
        last = pattern.lastIndex;
      }
      for (const char of String(text || "").slice(last)) tokens.push({ type: "plain", char, length: 1 });
      return tokens;
    }

    wrapMarkup(text) {
      const result = [];
      for (const paragraph of String(text || "").split("\n")) {
        if (!paragraph) { result.push([]); continue; }
        const tokens = this.parseMarkup(paragraph);
        let line = [];
        let count = 0;
        for (const token of tokens) {
          if (count + token.length > RENDER_CONFIG.maxCharsPerLine && line.length) {
            result.push(line);
            line = [];
            count = 0;
          }
          line.push(token);
          count += token.length;
        }
        if (line.length) result.push(line);
      }
      return result;
    }

    drawRuby(text, x, y, spanWidth, color) {
      const chars = [...String(text || "")];
      if (!chars.length) return;
      this.ctx.font = this.font("MokissText", RENDER_CONFIG.rubyFontSize, 500);
      this.ctx.textBaseline = "top";
      this.ctx.fillStyle = color;
      const widths = chars.map((char) => this.ctx.measureText(char).width);
      const total = widths.reduce((sum, value) => sum + value, 0);
      if (chars.length === 1) {
        this.ctx.fillText(chars[0], x + (spanWidth - widths[0]) / 2, y);
        return;
      }
      const gap = total >= spanWidth ? 0 : (spanWidth - total) / (chars.length - 1);
      let cursor = x;
      chars.forEach((char, index) => {
        this.ctx.fillText(char, cursor, y);
        cursor += widths[index] + gap;
      });
    }

    drawTokenLine(tokens, x, y, color) {
      const grid = this.gridWidth();
      let count = 0;
      for (const token of tokens) {
        if (count >= RENDER_CONFIG.maxCharsPerLine) break;
        if (token.type === "plain") {
          this.drawEffectGlyph(token.char, x + count * grid, y, color);
          count += 1;
          continue;
        }
        const chars = [...token.base].slice(0, RENDER_CONFIG.maxCharsPerLine - count);
        chars.forEach((char, index) => this.drawEffectGlyph(char, x + (count + index) * grid, y, color));
        if (token.type === "ruby") {
          this.drawRuby(token.ruby, x + count * grid, y - RENDER_CONFIG.rubyHeight, grid * chars.length, color);
        } else {
          chars.forEach((char, index) => this.drawRuby("·", x + (count + index) * grid, y - RENDER_CONFIG.rubyHeight, grid, color));
        }
        count += chars.length;
      }
    }

    textColor(speaker, forceFemale = false) {
      return forceFemale || FEMALE_CHARACTERS.has(String(speaker || "")) ? RENDER_CONFIG.femaleTextColor : RENDER_CONFIG.textColor;
    }

    drawName(name, y, color) {
      if (!name) return;
      const chars = [...String(name)];
      const display = chars.length === 1 ? ["　", chars[0], "　"] : chars.length === 2 ? [chars[0], "　", chars[1]] : chars;
      const grid = this.gridWidth("MokissName", 700);
      display.forEach((char, index) => this.drawEffectGlyph(char, RENDER_CONFIG.nameStartX + index * grid, y, color, "MokissName", RENDER_CONFIG.fontSize, 700));
    }

    drawDialogue(blocks) {
      const lines = [];
      for (const block of blocks || []) {
        if (!block || !block.body) continue;
        const wrapped = this.wrapMarkup(block.body);
        wrapped.forEach((tokens, index) => lines.push({
          tokens,
          speaker: block.speaker || "",
          forceFemale: !!block.forceFemale,
          first: index === 0,
        }));
      }
      const visible = lines.slice(-RENDER_CONFIG.maxDisplayLines);
      let previousSpeaker = null;
      let previousForceFemale = null;
      visible.forEach((line, index) => {
        const y = RENDER_CONFIG.textStartY + index * RENDER_CONFIG.lineHeight;
        const color = this.textColor(line.speaker, line.forceFemale);
        if (line.speaker && (index === 0 || line.speaker !== previousSpeaker || line.forceFemale !== previousForceFemale)) this.drawName(line.speaker, y, color);
        this.drawTokenLine(line.tokens, RENDER_CONFIG.textStartX, y, color);
        previousSpeaker = line.speaker || previousSpeaker;
        previousForceFemale = line.forceFemale;
      });
    }

    choiceLayout(count) {
      if (count <= 3) return [1, [count]];
      if (count <= 6) return [2, [Math.ceil(count / 2), Math.floor(count / 2)]];
      return [3, [Math.ceil(count / 3), Math.ceil((count - Math.ceil(count / 3)) / 2), Math.floor(count / 3)]];
    }

    drawChoices(choices) {
      const values = choices.slice(0, 9);
      const layout = this.choiceLayout(values.length);
      let consumed = 0;
      layout[1].forEach((rows, column) => {
        for (let row = 0; row < rows; row += 1) {
          const value = values[consumed++];
          const lines = this.wrapMarkup(value);
          const height = Math.max(1, lines.length) * RENDER_CONFIG.lineHeight;
          const x = 95 + column * (337 + 37);
          const y = 798 + row * height;
          lines.forEach((tokens, lineIndex) => this.drawTokenLine(tokens, x, y + lineIndex * RENDER_CONFIG.lineHeight, RENDER_CONFIG.textColor));
        }
      });
    }

    drawDate(text) {
      this.ctx.font = this.font("MokissDate", RENDER_CONFIG.dateFontSize, 400);
      this.ctx.textBaseline = "top";
      this.ctx.fillStyle = "rgb(0,0,0)";
      this.ctx.fillText(text, 22 + RENDER_CONFIG.shadowOffsetX, 30 + RENDER_CONFIG.shadowOffsetY);
      this.ctx.fillStyle = "rgb(255,255,255)";
      this.ctx.fillText(text, 22, 30);
    }

    async drawComposite(fields, code) {
      await this.ready();
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
    RENDER_CONFIG,
    parseTag,
    parseScenario,
    buildState,
    findStepForSourceLine,
    applyAction,
    classifyStem,
    AssetIndex,
    CanvasRenderer,
  };
});
