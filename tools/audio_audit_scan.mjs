import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

const root = process.cwd();
const outputPath = process.argv[2] || path.join(root, "audio_audit_scan.json");
const excludedDirs = new Set([
  ".git", "venv", ".pytest_cache", "__pycache__", "node_modules", "outputs",
]);
const audioExts = new Set([".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".mid", ".midi", ".opus"]);
const textExts = new Set([".py", ".ks", ".json", ".jsonl", ".md", ".txt", ".js", ".mjs", ".ts", ".yml", ".yaml", ".html", ".css", ".ps1", ".cfg"]);

async function walk(dir, out = []) {
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    if (entry.isDirectory() && excludedDirs.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) await walk(full, out);
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

function rel(full) {
  return path.relative(root, full).replaceAll("\\", "/");
}

function hash(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function nearby(lines, index) {
  const before = [];
  const after = [];
  for (let i = index - 1; i >= 0 && before.length < 2; i--) {
    const value = lines[i].trim();
    if (value) before.unshift(value);
  }
  for (let i = index + 1; i < lines.length && after.length < 2; i++) {
    const value = lines[i].trim();
    if (value) after.push(value);
  }
  return { before, after };
}

const files = await walk(root);
const audioFiles = [];
const textFiles = [];
for (const full of files) {
  const ext = path.extname(full).toLowerCase();
  if (audioExts.has(ext)) {
    const data = await fs.readFile(full);
    const stat = await fs.stat(full);
    audioFiles.push({
      path: rel(full),
      fileName: path.basename(full),
      stem: path.basename(full, ext),
      extension: ext,
      bytes: stat.size,
      sha256: hash(data),
    });
  } else if (textExts.has(ext)) {
    textFiles.push(full);
  }
}

const ksTags = [];
const literalAudioRefs = [];
const tagRegex = /\[\s*(BGMEND|BGM|SESTOP|SE|RAIN_SOUND_STOP|RAIN_SOUND)(?=\s|\])([^\]]*)\]/giu;
const attrRegex = /([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s\]]+))/g;
const audioLiteralRegex = /([^\s"'`<>\[\](){}:,;=]+\.(?:wav|mp3|ogg|flac|m4a|aac|wma|mid|midi|opus))/giu;

for (const full of textFiles) {
  let text;
  try {
    text = await fs.readFile(full, "utf8");
  } catch {
    continue;
  }
  const file = rel(full);
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    tagRegex.lastIndex = 0;
    let match;
    while ((match = tagRegex.exec(line))) {
      const tag = match[1].toLowerCase();
      const rawArgs = match[2] || "";
      const attrs = {};
      attrRegex.lastIndex = 0;
      let attr;
      while ((attr = attrRegex.exec(rawArgs))) attrs[attr[1].toLowerCase()] = attr[2] ?? attr[3] ?? attr[4] ?? "";
      const unparsed = rawArgs.replace(attrRegex, " ").replace(/[\s　]+/g, " ").trim();
      ksTags.push({ file, line: i + 1, tag, raw: match[0], lineText: line.trim(), attrs, unparsed, ...nearby(lines, i) });
    }
    audioLiteralRegex.lastIndex = 0;
    while ((match = audioLiteralRegex.exec(line))) {
      literalAudioRefs.push({ file, line: i + 1, value: match[1], text: line.trim() });
    }
  }
}

audioFiles.sort((a, b) => a.path.localeCompare(b.path, "ja"));
ksTags.sort((a, b) => a.file.localeCompare(b.file, "ja") || a.line - b.line);
literalAudioRefs.sort((a, b) => a.file.localeCompare(b.file, "ja") || a.line - b.line);

const byHash = {};
for (const item of audioFiles) (byHash[item.sha256] ||= []).push(item.path);
const duplicateGroups = Object.values(byHash).filter(group => group.length > 1);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, JSON.stringify({ audioFiles, ksTags, literalAudioRefs, duplicateGroups }, null, 2), "utf8");
console.log(JSON.stringify({
  outputPath,
  audioFileCount: audioFiles.length,
  ksTagCount: ksTags.length,
  literalAudioRefCount: literalAudioRefs.length,
  duplicateGroupCount: duplicateGroups.length,
}, null, 2));
