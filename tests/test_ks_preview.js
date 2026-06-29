const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const preview = require('../tools/dev/ks-editor/preview_engine.js');

test('render constants stay aligned with core/config.py', () => {
  assert.deepEqual({ width: preview.VIRTUAL_WIDTH, height: preview.VIRTUAL_HEIGHT }, { width: 1440, height: 1080 });
  assert.deepEqual(
    {
      textX: preview.RENDER_CONFIG.textStartX,
      textY: preview.RENDER_CONFIG.textStartY,
      nameX: preview.RENDER_CONFIG.nameStartX,
      nameY: preview.RENDER_CONFIG.nameStartY,
      chars: preview.RENDER_CONFIG.maxCharsPerLine,
      lines: preview.RENDER_CONFIG.maxDisplayLines,
      font: preview.RENDER_CONFIG.fontSize,
      glyphHeight: preview.RENDER_CONFIG.glyphHeight,
      lineHeight: preview.RENDER_CONFIG.lineHeight,
      rubyHeight: preview.RENDER_CONFIG.rubyHeight,
      box: [preview.RENDER_CONFIG.textBoxX, preview.RENDER_CONFIG.textBoxY, preview.RENDER_CONFIG.textBoxWidth, preview.RENDER_CONFIG.textBoxHeight],
    },
    { textX: 298, textY: 798, nameX: 95, nameY: 798, chars: 20, lines: 3, font: 45, glyphHeight: 63, lineHeight: 69, rubyHeight: 9, box: [50, 742, 1340, 288] },
  );
});

test('preview uses the same UI image dimensions and font files as pygame', () => {
  const root = path.join(__dirname, '..');
  function pngSize(file) {
    const bytes = fs.readFileSync(file);
    return [bytes.readUInt32BE(16), bytes.readUInt32BE(20)];
  }
  assert.deepEqual(pngSize(path.join(root, 'images', 'UI', 'ui.text-box.png')), [1340, 288]);
  assert.deepEqual(pngSize(path.join(root, 'images', 'UI', 'ui.auto.png')), [100, 28]);
  assert.deepEqual(pngSize(path.join(root, 'images', 'UI', 'ui.skip.png')), [83, 28]);
  for (const font of ['MPLUS1p-Medium.ttf', 'MPLUS1p-Bold.ttf', 'MPLUS1p-Regular.ttf']) {
    assert.ok(fs.statSync(path.join(root, 'fonts', font)).size > 1_000_000);
  }
});

test('Step editor exposes and verifies a real GitHub save path', () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'tools', 'dev', 'ks-editor', 'index.html'), 'utf8');
  assert.match(html, /id="step-save-github"/);
  assert.match(html, /GitHub mainへ保存/);
  assert.match(html, /verified\.sha===res\.content\.sha/);
  assert.match(html, /fromB64\(verified\.content\)===expectedText/);
  assert.match(html, /cache:\s*'no-store'/);
  assert.doesNotMatch(html, /\bsetLineNums\s*\(/);
});

test('parseTag handles quoted values, full-width spaces, and tag aliases', () => {
  const tag = preview.parseTag('[chara_show name="桃子"　torso="MMK_T01_ARM00_CLO00" x="0.5"]');
  assert.equal(tag.type, 'chara_show');
  assert.equal(tag.params.name, '桃子');
  assert.equal(tag.params.torso, 'MMK_T01_ARM00_CLO00');
  assert.equal(tag.params.x, '0.5');
  assert.equal(preview.parseTag('@scroll-stop').type, 'scroll_stop');
});

test('parseScenario binds pending actions and speakers to dialogue steps', () => {
  const parsed = preview.parseScenario(`*start
[bg_show storage="school" bg_x="0.5" bg_y="0.5"]
[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00"]
//桃子//
「こんにちは。」[scroll-stop]
[chara_shift name="桃子" eye="MMK_F00_EYE01_00"]
「次の行です。」`);
  assert.equal(parsed.steps.length, 2);
  assert.equal(parsed.steps[0].speaker, '桃子');
  assert.equal(parsed.steps[0].scrollStop, true);
  assert.deepEqual(parsed.steps[0].actions.map((action) => action.type), ['label', 'bg_show', 'chara_show']);
  assert.equal(parsed.steps[1].actions[0].type, 'chara_shift');
});

test('buildState replays background and character state up to selected step', () => {
  const parsed = preview.parseScenario(`[bg_show storage="school"]
[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" x="0.5" y="0.5"]
//桃子//
「一行目」
[chara_move name="桃子" left="0.1" top="-0.1" zoom="0.8"]
[chara_shift name="桃子" mouth="MMK_F00_MOU01_00"]
「二行目」`);
  const first = preview.buildState(parsed, 0);
  assert.equal(first.background.storage, 'school');
  assert.equal(first.characters['桃子'].x, 0.5);
  const second = preview.buildState(parsed, 1);
  assert.equal(second.characters['桃子'].x, 0.6);
  assert.equal(second.characters['桃子'].y, 0.4);
  assert.equal(second.characters['桃子'].size, 0.8);
  assert.equal(second.characters['桃子'].mouth, 'MMK_F00_MOU01_00');
  assert.equal(second.text.body, '二行目');
});

