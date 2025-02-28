import pytest
import PySimpleGUI as sg
from src.gui.main_window import MainWindow


def test_create_layout():
    """GUIレイアウト作成のテスト"""
    window = MainWindow()
    layout = window.create_layout()

    assert isinstance(layout, list)
    assert len(layout) > 0

    # レイアウト内の要素を確認
    elements = [elem for row in layout for elem in row]

    # テキスト、プログレスバー、ボタンの存在を確認
    assert any(
        isinstance(elem, sg.Text) and "データサルベージプログラム" in elem.DisplayText
        for elem in elements
    )
    assert any(isinstance(elem, sg.ProgressBar) for elem in elements)
    assert any(
        isinstance(elem, sg.Button) and elem.ButtonText in ["開始", "終了"]
        for elem in elements
    )


def test_update_progress(monkeypatch):
    """プログレスバー更新のテスト"""
    window = MainWindow()

    # モック化されたウィンドウを作成
    mock_window = {
        "-PROGRESS-": type("MockProgressBar", (), {"update_bar": lambda x: None})
    }
    window.window = mock_window

    # モック化されたsg.popupをパッチ
    def mock_popup(message):
        assert message is not None

    monkeypatch.setattr(sg, "popup", mock_popup)

    # メソッドを呼び出し
    window.update_progress(50, "テストメッセージ")


def test_show_error(monkeypatch):
    """エラーメッセージ表示のテスト"""

    # モック化されたsg.popup_errorをパッチ
    def mock_popup_error(message):
        assert "エラー: " in message

    monkeypatch.setattr(sg, "popup_error", mock_popup_error)

    window = MainWindow()
    window.show_error("テストエラー")


def test_update_file_list(capsys):
    """ファイル一覧更新のテスト"""
    window = MainWindow()
    test_files = [
        {"name": "file1.txt", "size": 100},
        {"name": "file2.txt", "size": 200},
    ]

    window.update_file_list(test_files)
    captured = capsys.readouterr().out

    assert "ファイル一覧を更新中..." in captured


def test_show_help(monkeypatch):
    """ヘルプ表示のテスト"""

    # モック化されたsg.popupをパッチ
    def mock_popup(message):
        assert "ヘルプ情報" in message

    monkeypatch.setattr(sg, "popup", mock_popup)

    window = MainWindow()
    window.show_help()


def test_display_disk_status(capsys):
    """ディスク状態表示のテスト"""
    window = MainWindow()
    test_status = {"status": "正常", "free_space": "100GB"}

    window.display_disk_status(test_status)
    captured = capsys.readouterr().out

    assert "ディスク状態:" in captured
