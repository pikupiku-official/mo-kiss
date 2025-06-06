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
        """デフォルトの対話データを返す"""
        return [
            [DEFAULT_BACKGROUND, "girl1", "", "", "", "デフォルトのテキストです。", 
             self.bgm_manager.DEFAULT_BGM, DEFAULT_BGM_VOLUME, DEFAULT_BGM_LOOP, "", False]
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
                            current_brow = brow_type.group(1) if brow_type else "brow1"

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
                        
                        for dialogue_text in dialogue_matches:
                            dialogue_text = dialogue_text.strip()
                            if dialogue_text:
                                dialogue_speaker = current_speaker if current_speaker else current_char

                                # スクロール継続フラグを追加 - 背景変更後は必ずFalse
                                scroll_continue = False
                                if dialogue_data:
                                    # 後ろから順に検索して、最後の対話を見つける
                                    for i in range(len(dialogue_data) - 1, -1, -1):
                                        item = dialogue_data[i]
                                        if item.get('type') == 'dialogue':
                                            # 最後の対話が同じ話者なら継続
                                            if item.get('character') == dialogue_speaker:
                                                scroll_continue = True
                                            break
                                        # 背景変更コマンドがあったら必ず中断
                                        elif item.get('type') in ['bg_show', 'bg_move']:
                                            scroll_continue = False
                                            break
                                        # キャラクター登場は無視して継続検索
                                        elif item.get('type') in ['character', 'bgm']:
                                            continue
                                        # 移動・退場コマンドがあったら中断
                                        elif item.get('type') in ['move', 'hide']:
                                            break
                                        # その他のコマンドも中断
                                        else:
                                            break

                                if self.debug:
                                    print(f"セリフ: {dialogue_text}, 話者: {dialogue_speaker}, スクロール継続: {scroll_continue}")
                                
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
                                    'scroll_continue': scroll_continue
                                })
                    
                    except Exception as e:
                        if self.debug:
                            print(f"セリフ解析エラー（行 {line_num}）: {e} - {line}")

            except Exception as e:
                    if self.debug:
                        print(f"ダイアログ読み取りエラー")
    
        if not dialogue_data:
            if self.debug:
                print("警告: 対話データが見つかりませんでした。")
            return self.get_default_dialogue()

        # 既存の対話データを従来形式に変換して返す
        formatted_data = []
        for item in dialogue_data:
            if item['type'] == 'dialogue':
                # 従来形式に変換: [背景, キャラクター, 目, 口, 眉, テキスト, BGM, 音量, ループ, 表示名, スクロール継続]
                formatted_data.append([
                    item['background'],
                    item['character'], 
                    item['eye'],
                    item['mouth'],
                    item['brow'],
                    item['text'],
                    item['bgm'],
                    item['bgm_volume'],
                    item['bgm_loop'],
                    item['character'],  # 表示名
                    item['scroll_continue']  # スクロール継続フラグ
                ])
            elif item['type'] == 'bg_show':
                formatted_data.append([
                    item['storage'], "", "", "", "", 
                    f"_BG_SHOW_{item['storage']}_{item['x']}_{item['y']}_{item['zoom']}", 
                    "", 0.5, True, "", False
                ])
            elif item['type'] == 'bg_move':
                formatted_data.append([
                    "", "", "", "", "", 
                    f"_BG_MOVE_{item['left']}_{item['top']}_{item['time']}_{item['zoom']}", 
                    "", 0.5, True, "", False
                ])
            elif item['type'] == 'character':
                formatted_data.append([
                    "", item['name'], item['eye'], item['mouth'], item['brow'],
                    f"_CHARA_NEW_{item['name']}_{item['show_x']}_{item['show_y']}",
                    "", 0.5, True, "", False
                ])
            elif item['type'] == 'move':
                formatted_data.append([
                    "", item['character'], "", "", "",
                    f"_MOVE_{item['left']}_{item['top']}_{item['time']}_{item['zoom']}",
                    "", 0.5, True, "", False
                ])
            elif item['type'] == 'hide':
                formatted_data.append([
                    "", "", "", "", "",
                    f"_CHARA_HIDE_{item['character']}",
                    "", 0.5, True, "", False
                ])

        if self.debug:
            print(f"変換後の対話データ数: {len(formatted_data)}")
            # 最初の数個のデータを出力してデバッグ
            for i, item in enumerate(formatted_data[:5]):
                print(f"データ {i}: {item}")

        return formatted_data