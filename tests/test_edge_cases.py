"""
エッジケーステストモジュール

このモジュールは、エッジケースや異常系のテストを行います。
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import hashlib
from src.main import Application
from src.disk_operations.disk_manager import Disk, FilesystemStatus
from src.file_operations.file_handler import File, FileError
from src.gui.main_window import MainWindow


@pytest.fixture
def app():
    """アプリケーションのフィクスチャ"""
    with patch("src.main.MainWindow"), patch("src.main.DiskManager"), patch(
        "src.main.FileHandler"
    ), patch("src.main.Logger"):
        return Application()


@pytest.mark.linux_only
def test_no_disks_detected(app):
    """ディスクが検出されない場合のテスト（Linux環境専用）"""
    app.disk_manager.detect_disks.return_value = []
    app.detect_and_update_disks()
    app.window.update_disk_list.assert_called_once_with([])
    app.logger.log_warning.assert_called_with("ディスクが検出されませんでした")


@pytest.mark.linux_only
def test_disk_suddenly_removed(app):
    """ディスクが突然取り外された場合のテスト（Linux環境専用）"""
    mock_disk = Disk("/dev/sda1", 500 * 1024 * 1024 * 1024, "ext4", False, "PASSED")
    app.disk_manager.detect_disks.return_value = [mock_disk]
    app.detect_and_update_disks()

    # ディスクが取り外された状態をシミュレート
    app.disk_manager.mount_disk.side_effect = OSError("デバイスが見つかりません")
    assert app.mount_disk(mock_disk) is False
    app.logger.log_error.assert_called_with(
        "ディスク /dev/sda1 のマウントに失敗しました"
    )


@pytest.mark.linux_only
def test_disk_full_during_copy(app):
    """コピー中にディスクが一杯になった場合のテスト（Linux環境専用）"""
    mock_files = [
        File("/test/large_file.dat", 1024 * 1024 * 1024, "test_hash", "正常", False)
    ]
    app.file_handler.copy_files.side_effect = OSError(
        "ディスクの空き容量が不足しています"
    )
    app.copy_files(mock_files, "/dest")
    app.logger.log_error.assert_called_with("ファイルのコピーに失敗しました")
    app.window.show_error.assert_called_with("ディスクの空き容量が不足しています")


@pytest.mark.linux_only
def test_corrupted_filesystem(app):
    """ファイルシステムが破損している場合のテスト（Linux環境専用）"""
    mock_disk = Disk("/dev/sda1", 500 * 1024 * 1024 * 1024, "ext4", False, "FAILED")
    mock_status = FilesystemStatus(
        False, "重大なファイルシステムエラーが検出されました"
    )
    app.disk_manager.check_filesystem.return_value = mock_status

    app.check_disk_status(mock_disk)
    app.window.display_disk_status.assert_called_once_with(mock_status)
    app.logger.log_error.assert_called_with(
        "ディスク /dev/sda1 のファイルシステムに問題が見つかりました"
    )


@pytest.mark.linux_only
def test_permission_denied(app):
    """権限エラーのテスト（Linux環境専用）"""
    mock_disk = Disk("/dev/sda1", 500 * 1024 * 1024 * 1024, "ext4", False, "PASSED")
    mock_files = [File("/test/protected.txt", 1000, "test_hash", "正常", False)]

    # マウントポイントへのアクセス権限がない場合
    app.disk_manager.mount_disk.side_effect = PermissionError("権限がありません")
    assert app.mount_disk(mock_disk) is False
    app.logger.log_error.assert_called_with(
        "ディスク /dev/sda1 のマウントに失敗しました"
    )

    # ファイルへのアクセス権限がない場合
    app.file_handler.copy_files.side_effect = PermissionError("権限がありません")
    app.copy_files(mock_files, "/dest")
    app.logger.log_error.assert_called_with("ファイルのコピーに失敗しました")


@pytest.mark.linux_only
def test_invalid_disk_selection(app):
    """無効なディスク選択のテスト（Linux環境専用）"""
    app.disk_manager.detect_disks.return_value = []
    selected_disk = app.handle_disk_selection("/dev/nonexistent")
    assert selected_disk is None
    app.logger.log_warning.assert_called_with(
        "選択されたディスクが見つかりません: /dev/nonexistent"
    )


@pytest.mark.linux_only
def test_duplicate_files(app):
    """重複ファイルのテスト（Linux環境専用）"""
    mock_files = [
        File("/test/file1.txt", 1000, "same_hash", "正常", False),
        File("/test/file2.txt", 1000, "same_hash", "正常", False),
    ]
    app.file_handler.list_files.return_value = mock_files

    # 重複ファイルの検出
    duplicates = [
        f
        for f in mock_files
        if any(f2.hash == f.hash and f2.path != f.path for f2 in mock_files)
    ]
    assert len(duplicates) == 2


@pytest.mark.linux_only
def test_special_characters_in_paths(app):
    """特殊文字を含むパスのテスト（Linux環境専用）"""
    special_paths = [
        "/test/file with spaces.txt",
        "/test/file_with_日本語.txt",
        "/test/file_with_#$%&.txt",
    ]
    mock_files = [
        File(path, 1000, "test_hash", "正常", False) for path in special_paths
    ]

    app.file_handler.copy_files.return_value = True
    app.copy_files(mock_files, "/dest/path with spaces")
    app.logger.log_info.assert_called_with("ファイルのコピーが完了しました")


@pytest.mark.linux_only
def test_very_large_file_list(app):
    """非常に多数のファイルのテスト（Linux環境専用）"""
    # 10000個のファイルを生成
    mock_files = [
        File(f"/test/file{i}.txt", 1000, f"hash{i}", "正常", False)
        for i in range(10000)
    ]
    app.file_handler.list_files.return_value = mock_files

    app.update_file_list(MagicMock())
    app.window.update_file_tree.assert_called_once_with(mock_files)
    app.logger.log_info.assert_called_with("10000個のファイルを検出しました")


@pytest.mark.linux_only
def test_zero_byte_files(app):
    """サイズが0のファイルのテスト（Linux環境専用）"""
    mock_files = [
        File("/test/empty1.txt", 0, hashlib.md5(b"").hexdigest(), "正常", False),
        File("/test/empty2.txt", 0, hashlib.md5(b"").hexdigest(), "正常", False),
    ]

    app.file_handler.copy_files.return_value = True
    app.copy_files(mock_files, "/dest")
    app.logger.log_info.assert_called_with("ファイルのコピーが完了しました")
