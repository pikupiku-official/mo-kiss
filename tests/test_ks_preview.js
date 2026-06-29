const test = require('node:test');
const assert = require('node:assert/strict');

const preview = require('../tools/dev/ks-editor/preview_engine.js');

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
