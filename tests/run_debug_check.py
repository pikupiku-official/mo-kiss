import sys
import os
import traceback

sys.path.insert(0, os.path.abspath("."))

out_path = os.path.join(os.path.dirname(__file__), "debug_result.txt")

try:
    log_lines = []
    def log(msg):
        log_lines.append(str(msg))

    import pygame
    pygame.init()
    pygame.mixer.init()

    screen = pygame.Surface((1440, 1080))
    virtual_screen = pygame.Surface((1440, 1080))

    log("=== デバッグテスト開始: E004.ks ===")
    from dialogue.dialogue_subsystem import DialogueSubsystem

    ds = DialogueSubsystem(screen, virtual_screen, "events/E004.ks")

    log("\n--- on_enter() 実行前 ---")
    log(f"現在再生中のBGM: {ds.game_state['bgm_manager'].current_bgm}")

    log("\n--- on_enter() 実行 ---")
    ds.on_enter()

    log(f"on_enter後 再生中BGM: {ds.game_state['bgm_manager'].current_bgm}")
    log(f"mixer get_busy(): {pygame.mixer.music.get_busy()}")

    log("\n--- 手動 advance_dialogue 実行 ---")
    from dialogue.model import advance_dialogue
    advance_dialogue(ds.game_state)
    log(f"advance後 再生中BGM: {ds.game_state['bgm_manager'].current_bgm}")
    log(f"mixer get_busy(): {pygame.mixer.music.get_busy()}")

except Exception as e:
    log(f"エラー発生: {e}")
    log(traceback.format_exc())

finally:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