test('background positioning matches background_manager virtual offsets', () => {
  const parsed = preview.parseScenario(`[bg_show storage="school" bg_x="1" bg_y="0" bg_zoom="2"]
「背景」
[bg_move left="-0.1" top="0.1" bg_zoom="2"]
「移動後」`);
  const first = preview.buildState(parsed, 0);
  assert.equal(first.background.offsetX, 720);
  assert.equal(first.background.offsetY, -540);
  const second = preview.buildState(parsed, 1);
  assert.equal(second.background.offsetX, 576);
  assert.equal(second.background.offsetY, -432);
});

test('scroll text keeps the latest blocks until scroll-stop', () => {
  const parsed = preview.parseScenario(`//桃子//
「一行目」
「二行目」
「三行目」[scroll-stop]
「四行目」`);
  assert.equal(preview.buildState(parsed, 1).textBlocks.length, 2);
  assert.deepEqual(preview.buildState(parsed, 2).textBlocks.map((block) => block.body), ['一行目', '二行目', '三行目']);
  assert.deepEqual(preview.buildState(parsed, 3).textBlocks.map((block) => block.body), ['四行目']);
});

test('scene jump maps an action-range start to the following dialogue step', () => {
  const parsed = preview.parseScenario(`「前の背景」
[bg_show storage="test.bg.9901"]
//ナレ//
「新しい背景」`);
  assert.equal(parsed.steps[1].startLine, 1);
  assert.equal(preview.findStepForSourceLine(parsed, 1), 1);
  assert.equal(preview.findStepForSourceLine(parsed, parsed.steps[1].sourceLine), 1);
  assert.equal(preview.buildState(parsed, preview.findStepForSourceLine(parsed, 1)).background.storage, 'test.bg.9901');
});

test('every real KS background switch selects the step carrying that background', () => {
  const root = path.join(__dirname, '..', 'events');
  for (const file of fs.readdirSync(root).filter((name) => name.endsWith('.ks'))) {
    const parsed = preview.parseScenario(fs.readFileSync(path.join(root, file), 'utf8'));
    parsed.steps.forEach((step, index) => {
      const backgrounds = step.actions.filter((action) => ['bg', 'bg_show', 'background'].includes(action.type));
      if (!backgrounds.length) return;
      const mapped = preview.findStepForSourceLine(parsed, step.startLine);
      assert.equal(mapped, index, `${file}: line ${step.startLine + 1} mapped to the wrong scene`);
      const expected = backgrounds.at(-1).params.storage || backgrounds.at(-1).params.value;
      assert.equal(preview.buildState(parsed, mapped).background.storage, expected, `${file}: wrong background at scene jump`);
    });
  }
});

test('classifyStem follows ImageManager naming rules', () => {
  assert.equal(preview.classifyStem('MMK_T01_ARM00_CLO00'), 'torso');
  assert.equal(preview.classifyStem('MMK_F01_EYE02_00'), 'eye');
  assert.equal(preview.classifyStem('MMK_F01_MOU02_00'), 'mouth');
  assert.equal(preview.classifyStem('MMK_E01_00'), 'effect');
  assert.equal(preview.classifyStem('MMK_A01_00'), 'accessory');
});

test('AssetIndex filters face parts by the selected torso number', async () => {
  const assets = new preview.AssetIndex({ fetch: async () => { throw new Error('not used'); } });
  assets.characters.set('MMK', [
    { stem: 'MMK_T01_ARM00_CLO00', part: 'torso' },
    { stem: 'MMK_F00_EYE00_00', part: 'eye' },
    { stem: 'MMK_F01_EYE00_00', part: 'eye' },
    { stem: 'MMK_F01_EYE01_00', part: 'eye' },
  ]);
  const options = await assets.partOptions('MMK', 'eye', 'MMK_T01_ARM00_CLO00');
  assert.deepEqual(options.map((item) => item.stem), ['MMK_F01_EYE00_00', 'MMK_F01_EYE01_00']);
});

test('AssetIndex preserves dotted background IDs instead of stripping their numeric suffix', async () => {
  const assets = new preview.AssetIndex({ fetch: async () => { throw new Error('not used'); } });
  assets.backgrounds = [
    { stem: 'test.bg.9873', url: 'first' },
    { stem: 'test.bg.9901', url: 'second' },
    { stem: 'test.bg.DSCN3314', url: 'third' },
  ];
  assert.equal((await assets.resolveBackground('test.bg.9901')).url, 'second');
  assert.equal((await assets.resolveBackground('test.bg.DSCN3314.jpg')).url, 'third');
});
