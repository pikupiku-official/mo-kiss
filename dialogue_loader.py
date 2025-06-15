import re
import os
from bgm_manager import BGMManager
from config import *

class DialogueLoader:
    def __init__(self, debug=False):
        self.debug = debug
        self.bgm_manager = BGMManager(debug)
        # キャラクター名と画像ファイル名の対応付け
        self.character_image_map = CHARACTER_IMAGE_MAP
        # 26文字改行設定
        self.max_chars_per_line = 26
        
        # 3行制限テスト用：スクロール継続を無効化
        self.disable_scroll_continue = True  # テスト用フラグ

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
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 対話データを解析
            dialogue_data = self._parse_ks_content(content)

            if self.debug:
                print(f"{len(dialogue_data)} 個の対話エントリーが解析されました")

            return dialogue_data
        
        except Exception as e:
            if self.debug:
                print(f"エラー: '{filename}' の読み込みに失敗しました: {e}")
            else:
                print(f"{filename}の読み込みに失敗しました: {e}")
                return self.get_default_dialogue()
        
    def get_default_dialogue(self):
        """デフォルトの対話データを辞書形式で返す"""
        return [
            {
                'type': 'dialogue',
                'text': 'デフォルトのテキストです。',
                'character': 'girl1',
                'eye': 'eye1',
                'mouth': 'mouth1',
                'brow': 'brow1',
                'background': DEFAULT_BACKGROUND,
                'bgm': self.bgm_manager.DEFAULT_BGM,
                'bgm_volume': DEFAULT_BGM_VOLUME,
                'bgm_loop': DEFAULT_BGM_LOOP,
                'scroll_continue': False,
                'line_count': 1
            }
        ]
        
    def _parse_ks_content(self, content):    
        dialogue_data = []
        current_bg = DEFAULT_BACKGROUND
        current_char = None
        current_speaker = None
        current_eye = "eye1"
        current_mouth = "mouth1"
        current_brow = "brow1"
        current_bgm = self.bgm_manager.DEFAULT_BGM
        current_bgm_volume = DEFAULT_BGM_VOLUME
        current_bgm_loop = DEFAULT_BGM_LOOP
        current_show_x = 0.5
        current_show_y = 0.5

        # 行ごとに処理
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            try:
                line = line.strip()

                # 話者の記述を検出 [キャラクター名]
                speaker_match = re.match(r'\//([^\]]+)\//', line)
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
                            if self.debug:
                                print(f"背景: {current_bg}")
                            
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

                            if self.debug:
                                print(f"背景表示: {bg_name}, bg_x={bg_x}, bg_y={bg_y}, bg_zoom={bg_zoom}")

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
                            
                            if self.debug:
                                print(f"背景移動: {bg_name}, 位置: ({move_left}, {move_top}), 時間: {move_time}, bg_zoom: {move_zoom}")
                            
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
                        # name属性またはsub属性を検索
                        char_name = re.search(r'name="([^"]+)"', line)
                        if not char_name:
                            char_name = re.search(r'sub="([^"]+)"', line)
                        
                        eye_type = re.search(r'eye="([^"]+)"', line)
                        mouth_type = re.search(r'mouth="([^"]+)"', line)
                        brow_type = re.search(r'brow="([^"]+)"', line)
                        show_x = re.search(r'x="([^"]+)"', line)
                        show_y = re.search(r'y="([^"]+)"', line)
                        
                        if char_name:
                            current_char = char_name.group(1)
                            # 属性が指定されていない場合はデフォルト値を使用
                            current_eye = eye_type.group(1) if eye_type else "eye1"
                            current_mouth = mouth_type.group(1) if mouth_type else "mouth1"
                            current_brow = brow_type.group(1) if brow_type else ""

                            # x, y を数値として処理
                            try:
                                current_show_x = float(show_x.group(1)) if show_x else 0.5
                            except (ValueError, AttributeError):
                                current_show_x = 0.5
                                
                            try:
                                current_show_y = float(show_y.group(1)) if show_y else 0.5
                            except (ValueError, AttributeError):
                                current_show_y = 0.5
                            
                            if self.debug:
                                print(f"キャラクター登場: {current_char}, 目: {current_eye}, 口: {current_mouth}, 眉: {current_brow}, x={current_show_x}, y={current_show_y}") 

                            dialogue_data.append({
                                'type': 'character',
                                'name': current_char,
                                'eye': current_eye,
                                'mouth': current_mouth,
                                'brow': current_brow,
                                'show_x': current_show_x,
                                'show_y': current_show_y
                            })
                        else:
                            if self.debug:
                                print(f"キャラクター名が見つかりません: {line}")

                    except Exception as e:
                        if self.debug:
                            print(f"キャラクター解析エラー（行 {line_num}）: {e} - {line}")
                    
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
                                current_bgm = self.bgm_manager.DEFAULT_BGM
                            elif bgm_name == "classroom":
                                current_bgm = self.bgm_manager.SECOND_BGM
                            else:
                                current_bgm = bgm_name
                            
                            current_bgm_volume = float(bgm_volume.group(1)) if bgm_volume else DEFAULT_BGM_VOLUME
                            current_bgm_loop = bgm_loop.group(1).lower() == "true" if bgm_loop else DEFAULT_BGM_LOOP
                            
                            if self.debug:
                                print(f"BGM: {current_bgm}, BGM音量: {current_bgm_volume}, BGMループ: {current_bgm_loop}")

                            dialogue_data.append({
                                'type': 'bgm',
                                'file': current_bgm,
                                'volume': current_bgm_volume,
                                'loop': current_bgm_loop
                            })  
                                
                    except Exception as e:
                        if self.debug:
                            print(f"BGM解析エラー（行 {line_num}）: {e} - {line}")
                        
                # キャラクター移動コマンドを検出
                elif "[chara_move" in line:
                    try:
                        name_parts_m = re.search(r'subm="([^"]+)"', line)
                        time = re.search(r'time="([^"]+)"', line)
                        left = re.search(r'left="([^"]+)"', line)
                        top = re.search(r'top="([^"]+)"', line)
                        zoom = re.search(r'zoom="([^"]+)"', line)
                        if name_parts_m and left and top and zoom:
                            char_name = name_parts_m.group(1)
                            move_time = time.group(1) if time else "600"
                            move_left = left.group(1)
                            move_top = top.group(1)
                            move_zoom = zoom.group(1) if zoom else "1.0"
                            
                            if self.debug:
                                print(f"キャラクター移動: {char_name}, 位置: ({move_left}, {move_top}), 時間: {move_time}, 拡大縮小: {move_zoom}")
                            
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
                        name_parts_h = re.search(r'subh="([^"]+)"', line)
                        if name_parts_h:
                            char_name = name_parts_h.group(1)
                            
                            if self.debug:
                                print(f"キャラクター退場: {char_name}")
                            
                            # 退場コマンドをダイアログデータに追加
                            dialogue_data.append({
                                'type': 'hide',
                                'character': char_name
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
                        # [en]タグを除去してからセリフを抽出（消去予定）
                        clean_line = re.sub(r'\[en\]', '', line)
                        dialogue_matches = re.findall(r'「([^」]+)」', clean_line)

                        # [scroll-stop]タグがあるかチェック
                        has_scroll_stop = '[scroll-stop]' in line
                        
                        for dialogue_text in dialogue_matches:
                            dialogue_text = dialogue_text.strip()
                            if dialogue_text:
                                dialogue_speaker = current_speaker if current_speaker else current_char

                                # テキストの行数を計算（26文字改行考慮）
                                line_count = self._wrap_text_and_count_lines(dialogue_text)

                                # 3行制限テスト用：スクロール継続を無効化
                                scroll_continue = False
                                if not self.disable_scroll_continue:
                                    # 元のスクロール継続判定ロジック
                                    if dialogue_data and not has_scroll_stop:
                                        # 後ろから順に検索して、最後の対話を見つける
                                        for i in range(len(dialogue_data) - 1, -1, -1):
                                            item = dialogue_data[i]
                                            if item.get('type') == 'dialogue':
                                                # 最後の対話が同じ話者なら継続
                                                if item.get('character') == dialogue_speaker:
                                                    scroll_continue = True
                                                break
                                            # scroll-stopコマンドがあったら中断
                                            elif item.get('type') == 'scroll_stop':
                                                scroll_continue = False
                                                break
                                            # その他のコマンドは無視して継続検索
                                            elif item.get('type') in ['character', 'bgm', 'move', 'hide', 'bg_show', 'bg_move']:
                                                continue
                                            else:
                                                break

                                if self.debug:
                                    print(f"セリフ: {dialogue_text}, 話者: {dialogue_speaker}, 行数: {line_count}, スクロール継続: {scroll_continue} (無効化: {self.disable_scroll_continue})")
                                
                                # 対話データを追加
                                dialogue_data.append({
                                    'type': 'dialogue',
                                    'text': dialogue_text,
                                    'character': dialogue_speaker,
                                    'eye': current_eye,
                                    'mouth': current_mouth,
                                    'brow': current_brow,
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

                # [scroll-stop]タグを独立して検出
                elif "[scroll-stop]" in line:
                    if self.debug:
                        print(f"独立したスクロール停止コマンド")
                    dialogue_data.append({
                        'type': 'scroll_stop'
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