import unittest
import sys
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath("."))

from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from core.bgm_manager import BGMManager

class TestBgmSe(unittest.TestCase):
    def _loader(self):
        loader = DialogueLoader.__new__(DialogueLoader)
        loader.debug = False
        loader.disable_scroll_continue = False
        loader.max_chars_per_line = 26
        return loader

    def test_bgm_unspecified_defaults_to_none(self):
        raw = self._loader()._parse_ks_content(
            "//桃子//\n"
            "「こんにちは」\n"
        )
        normalized = normalize_dialogue_data(raw)
        dialogue = next(entry for entry in normalized if isinstance(entry, list))
        self.assertIsNone(dialogue[7])
        
        ir = build_ir_from_normalized(normalized)
        actions = [a for step in ir["steps"] if "actions" in step and step["actions"] for a in step["actions"]]
        bgm_actions = [a for a in actions if a.get("action") == "bgm_play"]
        self.assertEqual(len(bgm_actions), 0)

    def test_bgm_specified_creates_action(self):
        raw = self._loader()._parse_ks_content(
            "[BGM bgm=\"MmkBgm1\" volume=\"0.5\" loop=\"true\"]\n"
            "//桃子//\n"
            "「こんにちは」\n"
        )
        normalized = normalize_dialogue_data(raw)
        bgm_cmd = next(entry for entry in normalized if isinstance(entry, list) and len(entry) > 6 and str(entry[6]).startswith("_BGM_PLAY_"))
        self.assertIn("_BGM_PLAY_MmkBgm1_0.5_True", bgm_cmd[6])
        
        ir = build_ir_from_normalized(normalized)
        actions = [a for step in ir["steps"] if "actions" in step and step["actions"] for a in step["actions"]]
        bgm_actions = [a for a in actions if a.get("action") == "bgm_play"]
        self.assertEqual(len(bgm_actions), 1)
        self.assertEqual(bgm_actions[0]["params"]["file"], "MmkBgm1")

    def test_se_specified_creates_action(self):
        raw = self._loader()._parse_ks_content(
            "[SE se=\"click.wav\" volume=\"0.8\"]\n"
            "//桃子//\n"
            "「こんにちは」\n"
        )
        normalized = normalize_dialogue_data(raw)
        se_cmd = next(entry for entry in normalized if isinstance(entry, list) and len(entry) > 6 and str(entry[6]).startswith("_SE_PLAY_"))
        self.assertIn("_SE_PLAY_click.wav_0.8_1_false", se_cmd[6])

        ir = build_ir_from_normalized(normalized)
        actions = [a for step in ir["steps"] if "actions" in step and step["actions"] for a in step["actions"]]
        se_actions = [a for a in actions if a.get("action") == "se_play"]
        self.assertEqual(len(se_actions), 1)
        self.assertEqual(se_actions[0]["params"]["file"], "click.wav")

    def test_bgmstop_parsing_and_normalization(self):
        # 小文字、大文字、数値指定を含むbgmstopタグの動作テスト
        raw = self._loader()._parse_ks_content(
            "[BGM bgm=\"MmkBgm1\" volume=\"0.5\" loop=\"true\"]\n"
            "//桃子//\n"
            "「BGM再生中」\n"
            "[bgmstop time=\"2.5\"]\n"
            "//桃子//\n"
            "「BGM停止後」\n"
        )
        self.assertTrue(any(e.get('type') == 'bgm_pause' and e.get('fade_time') == 2.5 for e in raw))
        
        normalized = normalize_dialogue_data(raw)
        bgm_pause_cmd = next(entry for entry in normalized if isinstance(entry, list) and len(entry) > 6 and str(entry[6]).startswith("_BGM_PAUSE"))
        self.assertIsNotNone(bgm_pause_cmd)
        self.assertEqual(bgm_pause_cmd[12].get('fade_time'), 2.5)

        # bgmstop後は後続行のcurrent_bgmがNoneになることを確認
        last_dialogue = normalized[-1]
        self.assertIsNone(last_dialogue[7])

        ir = build_ir_from_normalized(normalized)
        actions = [a for step in ir["steps"] if "actions" in step and step["actions"] for a in step["actions"]]
        pause_actions = [a for a in actions if a.get("action") == "bgm_pause"]
        self.assertEqual(len(pause_actions), 1)
        self.assertEqual(pause_actions[0]["params"]["fade_time"], 2.5)

    def test_bgm_manager_file_search_and_volume_normalization(self):
        manager = BGMManager(debug=False)
        # Test file extension matching for real files like '02_学校生活'
        actual = manager.get_bgm_for_scene("02_学校生活")
        self.assertEqual(actual, "02_学校生活.ogg")
        
        # Test case-insensitive or partial fallback
        actual2 = manager.get_bgm_for_scene("Mok1_Lap1")
        self.assertEqual(actual2, "Mok1_Lap2.mp3") if actual2 == "Mok1_Lap2.mp3" else self.assertEqual(actual2, "Mok1_Lap1.mp3")

    def test_no_bgm_at_start_if_unspecified(self):
        from dialogue.game_manager import _initialize_bgm
        raw = self._loader()._parse_ks_content(
            "//桃子//\n"
            "「BGMなしの冒頭」\n"
            "[BGM bgm=\"MmkBgm1\" volume=\"0.5\" loop=\"true\"]\n"
            "「BGM追加」\n"
        )
        normalized = normalize_dialogue_data(raw)
        game_state = {
            'bgm_manager': BGMManager(debug=False),
            'dialogue_data': normalized
        }
        # 1行目がBGM未指定のため、_initialize_bgmがFalseを返しBGM再生を始めないことを確認
        res = _initialize_bgm(game_state)
        self.assertFalse(res)

if __name__ == "__main__":
    unittest.main()
