"""
event_editor_mac.pyのテストケース

主な問題点:
1. start_preview()は別プロセスでpreview_dialogue.pyを起動するが、プロセス管理していない
2. stop_preview()はpreview_runningフラグとcommand_queueを使っているが、別プロセスには届かない
3. reload_preview()も同様にcommand_queueを使うが、別プロセスには届かない
4. preview_threadとPreviewWindowクラスは定義されているが、start_preview()では使われていない
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

class TestEventEditorMac:
    """event_editor_mac.pyのテストクラス"""

    def setup_method(self):
        """各テストの前処理"""
        self.events_dir = os.path.join(project_root, "events")
        self.test_file = os.path.join(self.events_dir, "E001.ks")
        self.preview_processes = []

    def teardown_method(self):
        """各テストの後処理 - 起動したプロセスをクリーンアップ"""
        print(f"\n[TEARDOWN] {len(self.preview_processes)}個のプロセスをクリーンアップ")
        for proc in self.preview_processes:
            if proc.poll() is None:  # まだ実行中
                print(f"[TEARDOWN] プロセス {proc.pid} を終了")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print(f"[TEARDOWN] プロセス {proc.pid} を強制終了")
                    proc.kill()
                    proc.wait()

    def test_preview_process_launch(self):
        """
        テスト1: プレビュープロセスの起動確認

        期待される動作:
        - preview_dialogue.pyが別プロセスとして起動される
        - プロセスが実行され続ける
        """
        print("\n=== テスト1: プレビュープロセスの起動 ===")

        # プレビュープロセスを起動（event_editor_mac.pyのstart_preview()と同じ方法）
        preview_script = os.path.join(project_root, "preview_dialogue.py")
        proc = subprocess.Popen(
            ['python3', preview_script, self.test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.preview_processes.append(proc)

        print(f"[TEST] プレビュープロセス起動: PID={proc.pid}")

        # 少し待ってプロセスが実行中か確認
        time.sleep(2)

        # プロセスが実行中であることを確認
        assert proc.poll() is None, "プレビュープロセスが予期せず終了しました"
        print(f"[TEST] ✅ プレビュープロセスは実行中 (PID={proc.pid})")

        # 出力を少し読む
        time.sleep(1)

    def test_preview_process_cannot_be_controlled_via_queue(self):
        """
        テスト2: 別プロセスはqueueで制御できない

        問題点:
        - event_editor_mac.pyのstop_preview()とreload_preview()は
          command_queueにコマンドをputしているが、別プロセスには届かない
        - queue.Queueはスレッド間通信用で、プロセス間通信には使えない

        期待される結果:
        - command_queueにputしても別プロセスには届かない
        - プロセスは実行され続ける
        """
        print("\n=== テスト2: queueで別プロセスを制御できない ===")

        import queue
        command_queue = queue.Queue()

        # プレビュープロセスを起動
        preview_script = os.path.join(project_root, "preview_dialogue.py")
        proc = subprocess.Popen(
            ['python3', preview_script, self.test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.preview_processes.append(proc)

        print(f"[TEST] プレビュープロセス起動: PID={proc.pid}")
        time.sleep(2)

        # stop_preview()と同じようにstopコマンドをqueueにput
        print("[TEST] command_queueに'stop'コマンドをput")
        command_queue.put({'type': 'stop'})

        # 少し待つ
        time.sleep(2)

        # プロセスは実行され続けている（queueは届いていない）
        assert proc.poll() is None, "プロセスが予期せず終了しました"
        print(f"[TEST] ✅ プロセスは実行中（queueコマンドは届いていない）")

    def test_multiple_preview_processes_accumulate(self):
        """
        テスト3: プレビューを複数回起動するとプロセスが蓄積する

        問題点:
        - start_preview()を複数回呼ぶと、古いプロセスが終了せずに残る
        - プロセスIDを保存していないため、古いプロセスを停止できない

        期待される結果:
        - 複数のプレビュープロセスが同時実行される
        """
        print("\n=== テスト3: 複数プレビュープロセスの蓄積 ===")

        preview_script = os.path.join(project_root, "preview_dialogue.py")

        # 1回目の起動
        proc1 = subprocess.Popen(
            ['python3', preview_script, self.test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.preview_processes.append(proc1)
        print(f"[TEST] 1回目のプレビュー起動: PID={proc1.pid}")
        time.sleep(1)

        # 2回目の起動（古いプロセスを停止せずに）
        proc2 = subprocess.Popen(
            ['python3', preview_script, self.test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.preview_processes.append(proc2)
        print(f"[TEST] 2回目のプレビュー起動: PID={proc2.pid}")
        time.sleep(1)

        # 両方のプロセスが実行中
        assert proc1.poll() is None, "1回目のプロセスが終了しました"
        assert proc2.poll() is None, "2回目のプロセスが終了しました"
        print(f"[TEST] ✅ 両方のプロセスが実行中（プロセスが蓄積している）")
        print(f"[TEST] プロセス1: PID={proc1.pid}, プロセス2: PID={proc2.pid}")

    def test_preview_process_termination(self):
        """
        テスト4: プロセスの正しい終了方法

        正しい方法:
        - subprocess.Popenで起動したプロセスはterminate()またはkill()で終了
        - プロセスIDを保存しておく必要がある

        期待される結果:
        - terminate()でプロセスが終了する
        """
        print("\n=== テスト4: プロセスの正しい終了方法 ===")

        preview_script = os.path.join(project_root, "preview_dialogue.py")
        proc = subprocess.Popen(
            ['python3', preview_script, self.test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.preview_processes.append(proc)

        print(f"[TEST] プレビュープロセス起動: PID={proc.pid}")
        time.sleep(2)

        # プロセスが実行中であることを確認
        assert proc.poll() is None, "プロセスが予期せず終了しました"
        print(f"[TEST] プロセスは実行中")

        # terminate()でプロセスを終了
        print(f"[TEST] プロセス {proc.pid} をterminateで終了")
        proc.terminate()
        proc.wait(timeout=3)

        # プロセスが終了したことを確認
        assert proc.poll() is not None, "プロセスが終了していません"
        print(f"[TEST] ✅ プロセスが正常に終了しました（戻り値={proc.poll()}）")

    def test_reload_requires_ipc(self):
        """
        テスト5: リロード機能にはプロセス間通信が必要

        問題点:
        - reload_preview()はcommand_queueにreloadコマンドをputするが届かない
        - プロセス間通信（IPC）の仕組みが必要

        解決策の例:
        - multiprocessing.Queueを使う
        - シグナル（SIGUSR1など）を使う
        - ファイルベースの通信を使う
        - ソケット通信を使う

        期待される結果:
        - 現在の実装ではリロードコマンドが届かない
        """
        print("\n=== テスト5: リロードにはIPCが必要 ===")

        import queue
        command_queue = queue.Queue()

        preview_script = os.path.join(project_root, "preview_dialogue.py")
        proc = subprocess.Popen(
            ['python3', preview_script, self.test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.preview_processes.append(proc)

        print(f"[TEST] プレビュープロセス起動: PID={proc.pid}")
        time.sleep(2)

        # reload_preview()と同じようにreloadコマンドをqueueにput
        print("[TEST] command_queueに'reload'コマンドをput")
        command_queue.put({'type': 'reload', 'keep_position': True})

        time.sleep(2)

        # プロセスは実行され続けている（reloadコマンドは届いていない）
        assert proc.poll() is None, "プロセスが予期せず終了しました"
        print(f"[TEST] ✅ プロセスは実行中（reloadコマンドは届いていない）")
        print(f"[TEST] ⚠️ プロセス間通信の仕組みが必要です")


def run_tests():
    """テストを実行して結果を表示"""
    print("=" * 60)
    print("event_editor_mac.py テスト実行")
    print("=" * 60)

    test_instance = TestEventEditorMac()

    # 各テストを実行
    tests = [
        ("プレビュープロセスの起動", test_instance.test_preview_process_launch),
        ("queueで別プロセスを制御できない", test_instance.test_preview_process_cannot_be_controlled_via_queue),
        ("複数プレビュープロセスの蓄積", test_instance.test_multiple_preview_processes_accumulate),
        ("プロセスの正しい終了方法", test_instance.test_preview_process_termination),
        ("リロードにはIPCが必要", test_instance.test_reload_requires_ipc),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"テスト: {test_name}")
        print(f"{'=' * 60}")

        test_instance.setup_method()

        try:
            test_func()
            results.append((test_name, "✅ PASS", None))
        except AssertionError as e:
            results.append((test_name, "❌ FAIL", str(e)))
            print(f"\n[ERROR] {e}")
        except Exception as e:
            results.append((test_name, "⚠️ ERROR", str(e)))
            print(f"\n[EXCEPTION] {e}")
        finally:
            test_instance.teardown_method()

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    for test_name, status, error in results:
        print(f"{status} {test_name}")
        if error:
            print(f"   エラー: {error}")

    # 問題点の評価
    print("\n" + "=" * 60)
    print("評価: event_editor_mac.pyの問題点")
    print("=" * 60)

    print("""
