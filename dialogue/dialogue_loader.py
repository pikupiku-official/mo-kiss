import re
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from bgm_manager import BGMManager
from config import *
from .ir_model import make_action, make_step, make_text

# aiofilesの条件付きインポート
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    if os.environ.get('DIALOGUE_DEBUG'):
        print("aiofiles not available - using ThreadPoolExecutor fallback")

class DialogueLoader:
    def __init__(self, debug=False):
        self.debug = debug
        self.bgm_manager = BGMManager(debug)
        # CHARACTER_IMAGE_MAPを削除（ファイル名直接使用）
        # self.character_image_map = CHARACTER_IMAGE_MAP
        # 26文字改行設定
        self.max_chars_per_line = 26
        
        # スクロール機能を全テキストに適用
        self.disable_scroll_continue = False  # スクロール機能を有効化
        
        # ストーリーフラグ管理システム
        self.story_flags = {}
        self.load_story_flags()
        
        # 選択肢履歴管理システム
        self.choice_history = {}  # {ks_file: [choice_indices]}
        self.current_ks_file = None
        self.choice_counter = 0
        
        # name_managerとの連携を設定
        from .name_manager import get_name_manager
        name_manager = get_name_manager()
        name_manager.set_dialogue_loader(self)
        
        # 通知システムの参照（後で設定される）
        self.notification_system = None
        
        # 非同期処理用
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.loading_tasks = {}  # ファイル読み込み中のタスク管理
        self.ir_data = None  # IR skeleton (optional)

    def _wrap_text_and_count_lines(self, text):
        """テキストを26文字で自動改行し、行数を返す"""
        if not text:
            return 0
        
        # 既存の改行コードで分割
        paragraphs = text.split('\n')
        total_lines = 0
        
        for paragraph in paragraphs:
            if not paragraph:
                # 空行の場合は1行として計算
                total_lines += 1
                continue
            
            # 26文字ごとに分割して行数を計算
            current_pos = 0
            while current_pos < len(paragraph):
                line_end = current_pos + self.max_chars_per_line
                if line_end >= len(paragraph):
                    # 最後の行
                    total_lines += 1
                    break
                else:
                    # 26文字で一行分
                    total_lines += 1
                    current_pos = line_end
        
        return total_lines

    def load_dialogue_from_ks(self, filename):
        try:
            # ファイルの存在確認
            if not os.path.exists(filename):
                if self.debug:
                    print(f"エラー: ファイル '{filename}' が見つかりません。カレントディレクトリ: {os.getcwd()}")
                return self.get_default_dialogue()
            
            # 新しいKSファイルの場合は履歴をクリア
            if self.current_ks_file != filename:
                self.current_ks_file = filename
                self.choice_history[filename] = []
                self.choice_counter = 0
                if self.debug:
                    print(f"新しいKSファイル読み込み: {filename} - 選択肢履歴をクリア")
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 対話データを解析
            dialogue_data = self._parse_ks_content(content)
            self.ir_data = self._build_ir_skeleton(dialogue_data)

            if self.debug:
                print(f"{len(dialogue_data)} 個の対話エントリーが解析されました")

            return dialogue_data
        
        except Exception as e:
            if self.debug:
                print(f"エラー: '{filename}' の読み込みに失敗しました: {e}")
            else:
                print(f"{filename}の読み込みに失敗しました: {e}")
                return self.get_default_dialogue()
    
    async def load_dialogue_from_ks_async(self, filename):
        """非同期で.ksファイルから対話データを読み込む"""
        try:
            # 既に読み込み中かチェック
            if filename in self.loading_tasks:
                if self.debug:
                    print(f"ファイル読み込み待機中: {filename}")
                return await self.loading_tasks[filename]
            
            # 非同期読み込みタスクを作成
            task = asyncio.create_task(self._load_dialogue_async_worker(filename))
            self.loading_tasks[filename] = task
            
            try:
                result = await task
                return result
            finally:
                # タスク完了後はリストから削除
                if filename in self.loading_tasks:
                    del self.loading_tasks[filename]
                    
        except Exception as e:
            if self.debug:
                print(f"非同期ファイル読み込みエラー: '{filename}': {e}")
            return self.get_default_dialogue()
    
    async def _load_dialogue_async_worker(self, filename):
        """非同期ファイル読み込みワーカー"""
        try:
            # ファイルの存在確認
            if not await asyncio.to_thread(os.path.exists, filename):
                if self.debug:
                    print(f"エラー: ファイル '{filename}' が見つかりません。カレントディレクトリ: {os.getcwd()}")
                return self.get_default_dialogue()
            
            # aiofilesを使って非同期でファイル読み込み
            if AIOFILES_AVAILABLE:
                try:
                    async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
                        content = await f.read()
                except Exception as e:
                    if self.debug:
                        print(f"aiofilesでの読み込みに失敗。ThreadPoolExecutorにフォールバック: {e}")
                    content = await asyncio.to_thread(self._read_file_sync, filename)
            else:
                # aiofilesが利用できない場合は、通常のファイル読み込みを別スレッドで実行
                if self.debug:
                    print("aiofilesが利用できません。ThreadPoolExecutorでファイル読み込み")
                content = await asyncio.to_thread(self._read_file_sync, filename)
            
            # パース処理を別スレッドで実行（CPU集約的な処理のため）
            dialogue_data = await asyncio.to_thread(self._parse_ks_content, content)
            self.ir_data = self._build_ir_skeleton(dialogue_data)
            
            if self.debug:
                print(f"非同期読み込み完了: {len(dialogue_data)} 個の対話エントリーが解析されました")
                
            return dialogue_data
            
        except Exception as e:
            if self.debug:
                print(f"非同期ファイル読み込みワーカーエラー: '{filename}': {e}")
            return self.get_default_dialogue()
    
    def _read_file_sync(self, filename):
        """同期的なファイル読み込み（フォールバック用）"""
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
        
    def get_default_dialogue(self):
        """デフォルトの対話データを辞書形式で返す"""
        return [
            {
                'type': 'dialogue',
                'text': 'デフォルトのテキストです。',
                'character': 'T00_00_00',
                'eye': '',
                'mouth': '',
                'brow': '',
                'cheek': '',
                'background': None,  # 背景はなし（ファイルで指定された場合のみ表示）
                'bgm': None,  # BGMはなし（ファイルで指定された場合のみ再生）
                'bgm_volume': DEFAULT_BGM_VOLUME,
                'bgm_loop': DEFAULT_BGM_LOOP,
                'scroll_continue': False,
                'line_count': 1
            }
        ]
        
    def _parse_ks_content(self, content):    
        dialogue_data = []
        current_bg = None  # 初期背景はなし
        current_char = None
        current_speaker = None
        # キャラクターごとの顔パーツを保存する辞書
        character_face_parts = {}
        current_bgm = None  # 初期BGMはなし
        current_bgm_volume = DEFAULT_BGM_VOLUME
        current_bgm_loop = DEFAULT_BGM_LOOP
        current_show_x = 0.5
        current_show_y = 0.5

        # 行ごとに処理
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            try:
                line = line.strip()

                # 話者の記述を検出 //キャラクター名//
                speaker_match = re.match(r'//([^/]+)//', line)
                if speaker_match:
                    current_speaker = speaker_match.group(1)
                    if self.debug:
                        print(f"話者設定: {current_speaker}")
                    continue

                # 背景設定を検出
                if "[bg" in line and "[bg_show" not in line and "[bg_move" not in line:
                    try:
                        bg_parts = re.search(r'storage="([^"]+)"', line)
                        if bg_parts:
                            current_bg = bg_parts.group(1)
                            # デバッグ出力削除
                            
                            dialogue_data.append({
                                'type': 'background',
                                'value': current_bg
                            })

                    except Exception as e:
                        if self.debug:
                            print(f"背景解析エラー（行 {line_num}）: {e} - {line}")

                # 背景表示コマンドを検出
                elif "[bg_show" in line:
                    try:
                        storage = re.search(r'storage="([^"]+)"', line)
                        x_pos = re.search(r'bg_x="([^"]+)"', line)
                        y_pos = re.search(r'bg_y="([^"]+)"', line)
                        zoom = re.search(r'bg_zoom="([^"]+)"', line)

                        if storage:
                            bg_name = storage.group(1)
                            bg_x = float(x_pos.group(1)) if x_pos else 0.5
                            bg_y = float(y_pos.group(1)) if y_pos else 0.5
                            bg_zoom = float(zoom.group(1)) if zoom else 1.0

                            # デバッグ出力削除

                            dialogue_data.append({
                                'type': 'bg_show',
                                'storage': bg_name,
                                'x': bg_x,
                                'y': bg_y,
                                'zoom': bg_zoom
                            })

                            current_bg = bg_name

                    except Exception as e:
                        if self.debug:
                            print(f"背景表示解析エラー (行{line_num}) : {e} - {line}")

                # 背景移動コマンドを検出 [bg_move]
                elif "[bg_move" in line:
                    try:
                        storage = re.search(r'storage="([^"]+)"', line)
                        sub = re.search(r'sub="([^"]+)"', line)
                        time = re.search(r'time="([^"]+)"', line)
                        left = re.search(r'bg_left="([^"]+)"', line)
                        top = re.search(r'bg_top="([^"]+)"', line)
                        zoom = re.search(r'bg_zoom="([^"]+)"', line)
                        
                        bg_name = storage.group(1) if storage else (sub.group(1) if sub else None)
                        
                        if bg_name and left and top:
                            move_time = time.group(1) if time else "600"
                            move_left = left.group(1)
                            move_top = top.group(1)
                            move_zoom = zoom.group(1) if zoom else "1.0"
                            
                            # デバッグ出力削除
                            
                            dialogue_data.append({
                                'type': 'bg_move',
                                'storage': bg_name,
                                'left': move_left,
                                'top': move_top,
                                'time': move_time,
                                'zoom': move_zoom
                            })

                    except Exception as e:
                        if self.debug:
                            print(f"背景移動解析エラー（行 {line_num}）: {e} - {line}")

                # キャラクターを検出
                elif "[chara_show" in line:
                    try:
                        # name属性（キャラクター論理名）を検索
                        char_name = re.search(r'name="([^"]+)"', line)
                        if not char_name:
                            char_name = re.search(r'sub="([^"]+)"', line)

                        # torso属性（胴体パーツID）を検索（新形式）
                        torso_id = re.search(r'torso="([^"]+)"', line)

                        eye_type = re.search(r'eye="([^"]+)"', line)
                        mouth_type = re.search(r'mouth="([^"]+)"', line)
                        brow_type = re.search(r'brow="([^"]+)"', line)
                        cheek_type = re.search(r'cheek="([^"]+)"', line)
                        blink = re.search(r'blink="([^"]+)"', line)
                        show_x = re.search(r'x="([^"]+)"', line)
                        show_y = re.search(r'y="([^"]+)"', line)
                        size = re.search(r'size="([^"]+)"', line)
                        fade = re.search(r'fade="([^"]+)"', line)
                        fade_time = re.search(r'time="([^"]+)"', line)

                        if char_name:
                            current_char = char_name.group(1)

                            # 後方互換性: torsoが指定されていない場合はnameを使用
                            current_torso = torso_id.group(1) if torso_id else current_char
                            
                            # キャラクターごとの顔パーツを取得（初回の場合は初期化）
                            if current_char not in character_face_parts:
                                character_face_parts[current_char] = {
                                    'eye': "",
                                    'mouth': "",
                                    'brow': "",
                                    'cheek': ""
                                }
                            
                            # 属性が指定されていない場合や空文字の場合は既存の値を保持
                            current_eye = eye_type.group(1) if eye_type and eye_type.group(1) else character_face_parts[current_char]['eye']
                            current_mouth = mouth_type.group(1) if mouth_type and mouth_type.group(1) else character_face_parts[current_char]['mouth']
                            current_brow = brow_type.group(1) if brow_type and brow_type.group(1) else character_face_parts[current_char]['brow']
                            current_cheek = cheek_type.group(1) if cheek_type and cheek_type.group(1) else character_face_parts[current_char]['cheek']
                            
                            # 更新された顔パーツをキャラクター別に保存
                            character_face_parts[current_char]['eye'] = current_eye
                            character_face_parts[current_char]['mouth'] = current_mouth
                            character_face_parts[current_char]['brow'] = current_brow
                            character_face_parts[current_char]['cheek'] = current_cheek

                            # x, y を数値として処理
                            try:
                                current_show_x = float(show_x.group(1)) if show_x else 0.5
                            except (ValueError, AttributeError):
                                current_show_x = 0.5
                                
                            try:
                                current_show_y = float(show_y.group(1)) if show_y else 0.5
                            except (ValueError, AttributeError):
                                current_show_y = 0.5
                            
                            # size パラメータを処理
                            try:
                                current_size = float(size.group(1)) if size else 1.0
                            except (ValueError, AttributeError):
                                current_size = 1.0
                            
                            # blink パラメータを処理（デフォルト: true）
                            try:
                                current_blink = blink.group(1).lower() != "false" if blink else True
                            except (ValueError, AttributeError):
                                current_blink = True

                            fade_source = fade.group(1) if fade else (fade_time.group(1) if fade_time else None)
                            current_fade = None
                            if fade_source is not None:
                                try:
                                    current_fade = float(fade_source)
                                except (ValueError, AttributeError):
                                    current_fade = None

                            # デバッグ出力削除

                            dialogue_data.append({
                                'type': 'character',
                                'name': current_char,
                                'torso': current_torso,  # 胴体パーツID（新規追加）
                                'eye': current_eye,
                                'mouth': current_mouth,
                                'brow': current_brow,
                                'cheek': current_cheek,
                                'blink': current_blink,
                                'show_x': current_show_x,
                                'show_y': current_show_y,
                                'size': current_size,
                                'fade': current_fade
                            })
                        else:
                            if self.debug:
                                print(f"キャラクター名が見つかりません: {line}")

                    except Exception as e:
                        if self.debug:
                            print(f"キャラクター解析エラー（行 {line_num}）: {e} - {line}")
                    
                # BGM一時停止を検出（[BGM より前にチェック）
                
                # chara_shift tag
                elif "[chara_shift" in line:
                    try:
                        char_name = re.search(r'name="([^"]+)"', line)
                        if not char_name:
                            char_name = re.search(r'sub="([^"]+)"', line)

                        torso_id = re.search(r'torso="([^"]+)"', line)
                        eye_type = re.search(r'eye="([^"]+)"', line)
                        mouth_type = re.search(r'mouth="([^"]+)"', line)
                        brow_type = re.search(r'brow="([^"]+)"', line)
                        cheek_type = re.search(r'cheek="([^"]+)"', line)
                        show_x = re.search(r'x="([^"]+)"', line)
                        show_y = re.search(r'y="([^"]+)"', line)
                        size = re.search(r'size="([^"]+)"', line)
                        fade = re.search(r'fade="([^"]+)"', line)
                        fade_time = re.search(r'time="([^"]+)"', line)

                        if char_name:
                            current_char = char_name.group(1)
                            current_torso = torso_id.group(1) if torso_id else None
                            current_eye = eye_type.group(1) if eye_type else ""
                            current_mouth = mouth_type.group(1) if mouth_type else ""
                            current_brow = brow_type.group(1) if brow_type else ""
                            current_cheek = cheek_type.group(1) if cheek_type else ""
                            current_show_x = show_x.group(1) if show_x else None
                            current_show_y = show_y.group(1) if show_y else None
                            current_size = size.group(1) if size else None
                            fade_source = fade.group(1) if fade else (fade_time.group(1) if fade_time else None)
                            current_fade = None
                            if fade_source is not None:
                                try:
                                    current_fade = float(fade_source)
                                except (ValueError, AttributeError):
                                    current_fade = None

                            if current_char not in character_face_parts:
                                character_face_parts[current_char] = {
                                    'eye': "",
                                    'mouth': "",
                                    'brow': "",
                                    'cheek': ""
                                }

                            if eye_type is not None:
                                character_face_parts[current_char]['eye'] = current_eye
                            if mouth_type is not None:
                                character_face_parts[current_char]['mouth'] = current_mouth
                            if brow_type is not None:
                                character_face_parts[current_char]['brow'] = current_brow
                            if cheek_type is not None:
                                character_face_parts[current_char]['cheek'] = current_cheek

                            shift_entry = {
                                'type': 'chara_shift',
                                'name': current_char
                            }
                            if torso_id is not None:
                                shift_entry['torso'] = current_torso
                            if eye_type is not None:
                                shift_entry['eye'] = current_eye
                            if mouth_type is not None:
                                shift_entry['mouth'] = current_mouth
                            if brow_type is not None:
                                shift_entry['brow'] = current_brow
                            if cheek_type is not None:
                                shift_entry['cheek'] = current_cheek
                            if show_x is not None:
                                shift_entry['x'] = current_show_x
                            if show_y is not None:
                                shift_entry['y'] = current_show_y
                            if size is not None:
                                shift_entry['size'] = current_size
                            if current_fade is not None:
                                shift_entry['fade'] = current_fade
                            dialogue_data.append(shift_entry)
                        else:
                            if self.debug:
                                print(f"character name not found: {line}")

                    except Exception as e:
                        if self.debug:
                            print(f"chara_shift parse error (line {line_num}): {e} - {line}")

                elif "[BGMSTOP" in line:
                    try:
                        time_match = re.search(r'time="([^"]+)"', line)
                        fade_time = float(time_match.group(1)) if time_match else 0.0
                        
                        if self.debug:
                            print(f"BGM一時停止コマンド検出: fade_time={fade_time}")
                        
                        dialogue_data.append({
                            'type': 'bgm_pause',
                            'fade_time': fade_time
                        })
                    except Exception as e:
                        if self.debug:
                            print(f"BGMSTOP解析エラー（行 {line_num}）: {e} - {line}")
                        # エラーの場合はフェードなしで追加
                        dialogue_data.append({
                            'type': 'bgm_pause',
                            'fade_time': 0.0
                        })
                
                # BGM再生開始を検出（[BGM より前にチェック）
                elif "[BGMSTART" in line:
                    try:
                        time_match = re.search(r'time="([^"]+)"', line)
                        fade_time = float(time_match.group(1)) if time_match else 0.0
                        
                        if self.debug:
                            print(f"BGM再生開始コマンド検出: fade_time={fade_time}")
                        
                        dialogue_data.append({
                            'type': 'bgm_unpause',
                            'fade_time': fade_time
                        })
                    except Exception as e:
                        if self.debug:
                            print(f"BGMSTART解析エラー（行 {line_num}）: {e} - {line}")
                        # エラーの場合はフェードなしで追加
                        dialogue_data.append({
                            'type': 'bgm_unpause',
                            'fade_time': 0.0
                        })
                
                # BGM設定を検出
                elif "[BGM" in line:
                    try:
                        bgm_parts = re.search(r'bgm="([^"]+)"', line)
                        bgm_volume = re.search(r'volume="([^"]+)"', line)
                        bgm_loop = re.search(r'loop="([^"]+)"', line)
                        if bgm_parts:
                            # BGMファイル名をマッピング
                            bgm_name = bgm_parts.group(1)
                            if bgm_name == "school":
                                current_bgm = None  # 初期BGMはなし
                            elif bgm_name == "classroom":
                                current_bgm = self.bgm_manager.SECOND_BGM
                            else:
                                current_bgm = bgm_name
                            
                            current_bgm_volume = float(bgm_volume.group(1)) if bgm_volume else DEFAULT_BGM_VOLUME
                            current_bgm_loop = bgm_loop.group(1).lower() == "true" if bgm_loop else DEFAULT_BGM_LOOP
                            
                            # デバッグ出力削除

                            dialogue_data.append({
                                'type': 'bgm',
                                'file': current_bgm,
                                'volume': current_bgm_volume,
                                'loop': current_bgm_loop
                            })  
                                
                    except Exception as e:
                        if self.debug:
                            print(f"BGM解析エラー（行 {line_num}）: {e} - {line}")
                        
                # SE設定を検出
                elif "[SE" in line:
                    try:
                        se_parts = re.search(r'se="([^"]+)"', line)
                        se_volume = re.search(r'volume="([^"]+)"', line)
                        se_frequency = re.search(r'frequency="([^"]+)"', line)
                        if se_parts:
                            se_name = se_parts.group(1)
                            se_vol = float(se_volume.group(1)) if se_volume else 0.5
                            se_freq = int(se_frequency.group(1)) if se_frequency else 1
                            
                            dialogue_data.append({
                                'type': 'se',
                                'file': se_name,
                                'volume': se_vol,
                                'frequency': se_freq
                            })
                                
                    except Exception as e:
                        if self.debug:
                            print(f"SE解析エラー（行 {line_num}）: {e} - {line}")
                        
                # キャラクター移動コマンドを検出
                elif "[chara_move" in line:
                    try:
                        # name属性を優先、なければsubmにフォールバック
                        name_parts_m = re.search(r'name="([^"]+)"', line)
                        if not name_parts_m:
                            name_parts_m = re.search(r'subm="([^"]+)"', line)
                        time = re.search(r'time="([^"]+)"', line)
                        left = re.search(r'left="([^"]+)"', line)
                        top = re.search(r'top="([^"]+)"', line)
                        zoom = re.search(r'zoom="([^"]+)"', line)
                        if name_parts_m and left and top:
                            char_name = name_parts_m.group(1)
                            move_time = time.group(1) if time else "600"
                            move_left = left.group(1)
                            move_top = top.group(1)
                            move_zoom = zoom.group(1) if zoom else "1.0"
                            
                            # デバッグ出力削除
                            
                            # 移動コマンドをダイアログデータに追加
                            dialogue_data.append({
                                'type': 'move',
                                'character': char_name,
                                'left': move_left,
                                'top': move_top,
                                'time': move_time,
                                'zoom': move_zoom
                            })

                    except Exception as e:
                        if self.debug:
                            print(f"キャラクター移動解析エラー（行 {line_num}）: {e} - {line}")

                # キャラクター退場コマンドを検出
                elif "[chara_hide" in line:
                    try:
                        # name属性を優先、なければsubhにフォールバック
                        name_parts_h = re.search(r'name="([^"]+)"', line)
                        if not name_parts_h:
                            name_parts_h = re.search(r'subh="([^"]+)"', line)
                        if name_parts_h:
                            char_name = name_parts_h.group(1)
                            fade = re.search(r'fade="([^"]+)"', line)
                            fade_time = re.search(r'time="([^"]+)"', line)
                            fade_source = fade.group(1) if fade else (fade_time.group(1) if fade_time else None)
                            current_fade = None
                            if fade_source is not None:
                                try:
                                    current_fade = float(fade_source)
                                except (ValueError, AttributeError):
                                    current_fade = None
                            
                            # デバッグ出力削除
                            
                            # 退場コマンドをダイアログデータに追加
                            dialogue_data.append({
                                'type': 'hide',
                                'character': char_name,
                                'fade': current_fade
                            })

                            # 退場したキャラクターが現在のキャラクターだった場合、リセット
                            if current_char == char_name:
                                current_char = None

                    except Exception as e:
                        if self.debug:
                            print(f"キャラクター退場解析エラー（行 {line_num}）: {e} - {line}")
                            
                # セリフを検出
                elif "「" in line and "」" in line:
                    try:
                        if self.debug:
                            print(f"セリフ検出: 行{line_num}: {line}")
                        # [en]タグを除去してからセリフを抽出（消去予定）
                        clean_line = re.sub(r'\[en\]', '', line)
                        dialogue_matches = re.findall(r'「([^」]+)」', clean_line)
                        if self.debug:
                            print(f"セリフ抽出結果: {dialogue_matches}")

                        # [scroll-stop]タグがあるかチェック
                        has_scroll_stop = '[scroll-stop]' in line
                        
                        for dialogue_text in dialogue_matches:
                            dialogue_text = dialogue_text.strip()
                            if dialogue_text:
                                dialogue_speaker = current_speaker if current_speaker else current_char

                                # テキストの行数を計算（26文字改行考慮）
                                line_count = self._wrap_text_and_count_lines(dialogue_text)

                                # スクロール継続判定ロジック - [scroll-stop]の直後のみ新規スクロール開始
                                scroll_continue = False
                                if not self.disable_scroll_continue and not has_scroll_stop:
                                    if dialogue_data:
                                        # 後ろから順に検索して、最後のscroll-stopまたは対話を見つける
                                        found_dialogue_or_stop = False
                                        for i in range(len(dialogue_data) - 1, -1, -1):
                                            item = dialogue_data[i]
                                            if item.get('type') == 'scroll_stop':
                                                # 最後にscroll-stopがあったら新規スクロール開始
                                                scroll_continue = False
                                                found_dialogue_or_stop = True
                                                break
                                            elif item.get('type') == 'dialogue':
                                                # 最後にscroll-stopがなければスクロールを継続
                                                scroll_continue = True
                                                found_dialogue_or_stop = True
                                                break
                                            # その他の全てのコマンドは無視して継続検索

                                        # dialogueもscroll_stopも見つからなかった場合（全てコマンド）
                                        # 最初の台詞ではないのでスクロールを継続
                                        if not found_dialogue_or_stop:
                                            scroll_continue = True

                                # 対話データを追加
                                if self.debug:
                                    print(f"対話データを追加: speaker={dialogue_speaker}, text='{dialogue_text}'")
                                
                                # 話者の顔パーツを取得
                                speaker_face_parts = character_face_parts.get(dialogue_speaker, {
                                    'eye': "",
                                    'mouth': "",
                                    'brow': "",
                                    'cheek': ""
                                })
                                
                                dialogue_data.append({
                                    'type': 'dialogue',
                                    'text': dialogue_text,
                                    'character': dialogue_speaker,
                                    'eye': speaker_face_parts['eye'],
                                    'mouth': speaker_face_parts['mouth'],
                                    'brow': speaker_face_parts['brow'],
                                    'cheek': speaker_face_parts['cheek'],
                                    'background': current_bg,
                                    'bgm': current_bgm,
                                    'bgm_volume': current_bgm_volume,
                                    'bgm_loop': current_bgm_loop,
                                    'scroll_continue': scroll_continue,
                                    'line_count': line_count
                                })

                                # [scroll-stop]タグがある場合はスクロール停止コマンドを追加
                                if has_scroll_stop:
                                    if self.debug:
                                        print(f"スクロール停止コマンド追加")
                                    dialogue_data.append({
                                        'type': 'scroll_stop'
                                    })
                    
                    except Exception as e:
                        if self.debug:
                            print(f"セリフ解析エラー（行 {line_num}）: {e} - {line}")

                # [choice]タグを検出
                elif "[choice" in line:
                    try:
                        # option1 ～ option9 を抽出
                        option_pattern = re.compile(r'option(\d+)="([^"]+)"')

                        options = []
                        for match in option_pattern.finditer(line):
                            idx = int(match.group(1))
                            if 1 <= idx <= 9:
                                options.append(match.group(2))

                        
                        if len(options) >= 2:  # 最低2つの選択肢が必要
                            if self.debug:
                                print(f"選択肢検出: {options}")
                            
                            dialogue_data.append({
                                'type': 'choice',
                                'options': options
                            })
                        else:
                            if self.debug:
                                print(f"選択肢の形式が正しくありません（最低2つの選択肢が必要）: {line}")
                    
                    except Exception as e:
                        if self.debug:
                            print(f"選択肢解析エラー（行 {line_num}）: {e} - {line}")

                # [scroll-stop]タグを独立して検出
                elif "[scroll-stop]" in line:
                    if self.debug:
                        print(f"独立したスクロール停止コマンド")
                    dialogue_data.append({
                        'type': 'scroll_stop'
                    })

                # [event_control]????? - ???????/???
                elif "[event_control" in line:
                    try:
                        unlock_match = re.search(r'unlock="([^"]+)"', line)
                        lock_match = re.search(r'lock="([^"]+)"', line)
                        events_match = re.search(r'events="([^"]+)"', line)
                        target_events = re.search(r'target="([^"]+)"', line)

                        if unlock_match:
                            unlock_list = unlock_match.group(1).split(',')
                        elif events_match:
                            unlock_list = events_match.group(1).split(',')
                        elif target_events:
                            unlock_list = target_events.group(1).split(',')
                        else:
                            unlock_list = []

                        lock_list = lock_match.group(1).split(',') if lock_match else []

                        unlock_list = [event.strip() for event in unlock_list if event.strip()]
                        lock_list = [event.strip() for event in lock_list if event.strip()]

                        if self.debug:
                            print(f"??????(event_control): ??={unlock_list}, ???={lock_list}")

                        dialogue_data.append({
                            'type': 'event_control',
                            'unlock': unlock_list,
                            'lock': lock_list
                        })

                    except Exception as e:
                        if self.debug:
                            print(f"??????(event_control)??????? {line_num}?: {e} - {line}")



                # [flag_set]????? - ??????????タグを検出 - ストーリーフラグ設定
                elif "[flag_set" in line:
                    try:
                        flag_name = re.search(r'name="([^"]+)"', line)
                        flag_value = re.search(r'value="([^"]+)"', line)
                        
                        if flag_name and flag_value:
                            flag_name_str = flag_name.group(1)
                            flag_value_str = flag_value.group(1)
                            
                            # 値の型変換
                            if flag_value_str.lower() == 'true':
                                flag_value_converted = True
                            elif flag_value_str.lower() == 'false':
                                flag_value_converted = False
                            elif flag_value_str.isdigit():
                                flag_value_converted = int(flag_value_str)
                            else:
                                flag_value_converted = flag_value_str
                            
                            if self.debug:
                                print(f"フラグ設定: {flag_name_str} = {flag_value_converted}")
                            
                            dialogue_data.append({
                                'type': 'flag_set',
                                'name': flag_name_str,
                                'value': flag_value_converted
                            })
                        
                    except Exception as e:
                        if self.debug:
                            print(f"フラグ設定解析エラー（行 {line_num}）: {e} - {line}")

                # [if]タグを検出 - 条件分岐開始
                elif "[if" in line:
                    try:
                        condition = re.search(r'condition="([^"]+)"', line)
                        
                        if condition:
                            condition_str = condition.group(1)
                            
                            if self.debug:
                                print(f"条件分岐開始: {condition_str}")
                            
                            dialogue_data.append({
                                'type': 'if_start',
                                'condition': condition_str
                            })
                        
                    except Exception as e:
                        if self.debug:
                            print(f"条件分岐解析エラー（行 {line_num}）: {e} - {line}")

                # [fadeout]タグを検出 - フェードアウト
                elif "[fadeout" in line:
                    try:
                        color_match = re.search(r'color="([^"]+)"', line)
                        time_match = re.search(r'time="([^"]+)"', line)
                        
                        fade_color = color_match.group(1) if color_match else "black"
                        fade_time = float(time_match.group(1)) if time_match else 1.0
                        
                        print(f"[FADE] フェードアウト解析: line='{line}', color={fade_color}, time={fade_time}")
                        
                        dialogue_data.append({
                            'type': 'fadeout',
                            'color': fade_color,
                            'time': fade_time
                        })
                        
                    except Exception as e:
                        print(f"[FADE] フェードアウト解析エラー（行 {line_num}）: {e} - {line}")

                # [fadein]タグを検出 - フェードイン
                elif "[fadein" in line:
                    try:
                        time_match = re.search(r'time="([^"]+)"', line)
                        
                        fade_time = float(time_match.group(1)) if time_match else 1.0
                        
                        print(f"[FADE] フェードイン解析: line='{line}', time={fade_time}")
                        
                        dialogue_data.append({
                            'type': 'fadein',
                            'time': fade_time
                        })
                        
                    except Exception as e:
                        print(f"[FADE] フェードイン解析エラー（行 {line_num}）: {e} - {line}")

                # [endif]タグを検出 - 条件分岐終了
                elif "[endif]" in line:
                    if self.debug:
                        print(f"条件分岐終了")
                    dialogue_data.append({
                        'type': 'if_end'
                    })

            except Exception as e:
                    if self.debug:
                        print(f"ダイアログ読み取りエラー")
    
        if not dialogue_data:
            if self.debug:
                print("警告: 対話データが見つかりませんでした。")
            return self.get_default_dialogue()

        if self.debug:
            print(f"解析完了: {len(dialogue_data)} 個の辞書エントリーを返します")

        return dialogue_data

    def _build_ir_skeleton(self, dialogue_data):
        """Build a minimal IR skeleton alongside existing dialogue data."""
        steps = []
        if not dialogue_data:
            return {"steps": steps}

        for index, entry in enumerate(dialogue_data, 1):
            step_id = f"step_{index:04d}"
            if isinstance(entry, dict) and entry.get("type") == "dialogue":
                text = make_text(
                    speaker=entry.get("character", ""),
                    body=entry.get("text", ""),
                    scroll=bool(entry.get("scroll_continue", False)),
                )
                steps.append(make_step(step_id=step_id, text=text))
                continue

            if isinstance(entry, dict):
                action = entry.get("type", "unknown")
                target = entry.get("character") or entry.get("name")
                params = {k: v for k, v in entry.items() if k != "type"}
                steps.append(
                    make_step(
                        step_id=step_id,
                        actions=[make_action(action=action, target=target, params=params)],
                    )
                )
                continue

            steps.append(make_step(step_id=step_id))

        return {"steps": steps}

    def set_max_chars_per_line(self, max_chars):
        """1行あたりの最大文字数を設定"""
        self.max_chars_per_line = max_chars
        if self.debug:
            print(f"dialogue_loader: 1行あたりの最大文字数を{max_chars}文字に設定")
    
    def enable_scroll_continue(self, enable=True):
        """スクロール継続機能の有効/無効を切り替え"""
        self.disable_scroll_continue = not enable
        if self.debug:
            print(f"スクロール継続機能: {'有効' if enable else '無効'}")
    
    def load_story_flags(self):
        """ストーリーフラグを読み込み"""
        import json
        flags_file = os.path.join("events", "story_flags.json")
        
        try:
            if os.path.exists(flags_file):
                with open(flags_file, 'r', encoding='utf-8') as f:
                    self.story_flags = json.load(f)
                if self.debug:
                    print(f"✅ ストーリーフラグ読み込み完了: {len(self.story_flags)}個")
            else:
                self.story_flags = {}
                if self.debug:
                    print("📝 新しいストーリーフラグファイルを作成します")
        except Exception as e:
            if self.debug:
                print(f"❌ ストーリーフラグ読み込みエラー: {e}")
            self.story_flags = {}
    
    def save_story_flags(self):
        """ストーリーフラグを保存"""
        import json
        flags_file = os.path.join("events", "story_flags.json")
        
        try:
            # eventsディレクトリが存在しない場合は作成
            os.makedirs("events", exist_ok=True)
            
            with open(flags_file, 'w', encoding='utf-8') as f:
                json.dump(self.story_flags, f, ensure_ascii=False, indent=2)
            if self.debug:
                print(f"✅ ストーリーフラグ保存完了: {len(self.story_flags)}個")
        except Exception as e:
            if self.debug:
                print(f"❌ ストーリーフラグ保存エラー: {e}")
    
    async def save_story_flags_async(self):
        """ストーリーフラグを非同期で保存"""
        import json
        flags_file = os.path.join("events", "story_flags.json")
        
        try:
            # eventsディレクトリが存在しない場合は作成
            await asyncio.to_thread(os.makedirs, "events", exist_ok=True)
            
            # JSON文字列作成を別スレッドで実行
            json_content = await asyncio.to_thread(
                json.dumps, 
                self.story_flags, 
                ensure_ascii=False, 
                indent=2
            )
            
            # ファイル書き込みを非同期で実行
            if AIOFILES_AVAILABLE:
                try:
                    async with aiofiles.open(flags_file, 'w', encoding='utf-8') as f:
                        await f.write(json_content)
                except Exception as e:
                    if self.debug:
                        print(f"aiofilesでの書き込みに失敗。ThreadPoolExecutorにフォールバック: {e}")
                    await asyncio.to_thread(self._write_file_sync, flags_file, json_content)
            else:
                # aiofilesが利用できない場合は別スレッドで実行
                await asyncio.to_thread(self._write_file_sync, flags_file, json_content)
            
            if self.debug:
                print(f"✅ ストーリーフラグ非同期保存完了: {len(self.story_flags)}個")
        except Exception as e:
            if self.debug:
                print(f"❌ ストーリーフラグ非同期保存エラー: {e}")
    
    def _write_file_sync(self, filepath, content):
        """同期的なファイル書き込み（フォールバック用）"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def set_story_flag(self, flag_name, value):
        """ストーリーフラグを設定"""
        self.story_flags[flag_name] = value
        self.save_story_flags()
        if self.debug:
            print(f"🚩 フラグ設定: {flag_name} = {value}")
    
    def get_story_flag(self, flag_name, default=False):
        """ストーリーフラグを取得"""
        return self.story_flags.get(flag_name, default)
    
    def record_choice(self, choice_index, choice_text):
        """選択肢の記録（0ベースのインデックス）"""
        if self.current_ks_file:
            self.choice_counter += 1
            choice_number = self.choice_counter
            
            # 履歴に追加
            if self.current_ks_file not in self.choice_history:
                self.choice_history[self.current_ks_file] = []
            
            choice_record = {
                'number': choice_number,
                'index': choice_index,
                'text': choice_text
            }
            self.choice_history[self.current_ks_file].append(choice_record)
            
            # フラグとして保存（条件分岐で使用可能）
            flag_name = f"choice_{choice_number}"
            self.set_story_flag(flag_name, choice_index + 1)  # 1ベースで保存
            
            if self.debug:
                print(f"選択肢記録: {flag_name} = {choice_index + 1} ('{choice_text}')")
            
            return choice_number
        return None
    
    def get_choice_text(self, choice_number):
        """選択肢番号から選択肢テキストを取得"""
        if self.current_ks_file and self.current_ks_file in self.choice_history:
            for choice in self.choice_history[self.current_ks_file]:
                if choice['number'] == choice_number:
                    return choice['text']
        return f"{{選択肢{choice_number}}}"  # フォールバック
    
    def clear_current_file_choices(self):
        """現在のファイルの選択肢履歴をクリア"""
        if self.current_ks_file:
            self.choice_history[self.current_ks_file] = []
            self.choice_counter = 0
            if self.debug:
                print(f"選択肢履歴クリア: {self.current_ks_file}")
    
    def check_condition(self, condition_str):
        """条件文字列を評価"""
        try:
            # シンプルな条件評価（例: "aggressive_approach==true"）
            if "==" in condition_str:
                flag_name, expected_value = condition_str.split("==")
                flag_name = flag_name.strip()
                expected_value = expected_value.strip()
                
                # 値の型変換
                if expected_value.lower() == 'true':
                    expected_value = True
                elif expected_value.lower() == 'false':
                    expected_value = False
                elif expected_value.isdigit():
                    expected_value = int(expected_value)
                else:
                    expected_value = expected_value.strip('"\'')  # クォートを除去
                
                current_value = self.get_story_flag(flag_name)
                result = current_value == expected_value
                # 条件評価は常にログ出力（デバッグ用）
                print(f"[CONDITION] 条件評価: {flag_name}({current_value}) == {expected_value} → {result}")
                return result
            
            # AND/OR条件（基本的な実装）
            elif " AND " in condition_str:
                conditions = condition_str.split(" AND ")
                return all(self.check_condition(cond.strip()) for cond in conditions)
            elif " OR " in condition_str:
                conditions = condition_str.split(" OR ")
                return any(self.check_condition(cond.strip()) for cond in conditions)
            
            return False
            
        except Exception as e:
            if self.debug:
                print(f"❌ 条件評価エラー: {e} - {condition_str}")
            return False
    
    
    def unlock_events(self, event_list):
        """イベントリストを解禁する（completed_events.csvの有効フラグを更新）"""
        if not event_list:
            return
            
        try:
            import csv
            # 静的DBは読み込み専用、動的データはcompleted_events.csvに書き込み
            events_csv_path = os.path.join("events", "events.csv")
            completed_csv_path = os.path.join("data", "current_state", "completed_events.csv")
            
            if not os.path.exists(completed_csv_path):
                print(f"❌ completed_events.csvが見つかりません: {completed_csv_path}")
                return
            
            # completed_events.csvファイル読み込み
            rows = []
            with open(completed_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # 静的DBから解禁対象イベントの詳細情報を取得
            event_details = {}
            if os.path.exists(events_csv_path):
                with open(events_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('イベントID') in event_list:
                            event_details[row['イベントID']] = {
                                'heroine': row.get('対象のヒロイン', 'unknown'),
                                'title': row.get('イベントのタイトル', '')
                            }
            
            # 指定されたイベントを解禁（E***番号順に並び替え）
            unlocked_count = 0
            unlocked_events = []
            
            # E***番号順にソート
            sorted_event_list = sorted(event_list, key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
            print(f"[EVENT_UNLOCK] イベント解禁順序: {sorted_event_list}")
            
            for event_id in sorted_event_list:
                for row in rows:
                    if row.get('イベントID') == event_id:
                        if row.get('有効フラグ') != 'TRUE':
                            row['有効フラグ'] = 'TRUE'
                            unlocked_count += 1
                            details = event_details.get(event_id, {})
                            heroine_name = details.get('heroine', 'unknown')
                            event_title = details.get('title', '')
                            unlocked_events.append({
                                'id': event_id,
                                'heroine': heroine_name,
                                'title': event_title
                            })
                            print(f"🔓 イベント解禁: {event_id} - {heroine_name}: {event_title}")
                        break
            
            # completed_events.csvに書き込み（静的DBのevents.csvは保護）
            fieldnames = ['イベントID', '実行日時', '実行回数', '有効フラグ']
            with open(completed_csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            # 通知システムに順番に通知を送信（E***番号順）
            if self.notification_system and unlocked_events:
                print(f"[NOTIFICATION] {len(unlocked_events)}個のイベント解禁通知を送信")
                for event in unlocked_events:
                    notification_msg = f"{event['heroine']}のイベントが解禁されました"
                    self.notification_system.add_notification(notification_msg)
                    print(f"[NOTIFICATION] 通知送信: {notification_msg}")
            elif unlocked_events:
                print(f"[NOTIFICATION] 通知システムが利用できません: notification_system={self.notification_system}")
            
            print(f"📝 イベント解禁完了: {unlocked_count}個のイベントを解禁")
            
        except Exception as e:
            print(f"❌ イベント解禁エラー: {e}")
    
    def _get_heroine_name_from_event(self, event_id):
        """イベントIDからヒロイン名を取得"""
        # events.csvからヒロイン名を取得
        try:
            import csv
            csv_path = os.path.join("events", "events.csv")
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('イベントID') == event_id:
                        return row.get('対象のヒロイン', '不明')
        except:
            pass
        
        return "不明"
    
    def update_completed_events_flags(self, unlock_events=[], lock_events=[]):
        """completed_events.csvの有効フラグを動的に更新（events.csvは読み込み専用）"""
        import csv
        completed_csv_path = os.path.join("data", "current_state", "completed_events.csv")
        
        try:
            # completed_events.csvを読み込み
            rows = []
            with open(completed_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 解放対象のイベント
                    if row['イベントID'] in unlock_events:
                        row['有効フラグ'] = 'TRUE'
                        if self.debug:
                            print(f"✅ イベント解放: {row['イベントID']}")
                    
                    # ロック対象のイベント  
                    if row['イベントID'] in lock_events:
                        row['有効フラグ'] = 'FALSE'
                        if self.debug:
                            print(f"🔒 イベントロック: {row['イベントID']}")
                    
                    rows.append(row)
            
            # completed_events.csvに書き込み（静的DBのevents.csvは保護）
            with open(completed_csv_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['イベントID', '実行日時', '実行回数', '有効フラグ']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            if self.debug:
                print(f"📝 completed_events.csv更新完了: 解放{len(unlock_events)}個, ロック{len(lock_events)}個")
            
        except Exception as e:
            if self.debug:
                print(f"❌ イベントフラグ更新エラー: {e}")

    def execute_story_command(self, command_data):
        """ストーリーコマンドを実行"""
        command_type = command_data.get('type')
        
        if command_type == 'event_control':
            unlock_events = command_data.get('unlock', [])
            lock_events = command_data.get('lock', [])
            self.update_completed_events_flags(unlock_events, lock_events)
            
        elif command_type == 'flag_set':
            flag_name = command_data.get('name')
            flag_value = command_data.get('value')
            self.set_story_flag(flag_name, flag_value)
            
            
        elif command_type == 'check_condition':
            condition = command_data.get('condition', '')
            return self.check_condition(condition)
            
        return None
    
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
            print("DialogueLoader: リソースクリーンアップ完了")
