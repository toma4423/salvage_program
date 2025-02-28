"""
MainWindowクラスのテストモジュール

このモジュールは、GUIウィンドウの機能をテストします。
一部のテストは特定の環境でのみ実行されます。
"""

import sys
import PySimpleGUI as sg
import pytest
from unittest.mock import MagicMock, patch
from src.gui.main_window import MainWindow
from src.disk_operations.disk_manager import FilesystemStatus
from src.file_operations.file_handler import File


@pytest.mark.linux_only
def test_create_layout():
    """GUIレイアウト作成のテスト（Linux環境専用）"""
    window = MainWindow()
    layout = window.create_layout()

    assert isinstance(layout, list)
    assert len(layout) > 0

    # レイアウト内の要素を確認（再帰的に検索）
    def find_elements(layout_list):
        elements = []
        if not isinstance(layout_list, list):
            return elements

        for row in layout_list:
            if isinstance(row, list):
                elements.extend(find_elements(row))
            elif isinstance(row, sg.Column):
                # Columnの引数を直接取得
                col_args = getattr(row, "Args", [])
                if col_args and isinstance(col_args[0], list):
                    # 最初の引数がレイアウトリスト
                    elements.extend(find_elements(col_args[0]))
                # layout属性も確認
                col_layout = getattr(row, "layout", None)
                if isinstance(col_layout, list):
                    elements.extend(find_elements(col_layout))
            else:
                elements.append(row)
        return elements

    elements = find_elements(layout)
    element_types = {type(elem).__name__ for elem in elements}

    # 必要なGUI要素の存在を確認
    disk_tree = next(
        (elem for elem in elements if getattr(elem, "Key", None) == "-DISK_TREE-"), None
    )
    file_tree = next(
        (elem for elem in elements if getattr(elem, "Key", None) == "-FILE_TREE-"), None
    )
    progress_bar = next(
        (elem for elem in elements if getattr(elem, "Key", None) == "-PROGRESS-"), None
    )

    # 各要素の存在を確認
    assert disk_tree is not None, "ディスクツリーが見つかりません"
    assert file_tree is not None, "ファイルツリーが見つかりません"
    assert progress_bar is not None, "プログレスバーが見つかりません"

    # 要素の型を確認
    assert isinstance(disk_tree, sg.Tree), "ディスクツリーの型が正しくありません"
    assert isinstance(file_tree, sg.Tree), "ファイルツリーの型が正しくありません"
    assert isinstance(
        progress_bar, sg.ProgressBar
    ), "プログレスバーの型が正しくありません"


def test_update_progress():
    """プログレスバー更新のテスト"""
    window = MainWindow()

    # モック化されたウィンドウを作成
    class MockElement:
        def update(self, value=None):
            if isinstance(self, MockProgressBar):
                assert value == 50
            else:
                assert value == "テストメッセージ"

    class MockProgressBar(MockElement):
        pass

    mock_window = {"-PROGRESS-": MockProgressBar(), "-STATUS-": MockElement()}
    window.window = mock_window

    # メソッドを呼び出し
    window.update_progress(50, "テストメッセージ")


def test_show_error():
    """エラーメッセージ表示のテスト"""
    window = MainWindow()
    test_message = "テストエラー"

    # モック化されたsg.popup_errorを作成
    with patch("PySimpleGUI.popup_error") as mock_popup_error:
        window.show_error(test_message)
        mock_popup_error.assert_called_once_with(
            "エラー: " + test_message, title="エラー"
        )


def test_update_file_tree():
    """ファイルツリー更新のテスト"""
    window = MainWindow()
    test_files = [
        File(
            path="/test/file1.txt",
            size=100,
            attributes=None,
            status="正常",
            is_corrupted=False,
        ),
        File(
            path="/test/file2.txt",
            size=200,
            attributes=None,
            status="正常",
            is_corrupted=False,
        ),
    ]

    # モック化されたウィンドウを作成
    class MockTree:
        def update(self, values):
            assert isinstance(values, sg.TreeData)

    mock_window = {"-FILE_TREE-": MockTree()}
    window.window = mock_window

    window.update_file_tree(test_files)


def test_show_help():
    """ヘルプ表示のテスト"""
    window = MainWindow()

    # モック化されたsg.popup_scrolledを作成
    with patch("PySimpleGUI.popup_scrolled") as mock_popup_scrolled:
        window.show_help()
        mock_popup_scrolled.assert_called_once()
        assert "ヘルプ" in mock_popup_scrolled.call_args[1]["title"]


def test_display_disk_status():
    """ディスク状態表示のテスト"""
    window = MainWindow()
    test_status = FilesystemStatus(is_consistent=True, details="正常に動作しています")

    # モック化されたウィンドウを作成
    class MockText:
        def update(self, value):
            assert "正常" in value

    mock_window = {"-DISK_STATUS-": MockText()}
    window.window = mock_window

    window.display_disk_status(test_status)
