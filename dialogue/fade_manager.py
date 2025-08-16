import pygame
from config import *

def parse_color(color_str):
    """色文字列をRGB値に変換"""
    if color_str.lower() == "black":
        return (0, 0, 0)
    elif color_str.lower() == "white":
        return (255, 255, 255)
    elif color_str.lower() == "red":
        return (255, 0, 0)
    elif color_str.lower() == "green":
        return (0, 255, 0)
    elif color_str.lower() == "blue":
        return (0, 0, 255)
    elif color_str.startswith("#") and len(color_str) == 7:
        # #RRGGBB形式
        try:
            r = int(color_str[1:3], 16)
            g = int(color_str[3:5], 16)
            b = int(color_str[5:7], 16)
            return (r, g, b)
        except ValueError:
            return (0, 0, 0)
    else:
        return (0, 0, 0)  # デフォルトは黒

def start_fadeout(game_state, color="black", duration=1.0):
    """フェードアウトを開始"""
    current_time = pygame.time.get_ticks()
    fade_color = parse_color(color)
    duration_ms = int(duration * 1000)
    
    # 既存のフェードをキャンセル
    if game_state.get('fade_state', {}).get('active'):
        print(f"[FADE] 既存のフェードをキャンセルしてフェードアウト開始")
    
    game_state['fade_state'] = {
        'type': 'fadeout',
        'start_time': current_time,
        'duration': duration_ms,
        'color': fade_color,
        'alpha': 0,
        'active': True
    }
    
    print(f"[FADE] フェードアウト開始: color={color}({fade_color}), duration={duration}s, duration_ms={duration_ms}")

def start_fadein(game_state, duration=1.0):
    """フェードインを開始"""
    current_time = pygame.time.get_ticks()
    duration_ms = int(duration * 1000)
    
    # 現在のフェード色を取得（フェードアウトしていない場合は黒）
    current_color = game_state.get('fade_state', {}).get('color', (0, 0, 0))
    
    # フェードアウトが完了していない場合は警告
    if game_state.get('fade_state', {}).get('active') and game_state['fade_state']['type'] == 'fadeout':
        elapsed = current_time - game_state['fade_state']['start_time']
        if elapsed < game_state['fade_state']['duration']:
            print(f"[FADE] 警告: フェードアウト未完了でフェードイン開始 (elapsed={elapsed}ms, duration={game_state['fade_state']['duration']}ms)")
    
    game_state['fade_state'] = {
        'type': 'fadein',
        'start_time': current_time,
        'duration': duration_ms,
        'color': current_color,
        'alpha': 255,
        'active': True
    }
    
    print(f"[FADE] フェードイン開始: color={current_color}, duration={duration}s, duration_ms={duration_ms}")

def update_fade_animation(game_state):
    """フェードアニメーションを更新"""
    if not game_state.get('fade_state', {}).get('active'):
        return
    
    fade_state = game_state['fade_state']
    current_time = pygame.time.get_ticks()
    elapsed = current_time - fade_state['start_time']
    
    # デバッグ出力（開始から1秒間は頻繁に、その後は1秒おき）
    if not hasattr(game_state, 'last_fade_debug_time'):
        game_state['last_fade_debug_time'] = 0
    
    debug_interval = 100 if elapsed < 1000 else 1000  # 最初は100ms、その後は1秒おき
    if current_time - game_state['last_fade_debug_time'] > debug_interval:
        progress_pct = (elapsed / fade_state['duration']) * 100 if fade_state['duration'] > 0 else 100
        print(f"[FADE] 更新: type={fade_state['type']}, elapsed={elapsed}ms, duration={fade_state['duration']}ms, progress={progress_pct:.1f}%, alpha={fade_state['alpha']}")
        game_state['last_fade_debug_time'] = current_time
    
    if elapsed >= fade_state['duration']:
        # アニメーション完了
        if fade_state['type'] == 'fadeout':
            fade_state['alpha'] = 255  # 完全に不透明
            print(f"[FADE] フェードアウト完了: alpha=255")
        else:  # fadein
            fade_state['alpha'] = 0    # 完全に透明
            fade_state['active'] = False  # フェードイン完了で無効化
            print(f"[FADE] フェードイン完了: alpha=0, 無効化")
        return
    
    # アルファ値を計算
    if fade_state['duration'] <= 0:
        print(f"[FADE] エラー: duration が0以下です: {fade_state['duration']}")
        fade_state['active'] = False
        return
    
    progress = elapsed / fade_state['duration']
    
    if fade_state['type'] == 'fadeout':
        # 0（透明）から255（不透明）へ
        fade_state['alpha'] = int(255 * progress)
    else:  # fadein
        # 255（不透明）から0（透明）へ
        fade_state['alpha'] = int(255 * (1.0 - progress))

def draw_fade_overlay(game_state):
    """フェードオーバーレイを描画"""
    if not game_state.get('fade_state', {}).get('active'):
        return
    
    fade_state = game_state['fade_state']
    
    # デバッグ出力（描画時の状態を確認）
    if not hasattr(game_state, 'last_draw_debug_time'):
        game_state['last_draw_debug_time'] = 0
    
    current_time = pygame.time.get_ticks()
    if current_time - game_state['last_draw_debug_time'] > 200:  # 200msおき
        print(f"[FADE] 描画: alpha={fade_state['alpha']}, color={fade_state['color']}, active={fade_state['active']}")
        game_state['last_draw_debug_time'] = current_time
    
    if fade_state['alpha'] <= 0:
        return
    
    screen = game_state['screen']
    overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay_surface.set_alpha(fade_state['alpha'])
    overlay_surface.fill(fade_state['color'])
    
    screen.blit(overlay_surface, (0, 0))

def is_fade_active(game_state):
    """フェードが実行中かどうかを判定"""
    return game_state.get('fade_state', {}).get('active', False)

def is_fadeout_complete(game_state):
    """フェードアウトが完了しているかどうかを判定"""
    fade_state = game_state.get('fade_state', {})
    return (fade_state.get('type') == 'fadeout' and 
            fade_state.get('alpha', 0) >= 255)