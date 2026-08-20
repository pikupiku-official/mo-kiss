# Ruri v3 30M INT8 ONNX

- ONNX conversion: `WariHima/ruri-v3-30m-onnx`
- Conversion revision: `5c329c35a623f38804d1b048dfa61b9f5818d8b4`
- Upstream model: `cl-nagoya/ruri-v3-30m`
- Upstream revision: `24899e5de370b56d179604a007c0d727bf144504`
- License: Apache-2.0 (see `LICENSE-APACHE-2.0.txt`)

`model_int8.onnx` comes from the conversion repository. `tokenizer.model`
comes from the pinned upstream revision. The conversion repository's
`tokenizer.json` encoded Japanese text as `<unk>` when loaded directly, so it
is not bundled. The game reads `tokenizer.model` directly with SentencePiece
and constructs the same BOS + text + EOS input used by the official model.

The game uses this model entirely offline. It never downloads model files at
runtime.

## SHA-256

- `model_int8.onnx`: `E97133D96919255DE21A62D22002E9E2BB6BC8B8B82A646AEE295FD414BAACA9`
- `tokenizer.model`: `008293028E1A9D9A1038D9B63D989A2319797DFEAA03F171093A57B33A3A8277`
