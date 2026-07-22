import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath("."))

log_path = os.path.abspath("tests/debug_result.txt")
with open(log_path, "w", encoding="utf-8") as f:
    f.write("=== LOG START ===\n")

def write_log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

try:
    write_log("1. Importing core modules")
    import core.config
    write_log("core.config OK")
    import core.bgm_manager
    write_log("core.bgm_manager OK")

    write_log("2. Importing dialogue modules step by step")
    import dialogue.ir_model
    write_log("dialogue.ir_model OK")

    import dialogue.dialogue_loader
    write_log("dialogue.dialogue_loader OK")

    import dialogue.data_normalizer
    write_log("dialogue.data_normalizer OK")

    import dialogue.ir_builder
    write_log("dialogue.ir_builder OK")

    write_log("3. Testing DialogueLoader")
    loader = dialogue.dialogue_loader.DialogueLoader()
    raw = loader.load_dialogue_from_ks("events/E004.ks")
    write_log(f"Raw loaded: {len(raw) if raw else 0} items")

    data = dialogue.data_normalizer.normalize_dialogue_data(raw)
    write_log(f"Normalized: {len(data) if data else 0} items")

    ir_data = dialogue.ir_builder.build_ir_from_normalized(data)
    write_log(f"IR steps: {len(ir_data.get('steps', []))} steps")

    write_log("4. Testing BGMManager play_bgm directly")
    bgm_mgr = core.bgm_manager.BGMManager(debug=True)
    res = bgm_mgr.play_bgm("school_daily", 0.5, True)
    write_log(f"Play bgm result: {res}, current_bgm: {bgm_mgr.current_bgm}")

except Exception as e:
    import traceback
    write_log(f"ERROR: {e}")
    write_log(traceback.format_exc())

write_log("=== LOG END ===")
