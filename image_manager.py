import pygame
import os
import warnings
import asyncio
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from config import get_textbox_position, get_ui_button_positions

class ImageManager:
    def __init__(self, debug=False, cache_size=50):
        self.debug = debug
        self.images = {}
        self.image_cache = OrderedDict()  # LRUキャッシュ
        self.cache_size = cache_size
        self.image_paths = {}  # パス情報を保存
        self.default_sizes = {
            'character': None,  # キャラクター画像は元サイズを維持
            'background': None,  # 背景は画面サイズに合わせる
            'ui': None,  # UIは元サイズまたは設定サイズ
            'face_part': None  # 顔パーツは元サイズを維持
        }
        
        # 非同期処理用
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.loading_tasks = {}  # 読み込み中タスクの管理
        self.lock = threading.Lock()  # キャッシュ操作の同期
        
        # libpng警告を抑制
        warnings.filterwarnings("ignore", message=".*iCCP.*")
        warnings.filterwarnings("ignore", message=".*cHRM.*")

    def _manage_cache(self, cache_key, image):
        """LRUキャッシュの管理（スレッドセーフ）"""
        with self.lock:
            if cache_key in self.image_cache:
                # 既存のキーを最新に移動
                self.image_cache.move_to_end(cache_key)
            else:
                # 新しいアイテムを追加
                self.image_cache[cache_key] = image
                
                # キャッシュサイズを超えた場合、最も古いアイテムを削除
                if len(self.image_cache) > self.cache_size:
                    oldest_key = next(iter(self.image_cache))
                    del self.image_cache[oldest_key]
                    if self.debug:
                        print(f"キャッシュから削除: {oldest_key}")
    
    def _get_from_cache(self, cache_key):
        """キャッシュから画像を取得（スレッドセーフ）"""
        with self.lock:
            if cache_key in self.image_cache:
                self.image_cache.move_to_end(cache_key)  # LRU更新
                return self.image_cache[cache_key]
            return None

    def _get_optimal_size(self, filepath, requested_size=None):
        """画像の最適なサイズを決定"""
        if requested_size:
            return requested_size
            
        # ファイルパスから画像タイプを判定して推奨サイズを返す
        if "characters" in filepath or "char" in filepath:
            return self.default_sizes['character']
        elif "eyes" in filepath or "mouths" in filepath or "brows" in filepath or "cheeks" in filepath:
            return self.default_sizes['face_part']
        elif "bg" in filepath:
            return self.default_sizes['background']
        else:
            return None  # 元サイズを維持

    def load_image(self, filepath, size=None, lazy=True):
        """画像を読み込む（遅延ロード対応）"""
        # 最適サイズを決定
        optimal_size = self._get_optimal_size(filepath, size)
        cache_key = f"{filepath}_{optimal_size if optimal_size else 'original'}"
        
        # キャッシュから返す
        if cache_key in self.image_cache:
            self.image_cache.move_to_end(cache_key)  # LRU更新
            return self.image_cache[cache_key]
        
        if lazy:
            # 遅延ロードの場合はパス情報のみ保存
            return None
            
        return self._load_image_immediately(filepath, optimal_size, cache_key)
    
    async def load_image_async(self, filepath, size=None):
        """画像を非同期で読み込む"""
        optimal_size = self._get_optimal_size(filepath, size)
        cache_key = f"{filepath}_{optimal_size if optimal_size else 'original'}"
        
        # キャッシュから確認
        cached_image = self._get_from_cache(cache_key)
        if cached_image:
            return cached_image
        
        # 既に読み込み中かチェック
        if cache_key in self.loading_tasks:
            if self.debug:
                print(f"画像読み込み待機中: {filepath}")
            return await self.loading_tasks[cache_key]
        
        # 非同期で読み込み開始
        if self.debug:
            print(f"画像を非同期読み込み開始: {filepath}")
        
        task = asyncio.create_task(self._load_image_async_worker(filepath, optimal_size, cache_key))
        self.loading_tasks[cache_key] = task
        
        try:
            result = await task
            return result
        finally:
            # タスク完了後はリストから削除
            if cache_key in self.loading_tasks:
                del self.loading_tasks[cache_key]
    
    async def _load_image_async_worker(self, filepath, size, cache_key):
        """画像読み込みワーカー"""
        loop = asyncio.get_event_loop()
        
        try:
            # ファイル存在チェックを非同期で実行
            exists = await loop.run_in_executor(self.executor, os.path.exists, filepath)
            if not exists:
                if self.debug:
                    print(f"警告: 画像ファイルが見つかりません: {filepath}")
                return None
            
            # 画像読み込みを別スレッドで実行
            image = await loop.run_in_executor(
                self.executor, 
                self._load_image_sync, 
                filepath, 
                size
            )
            
            if image:
                # キャッシュに保存
                self._manage_cache(cache_key, image)
                if self.debug:
                    print(f"画像読み込み完了: {filepath}")
            
            return image
            
        except Exception as e:
            if self.debug:
                print(f"非同期画像読み込みエラー: {filepath}: {e}")
            return None
    
    def _load_image_sync(self, filepath, size):
        """同期的な画像読み込み（スレッド内で実行）"""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                image = pygame.image.load(filepath)
                image = image.convert_alpha()
            
            if size and isinstance(size, tuple) and len(size) == 2:
                original_size = image.get_size()
                if original_size != size:
                    image = pygame.transform.scale(image, size)
            
            return image
            
        except pygame.error as e:
            if self.debug:
                print(f"pygame読み込みエラー: {filepath}: {e}")
            return None
        except Exception as e:
            if self.debug:
                print(f"画像読み込みエラー: {filepath}: {e}")
            return None
    
    def _load_image_immediately(self, filepath, size, cache_key):
        """画像を即座に読み込む"""
        try:
            if not os.path.exists(filepath):
                if self.debug:
                    print(f"警告: 画像ファイルが見つかりません: {filepath}")
                return None
                
            # libpng警告を一時的に抑制
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # 画像を読み込む
                image = pygame.image.load(filepath)
                image = image.convert_alpha()

            # 画面サイズに合わせて画像をリサイズ（必要に応じて）
            if size and isinstance(size, tuple) and len(size) == 2:
                original_size = image.get_size()
                if original_size != size:
                    image = pygame.transform.scale(image, size)
                    if self.debug:
                        print(f"画像リサイズ: {filepath} {original_size} -> {size}")
                
            # キャッシュに保存
            self._manage_cache(cache_key, image)

            return image
        
        except pygame.error as e:
            if self.debug:
                print(f"pygame読み込みエラー: {filepath}: {e}")
            return None
        except Exception as e:
            if self.debug:
                print(f"画像読み込みエラー: {filepath}: {e}")
            return None
    
    def get_image(self, image_type, image_key, size=None):
        """画像を取得（必要に応じて遅延ロード）スレッドセーフ"""
        if image_type in self.image_paths and image_key in self.image_paths[image_type]:
            filepath = self.image_paths[image_type][image_key]
            optimal_size = self._get_optimal_size(filepath, size)
            cache_key = f"{filepath}_{optimal_size if optimal_size else 'original'}"

            # キャッシュチェックとロード中チェック（スレッドセーフ）
            load_event = None
            should_load = False

            with self.lock:
                # まずキャッシュを確認
                if cache_key in self.image_cache:
                    self.image_cache.move_to_end(cache_key)
                    cached_image = self.image_cache[cache_key]
                    # キャッシュヒットは頻繁すぎるのでログ出力しない
                    return cached_image

                # ロード中かチェック
                if cache_key in self.loading_tasks:
                    # 別スレッドがロード中の場合、イベントを取得して待機
                    load_event = self.loading_tasks[cache_key]
                    should_load = False
                else:
                    # 新規ロードの場合、イベントを作成
                    import threading
                    load_event = threading.Event()
                    self.loading_tasks[cache_key] = load_event
                    should_load = True

            # ロックの外で処理
            if should_load:
                # 自分がロードを担当する場合
                try:
                    # 新規ロード時のみログ出力
                    print(f"[IMG_LOAD] ロード: {image_type}/{image_key}")
                    result = self._load_image_immediately(filepath, optimal_size, cache_key)
                    if result is None:
                        print(f"[IMG_ERROR] ロード失敗: {image_type}/{image_key} from {filepath}")
                    return result
                finally:
                    # ロード完了後、イベントをシグナルして削除
                    with self.lock:
                        if cache_key in self.loading_tasks:
                            load_event.set()  # 待機中のスレッドに通知
                            del self.loading_tasks[cache_key]
            else:
                # 他スレッドがロード中の場合は待機
                print(f"[IMG_WAIT] ロード完了待機: {image_type}/{image_key}")
                load_event.wait(timeout=2.0)
                # 待機後、キャッシュから再取得
                with self.lock:
                    if cache_key in self.image_cache:
                        self.image_cache.move_to_end(cache_key)
                        return self.image_cache[cache_key]
                # タイムアウトまたはロード失敗
                print(f"[IMG_WARN] ロード待機タイムアウト: {image_type}/{image_key}")
                return None
        else:
            print(f"[IMG_ERROR] 画像パスが見つかりません: type={image_type}, key={image_key}")
            if image_type in self.image_paths:
                print(f"[IMG_ERROR] 利用可能なキー ({image_type}): {list(self.image_paths[image_type].keys())[:10]}...")
            return None
    
    async def get_image_async(self, image_type, image_key, size=None):
        """画像を非同期で取得"""
        if image_type in self.image_paths and image_key in self.image_paths[image_type]:
            filepath = self.image_paths[image_type][image_key]
            return await self.load_image_async(filepath, size)
        return None

    def center_part(self, part, position):
        """パーツを指定された位置の中心に配置するための座標を計算"""
        return (
            position[0] - part.get_width() // 2,
            position[1] - part.get_height() // 2
        )

    def scan_image_paths(self, screen_width, screen_height):
        """画像パスをスキャンして保存（実際の読み込みは遅延）"""
        self.image_paths = {
            "backgrounds": {},
            "characters": {},
            "eyes": {},
            "mouths": {},
            "brows": {},
            "cheeks": {},
            "ui": {}
        }
        
        # 背景サイズを設定
        self.default_sizes['background'] = (screen_width, screen_height)

        # imagesディレクトリ内のすべてのファイルをスキャン
        project_root = os.path.dirname(os.path.dirname(__file__))
        images_dir = os.path.join(project_root, "mo-kiss", "images")
        
        if self.debug:
            print(f"画像パススキャン開始: {images_dir}")
            
        for root, dirs, files in os.walk(images_dir):
            for file in files:
                if file.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    file_path = os.path.join(root, file)
                    file_name_without_ext = os.path.splitext(file)[0]
                    
                    if "bg" in file:
                        # 完全なファイル名 (拡張子なし) で背景を登録
                        bg_key = file_name_without_ext
                        self.image_paths["backgrounds"][bg_key] = file_path
                        
                        if self.debug:
                            print(f"背景画像登録: {bg_key} -> {file_path}")
                    elif "char" in file or root.endswith("characters") or root.endswith("桃子"):
                        self.image_paths["characters"][file_name_without_ext] = file_path
                    elif "eye" in file or root.endswith("eyes"):
                        self.image_paths["eyes"][file_name_without_ext] = file_path
                    elif "mouth" in file or root.endswith("mouths"):
                        self.image_paths["mouths"][file_name_without_ext] = file_path
                    elif "brow" in file or root.endswith("brows"):
                        self.image_paths["brows"][file_name_without_ext] = file_path
                    elif "cheek" in file or root.endswith("cheeks"):
                        self.image_paths["cheeks"][file_name_without_ext] = file_path
                    elif "ui" in file:
                        ui_name = file.split('.')[1] if len(file.split('.')) >= 3 else file.split('.')[0]
                        self.image_paths["ui"][ui_name] = file_path
        
        if self.debug:
            total_images = sum(len(paths) for paths in self.image_paths.values())
            print(f"画像パススキャン完了: {total_images}個の画像ファイルを発見")
    
    def load_essential_images(self, screen_width, screen_height):
        """必要最小限の画像のみを事前ロード"""
        images = {
            "backgrounds": {},
            "characters": {},
            "eyes": {},
            "mouths": {},
            "brows": {},
            "cheeks": {},
            "ui": {}
        }
        
        # UIの重要な画像のみ事前ロード
        essential_ui = ["text-box", "auto", "skip"]
        
        for ui_name in essential_ui:
            if ui_name in self.image_paths["ui"]:
                file_path = self.image_paths["ui"][ui_name]
                
                if ui_name == "text-box":
                    from config import scale_size
                    virtual_width = 1340  # 1646×0.75（4:3対応）
                    # 元画像を一時的に読み込んでサイズを取得
                    temp_image = self._load_image_immediately(file_path, None, f"temp_{ui_name}")
                    if temp_image:
                        original_width = temp_image.get_width()
                        original_height = temp_image.get_height()
                        virtual_height = int(virtual_width * original_height / original_width)
                        new_width, new_height = scale_size(virtual_width, virtual_height)
                        images["ui"][ui_name] = self._load_image_immediately(file_path, (new_width, new_height), f"ui_{ui_name}")
                        
                elif ui_name == "auto":
                    from config import scale_size
                    virtual_width2 = 110
                    temp_image2 = self._load_image_immediately(file_path, None, f"temp_{ui_name}")
                    if temp_image2:
                        original_width2 = temp_image2.get_width()
                        original_height2 = temp_image2.get_height()
                        virtual_height2 = int(virtual_width2 * original_height2 / original_width2)
                        new_width2, new_height2 = scale_size(virtual_width2, virtual_height2)
                        images["ui"][ui_name] = self._load_image_immediately(file_path, (new_width2, new_height2), f"ui_{ui_name}")
                        
                elif ui_name == "skip":
                    from config import scale_size
                    virtual_width3 = 91
                    temp_image3 = self._load_image_immediately(file_path, None, f"temp_{ui_name}")
                    if temp_image3:
                        original_width3 = temp_image3.get_width()
                        original_height3 = temp_image3.get_height()
                        virtual_height3 = int(virtual_width3 * original_height3 / original_width3)
                        new_width3, new_height3 = scale_size(virtual_width3, virtual_height3)
                        images["ui"][ui_name] = self._load_image_immediately(file_path, (new_width3, new_height3), f"ui_{ui_name}")
        
        if self.debug:
            loaded_count = sum(len(category) for category in images.values())
            print(f"必須画像ロード完了: {loaded_count}個")
        
        return images 
    
    def draw_ui_elements(self, screen, images, show_text=True):
        """UI要素を描画する（遅延ロード対応）"""
        if not show_text:
            return
        
        # UI画像を必要に応じて遅延ロード
        ui_elements = ["text-box", "auto", "skip"]
        
        for ui_name in ui_elements:
            # 事前ロードされた画像があるかチェック
            if "ui" in images and ui_name in images["ui"] and images["ui"][ui_name]:
                ui_image = images["ui"][ui_name]
            else:
                # 遅延ロードで取得
                ui_image = self.get_image("ui", ui_name)
                
            if ui_image:
                if ui_name == "text-box":
                    x_pos, y_pos = get_textbox_position(screen, ui_image)

                    # 色変更が有効な場合、色を適用
                    from config import TEXTBOX_COLOR_TINT
                    if TEXTBOX_COLOR_TINT.get("enabled", False):
                        # 色を適用するため、一時的なサーフェスを作成
                        tinted_image = ui_image.copy()
                        # RGB乗算で色を適用（アルファチャンネルは保持）
                        color_surface = pygame.Surface(tinted_image.get_size(), pygame.SRCALPHA)
                        color_surface.fill((*TEXTBOX_COLOR_TINT["color"], 255))
                        tinted_image.blit(color_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        screen.blit(tinted_image, (x_pos, y_pos))
                    else:
                        screen.blit(ui_image, (x_pos, y_pos))
                elif ui_name in ["auto", "skip"]:
                    button_positions = get_ui_button_positions(screen)
                    if ui_name in button_positions:
                        btn_x, btn_y = button_positions[ui_name]
                        # auto/skipボタンを0.9倍に縮小
                        original_size = ui_image.get_size()
                        new_size = (int(original_size[0] * 0.9), int(original_size[1] * 0.9))
                        scaled_ui_image = pygame.transform.scale(ui_image, new_size)
                        screen.blit(scaled_ui_image, (btn_x, btn_y))
    
    def preload_character_set(self, character_name, face_parts=None):
        """キャラクターと関連顔パーツを事前ロード"""
        if self.debug:
            print(f"キャラクター事前ロード開始: {character_name}")
        
        # キャラクターメイン画像をロード
        char_img = self.get_image("characters", character_name)
        if char_img and self.debug:
            print(f"キャラクター画像ロード完了: {character_name} ({char_img.get_width()}x{char_img.get_height()})")
        
        # 顔パーツをロード
        if face_parts:
            for part_type, part_name in face_parts.items():
                if part_name and part_type in ["eyes", "mouths", "brows", "cheeks"]:
                    part_img = self.get_image(part_type, part_name)
                    if part_img and self.debug:
                        print(f"顔パーツロード完了: {part_type}/{part_name}")
    
    async def preload_character_set_async(self, character_name, face_parts=None):
        """キャラクターと関連顔パーツを非同期で事前ロード"""
        if self.debug:
            print(f"キャラクター非同期事前ロード開始: {character_name}")
        
        # 非同期タスクのリスト
        tasks = []
        
        # キャラクターメイン画像をロード
        if "characters" in self.image_paths and character_name in self.image_paths["characters"]:
            tasks.append(self.get_image_async("characters", character_name))
        
        # 顔パーツをロード
        if face_parts:
            for part_type, part_names in face_parts.items():
                if part_type in ["eyes", "mouths", "brows", "cheeks"]:
                    if isinstance(part_names, list):
                        for part_name in part_names:
                            if part_name:
                                tasks.append(self.get_image_async(part_type, part_name))
                    elif part_names:
                        tasks.append(self.get_image_async(part_type, part_names))
        
        # 全ての読み込みタスクを並行実行
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            if self.debug:
                success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
                print(f"キャラクター非同期事前ロード完了: {character_name} ({success_count}/{len(tasks)} 成功)")
        
        return True
    
    def preload_characters_from_dialogue(self, dialogue_data):
        """対話データからキャラクターを抽出して事前ロード"""
        if not dialogue_data:
            return
        
        try:
            character_usage = {}
            
            # 対話データからキャラクター情報を抽出
            for entry in dialogue_data:
                try:
                    if isinstance(entry, (list, tuple)) and len(entry) >= 6:
                        # キャラクター名を取得
                        char_name = entry[1] if len(entry) > 1 and entry[1] else None
                        if char_name and isinstance(char_name, str) and not char_name.startswith("_"):  # コマンドではない名前
                            if char_name not in character_usage:
                                character_usage[char_name] = {
                                    "eyes": set(),
                                    "mouths": set(), 
                                    "brows": set(),
                                    "cheeks": set()
                                }
                            
                            # 顔パーツ情報を追加（安全にチェック）
                            if len(entry) > 2 and entry[2] and isinstance(entry[2], str):  # eye
                                character_usage[char_name]["eyes"].add(entry[2])
                            if len(entry) > 3 and entry[3] and isinstance(entry[3], str):  # mouth
                                character_usage[char_name]["mouths"].add(entry[3])
                            if len(entry) > 4 and entry[4] and isinstance(entry[4], str):  # brow
                                character_usage[char_name]["brows"].add(entry[4])
                            if len(entry) > 5 and entry[5] and isinstance(entry[5], str):  # cheek
                                character_usage[char_name]["cheeks"].add(entry[5])
                except Exception as e:
                    if self.debug:
                        print(f"エントリ処理エラー（スキップ）: {e}, entry: {entry}")
                    continue
            
            # キャラクターを事前ロード
            if self.debug:
                print(f"事前ロード対象キャラクター: {list(character_usage.keys())}")
            
            for char_name, parts in character_usage.items():
                try:
                    # 顔パーツを辞書形式に変換
                    face_parts = {}
                    for part_type, part_set in parts.items():
                        if part_set and isinstance(part_set, set):  # 空でない場合、最初の要素を代表として使用
                            face_parts[part_type] = list(part_set)
                    
                    self.preload_character_set(char_name, face_parts)
                except Exception as e:
                    if self.debug:
                        print(f"キャラクター事前ロードエラー（スキップ）: {char_name}: {e}")
                    continue
                    
        except Exception as e:
            if self.debug:
                print(f"キャラクター事前ロード処理全体エラー: {e}")
            # エラーがあっても処理を続行
    
    def get_cache_stats(self):
        """キャッシュ統計を取得"""
        return {
            'cache_size': len(self.image_cache),
            'max_cache_size': self.cache_size,
            'cache_hit_ratio': getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1),
            'loading_tasks': len(self.loading_tasks)
        }
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        # 実行中のタスクをキャンセル
        for task in self.loading_tasks.values():
            if not task.done():
                task.cancel()
        self.loading_tasks.clear()
        
        # ExecutorPoolをシャットダウン
        self.executor.shutdown(wait=False)
        
        if self.debug:
            print("ImageManager: リソースクリーンアップ完了")