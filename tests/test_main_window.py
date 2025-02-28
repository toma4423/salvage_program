"""
MainWindowクラスのテストモジュール

このモジュールは、GUIウィンドウの機能をテストします。
"""

import pytest
from unittest.mock import MagicMock, patch
import PySimpleGUI as sg
from src.gui.main_window import MainWindow
from src.disk_operations.disk_manager import Disk, FilesystemStatus
from src.file_operations.file_handler import File


@pytest.fixture
def main_window():
    """MainWindowのフィクスチャ"""
    return MainWindow()


@pytest.fixture
def mock_window():
    """モック化されたウィンドウのフィクスチャ"""
    mock = MagicMock()
    mock["-DISK_TREE-"] = MagicMock()
    mock["-FILE_TREE-"] = MagicMock()
    mock["-PROGRESS-"] = MagicMock()
    mock["-STATUS-"] = MagicMock()
    mock["-DISK_STATUS-"] = MagicMock()
    return mock


def test_initialization(main_window):
    """初期化のテスト"""
    assert main_window.window is None
    assert main_window.current_disk is None
    assert main_window.selected_files == []


def test_create_layout(main_window):
    """レイアウト作成のテスト"""
    layout = main_window.create_layout()
    assert isinstance(layout, list)
    assert len(layout) > 0

    # 必要なGUI要素の存在を確認
    elements = []
    for row in layout:
        for element in row:
            if isinstance(element, list):
                elements.extend(element)
            else:
                elements.append(element)

    # 主要なGUI要素のキーを確認
    keys = [
        elem.Key for elem in elements if hasattr(elem, "Key") and elem.Key is not None
    ]
    required_keys = [
        "-DISK_TREE-",
        "-FILE_TREE-",
        "-PROGRESS-",
        "-STATUS-",
        "-DISK_STATUS-",
        "-SELECT-",
        "-SELECT_ALL-",
        "-DESELECT-",
        "-MOUNT-",
        "-UNMOUNT-",
        "-COPY-",
        "-DEST_PATH-",
        "-BROWSE-",
    ]
    for key in required_keys:
        assert key in keys, f"{key}が見つかりません"


def test_create_window(main_window):
    """ウィンドウ作成のテスト"""
    with patch("PySimpleGUI.Window") as mock_window:
        main_window.create_window()
        mock_window.assert_called_once()
        assert main_window.window is not None


def test_update_disk_list(main_window, mock_window):
    """ディスクリスト更新のテスト"""
    main_window.window = mock_window
    test_disks = [
        Disk("/dev/sda1", 1000000000, "ext4", False, "正常"),
        Disk("/dev/sdb1", 2000000000, "ntfs", False, "正常"),
    ]

    main_window.update_disk_list(test_disks)
    mock_window["-DISK_TREE-"].update.assert_called_once()


def test_update_file_tree(main_window, mock_window):
    """ファイルツリー更新のテスト"""
    main_window.window = mock_window
    test_files = [
        File("/test/file1.txt", 1000, None, "正常", False),
        File("/test/file2.txt", 2000, None, "正常", False),
    ]

    main_window.update_file_tree(test_files)
    mock_window["-FILE_TREE-"].update.assert_called_once()


def test_update_progress(main_window, mock_window):
    """進捗更新のテスト"""
    main_window.window = mock_window
    test_value = 50
    test_message = "テスト進捗"

    main_window.update_progress(test_value, test_message)
    mock_window["-PROGRESS-"].update.assert_called_once_with(test_value)
    mock_window["-STATUS-"].update.assert_called_once_with(test_message)


def test_show_error():
    """エラー表示のテスト"""
    window = MainWindow()
    test_message = "テストエラー"

    with patch("PySimpleGUI.popup_error") as mock_popup:
        window.show_error(test_message)
        mock_popup.assert_called_once_with("エラー: " + test_message, title="エラー")


def test_show_help():
    """ヘルプ表示のテスト"""
    window = MainWindow()

    with patch("PySimpleGUI.popup_scrolled") as mock_popup:
        window.show_help()
        mock_popup.assert_called_once()
        assert "ヘルプ" in mock_popup.call_args[1]["title"]


def test_display_disk_status(main_window, mock_window):
    """ディスク状態表示のテスト"""
    main_window.window = mock_window
    test_status = FilesystemStatus(True, "正常に動作しています")

    main_window.display_disk_status(test_status)
    mock_window["-DISK_STATUS-"].update.assert_called_once()


def test_close(main_window, mock_window):
    """ウィンドウ終了のテスト"""
    main_window.window = mock_window
    main_window.close()
    mock_window.close.assert_called_once()


@pytest.mark.parametrize(
    "event,values,expected_files",
    [
        ("-SELECT-", {"-FILE_TREE-": ["file1.txt"]}, ["file1.txt"]),
        (
            "-SELECT_ALL-",
            {"-FILE_TREE-": ["file1.txt", "file2.txt"]},
            ["file1.txt", "file2.txt"],
        ),
        ("-DESELECT-", {"-FILE_TREE-": []}, []),
    ],
)
def test_handle_file_selection(main_window, mock_window, event, values, expected_files):
    """ファイル選択処理のテスト"""
    main_window.window = mock_window
    main_window.handle_file_selection(event, values)
    assert main_window.selected_files == expected_files
