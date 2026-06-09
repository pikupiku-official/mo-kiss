<?php
// ============================================================
//  mo-kiss KSエディタ — GitHub API プロキシ
//  認証情報は api_config.php に記載（.gitignore で除外）
// ============================================================

$config = __DIR__ . '/api_config.php';
if (!file_exists($config)) {
    http_response_code(503);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'api_config.php が見つかりません。サーバー管理者に連絡してください。']);
    exit;
}
require_once $config;

define('REPO',   'pikupiku-official/mo-kiss');
define('BRANCH', 'main');

// ── CORS & レスポンスヘッダー ──
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-App-Secret');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit; }

// ── 認証 ──
$secret = $_SERVER['HTTP_X_APP_SECRET'] ?? '';
if ($secret !== APP_SECRET) {
    http_response_code(401);
    echo json_encode(['error' => '認証エラー']);
    exit;
}

// ── アクション取得 ──
$action = $_GET['action'] ?? '';
$path   = trim($_GET['path'] ?? '', '/');

// パストラバーサル対策
if (strpos($path, '..') !== false || strpos($path, "\0") !== false) {
    http_response_code(400);
    echo json_encode(['error' => '不正なパス']);
    exit;
}

$api_base = 'https://api.github.com/repos/' . REPO;
$headers  = [
    'Accept: application/vnd.github+json',
    'Authorization: Bearer ' . GITHUB_PAT,
    'User-Agent: mo-kiss-ks-editor/1.0',
    'X-GitHub-Api-Version: 2022-11-28',
];

function gh_request(string $url, string $method, array $headers, ?string $body = null): array {
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 20);
    if ($body !== null) curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
    $response = curl_exec($ch);
    $code     = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return ['code' => $code, 'body' => $response];
}

switch ($action) {
    case 'list':
        $dir = $_GET['dir'] ?? 'events';
        $r = gh_request("$api_base/contents/$dir?ref=" . BRANCH, 'GET', $headers);
        http_response_code($r['code']); echo $r['body']; break;

    case 'get':
        if (!$path) { http_response_code(400); echo json_encode(['error'=>'path required']); break; }
        $r = gh_request("$api_base/contents/$path?ref=" . BRANCH, 'GET', $headers);
        http_response_code($r['code']); echo $r['body']; break;

    case 'save':
        if (!$path) { http_response_code(400); echo json_encode(['error'=>'path required']); break; }
        $input   = file_get_contents('php://input');
        $hdrs    = array_merge($headers, ['Content-Type: application/json']);
        $r = gh_request("$api_base/contents/$path", 'PUT', $hdrs, $input);
        http_response_code($r['code']); echo $r['body']; break;

    case 'delete':
        if (!$path) { http_response_code(400); echo json_encode(['error'=>'path required']); break; }
        $input   = file_get_contents('php://input');
        $hdrs    = array_merge($headers, ['Content-Type: application/json']);
        $r = gh_request("$api_base/contents/$path", 'DELETE', $hdrs, $input);
        http_response_code($r['code']); echo $r['body']; break;

    default:
        http_response_code(400);
        echo json_encode(['error' => '不明なアクション: ' . $action]);
}
