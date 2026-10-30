KS読み込みの画像準備を短縮した。フェードの描画処理、時間、縮小品質、再生前のキャッシュ準備は維持している。KSファイルは変更していない。

遅延の中心はKSのテキスト解析ではなく、元画像の展開と表示サイズへの縮小だった。GD006では解析約40msに対し、変更前の画像準備は約19〜20秒。サイズ確認だけで元画像全体を展開し、元画像キャッシュから追い出された立ち絵を準備時に再展開していた。画像準備も直列だった。

画像サイズは既存のPyQt5のQImageReaderでヘッダーから取得する。取得できない形式や別名の解決は従来のget_imageに戻す。画像の展開・縮小は独立した画像2枚まで並列に進める。キャッシュへの登録と進捗表示は呼び出し元スレッドで行い、登録順と容量制限を維持する。全画像分のジョブを先に投入しない。

同じ計測スクリプト、隔離したセーブ領域、SDL dummyで画像準備を測定した。数値は各1回で、アプリ全体の起動時間や実画面でのロード時間ではない。

| KS | 変更前 | 変更後 | 短縮 | 元画像の展開回数 |
| --- | ---: | ---: | ---: | ---: |
| GD006 | 20.30秒 | 12.02秒 | 40.8% | 92 → 81 |
| GD001 | 42.19秒 | 27.35秒 | 35.2% | 176 → 155 |

最初の変更前測定はGD006 18.76秒、GD001 36.98秒で、測定間のばらつきがある。変更後に同じ元画像の重複展開は両KSともゼロになった。

表示用画像全293枚についてRGBAのSHA-256、切り出し位置、画像寸法が変更前と完全一致した。最終的なキャッシュ容量もGD006 98.03MiB、GD001 143.42MiBで同じ。

実アプリのGD006を実時計・キーボードSKIPで再生し、21回のCGフェードすべての指定時間と複数フレームの描画を確認。再生中の追加画像読み込みはゼロ。変更前・変更後の最終画面も完全一致し、KSと通常セーブ領域は不変だった。CGクロスフェード描画中央値は変更前5.94ms、変更後7.59ms／再測定6.11ms。描画時間には測定間のばらつきがあるが、描画コードそのものは今回変更していない。

関連テストは82件成功、2件失敗。失敗したtests/test_image_manager_debug_logging.pyの2件はHEAD版のImageManagerでも同じAttributeErrorになることを別実行で確認した。テストのobject()にget_size()がないことによる既存の失敗で、今回の修正には含めていない。

計測コードと生データ:

- ks-loading-profile.py / ks-loading-before.json / ks-loading-reference.json / ks-loading-after.json
- ks-character-images-before.py.txt は今回の変更前のcharacter_images.py
- ks-loading-playback-reference.py / ks-loading-cg-reference/metrics.json
- ks-loading-cg-playback/metrics.json / ks-loading-cg-playback-repeat/metrics.json

再計測はリポジトリルートから実行する:

```powershell
$env:KS_LOADING_REFERENCE = 'outputs/ks-character-images-before.py.txt'
python outputs/ks-loading-profile.py outputs/ks-loading-reference.json events/GD006.ks events/GD001.ks
Remove-Item Env:KS_LOADING_REFERENCE
python outputs/ks-loading-profile.py outputs/ks-loading-after.json events/GD006.ks events/GD001.ks
python outputs/ks-loading-playback-reference.py
python tests/gd006_cg_playback_runner.py outputs/ks-loading-cg-playback-repeat
```