【問題1】プロセス管理の欠如
- start_preview()で起動したプロセスを保存していない
- 複数回起動すると古いプロセスが残り続ける
- プロセスを停止する手段がない

【問題2】stop_preview()が機能しない
- command_queue.put({'type': 'stop'})としているが、
  別プロセスには届かない
- queue.Queueはスレッド間通信用で、プロセス間通信には使えない
- preview_runningフラグも同様に別プロセスからは見えない

【問題3】reload_preview()が機能しない
- command_queue.put({'type': 'reload'})としているが、
  別プロセスには届かない
- リロード機能を実現するにはプロセス間通信（IPC）が必要

【問題4】PreviewWindowクラスが未使用
- PreviewWindowクラスとpreview_threadが定義されているが、
  start_preview()では別プロセスとして起動している
- スレッド版とプロセス版の実装が混在している

【推奨される解決策】
1. subprocess.Popenで起動したプロセスのPIDを保存
2. stop_preview()でproc.terminate()を使ってプロセスを終了
3. リロード機能は以下のいずれかで実装:
   a) プロセスを一度終了して再起動（シンプル）
   b) multiprocessing.Queueでプロセス間通信
   c) シグナル（SIGUSR1など）でリロードを指示
   d) ファイルベースの通信（監視ファイルを使う）
4. 複数起動を防ぐため、既存プロセスがあれば先に終了
    """)


if __name__ == "__main__":
    run_tests()
