"""
MainWindowクラスのテストモジュール

このモジュールは、GUIウィンドウの機能をテストします。
"""

import pytest
from unittest.mock import MagicMock, patch, call
import PySimpleGUI as sg
from src.gui.main_window import MainWindow
from src.disk_operations.disk_manager import Disk, FilesystemStatus
from src.file_operations.file_handler import File


@pytest.fixture
def mock_sg():
    """PySimpleGUIのモックフィクスチャ"""
    with patch("src.gui.main_window.sg") as mock_sg:
        # 必要な属性をモックに追加
        mock_sg.Text = MagicMock()
        mock_sg.Tree = MagicMock()
        mock_sg.TreeData = MagicMock()
        mock_sg.Column = MagicMock()
        mock_sg.Button = MagicMock()
        mock_sg.Input = MagicMock()
        mock_sg.FolderBrowse = MagicMock()
        mock_sg.ProgressBar = MagicMock()
        mock_sg.Window = MagicMock()
        mock_sg.popup_error = MagicMock()
        mock_sg.popup_scrolled = MagicMock()
        yield mock_sg


@pytest.fixture
def main_window(mock_sg):
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
    mock["-DISK_LIST-"] = MagicMock()
    return mock


def test_initialization(main_window):
    """初期化のテスト"""
    assert main_window.window is None
    assert main_window.current_disk is None
    assert main_window.selected_files == []


def test_create_layout(main_window, mock_sg):
    """レイアウト作成のテスト"""
    layout = main_window.create_layout()
    assert isinstance(layout, list)
    assert len(layout) > 0


def test_create_window(main_window, mock_sg):
    """ウィンドウ作成のテスト"""
    main_window.create_window()
    mock_sg.Window.assert_called_once()
    assert main_window.window is not None


def test_update_disk_list(main_window, mock_window):
    """ディスクリスト更新のテスト"""
    main_window.window = mock_window
    test_disks = [
        Disk("/dev/sda1", 1000000000, "ext4", False, "正常"),
        Disk("/dev/sdb1", 2000000000, "ntfs", False, "正常"),
    ]

    main_window.update_disk_list(test_disks)
    mock_window["-DISK_LIST-"].update.assert_called_once()


def test_update_file_tree(main_window, mock_window, mock_sg):
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

    # プログレスバーとステータスメッセージの更新を個別にモック化
    progress_mock = MagicMock()
    status_mock = MagicMock()
    mock_window["-PROGRESS-"].update = progress_mock
    mock_window["-STATUS-"].update = status_mock

    main_window.update_progress(test_value, test_message)

    # 個別に更新が呼ばれたことを確認
    progress_mock.assert_called_once_with(current_count=test_value)
    status_mock.assert_called_once_with(value=test_message)


def test_show_error(main_window, mock_sg):
    """エラー表示のテスト"""
    test_message = "テストエラー"
    main_window.show_error(test_message)
    mock_sg.popup_error.assert_called_once_with(
        "エラー: " + test_message, title="エラー"
    )


def test_show_help(main_window, mock_sg):
    """ヘルプ表示のテスト"""
    main_window.show_help()
    mock_sg.popup_scrolled.assert_called_once()
    assert "ヘルプ" in mock_sg.popup_scrolled.call_args[1]["title"]


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
        ("-SELECT_ALL-", {"-FILE_TREE-": []}, ["file1.txt", "file2.txt"]),
        ("-DESELECT-", {"-FILE_TREE-": []}, []),
    ],
)
def test_handle_file_selection(main_window, mock_window, event, values, expected_files):
    """ファイル選択処理のテスト"""
    main_window.window = mock_window
    if event == "-SELECT_ALL-":
        mock_window["-FILE_TREE-"].get_children.return_value = expected_files

    main_window.handle_file_selection(event, values)
    assert main_window.selected_files == expected_files
