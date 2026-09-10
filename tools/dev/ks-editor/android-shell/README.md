# mo-kiss KSエディタ Android版

このディレクトリは、`tools/dev/ks-editor` のWeb UIをCapacitorでAndroid APKへ包むためのシェルです。

## ビルド環境

- Node.js / npm
- Java 17以上
- Android StudioまたはAndroid SDK
- Android SDKの`platform-tools`とビルドツール

## 初回セットアップ

```powershell
npm install
npx cap add android
```

## 同梱データを含めて同期

```powershell
npm run build:web
npx cap sync android
```

`events`、`images`、`sounds`、`fonts`、`movies`をAPK用Web資産へコピーし、
`offline-manifest.json`を生成します。初回APKはオンラインなしでもKS一覧とプレビューを起動できます。

## Androidプロジェクトを開く

```powershell
npm run android
```

このアプリはWeb版と同じUIを使います。KS・アセットの更新はオンライン時にGitHubから同期し、
編集内容はIndexedDBへ保存してから`mokiss.jp`の保存APIへ送信します。
