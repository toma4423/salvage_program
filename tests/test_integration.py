"""
統合テストモジュール

このモジュールは、複数のコンポーネントが連携する機能をテストします。
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import hashlib
from src.main import Application
from src.disk_operations.disk_manager import Disk, FilesystemStatus
from src.file_operations.file_handler import File
from src.gui.main_window import MainWindow


@pytest.fixture
def app():
    """アプリケーションのフィクスチャ"""
    with patch("src.main.MainWindow"), patch("src.main.DiskManager"), patch(
        "src.main.FileHandler"
    ), patch("src.main.Logger"):
        return Application()


@pytest.fixture
def mock_disk():
    """テスト用のディスクフィクスチャ"""
    return Disk("/dev/sda1", 500 * 1024 * 1024 * 1024, "ext4", False, "PASSED")


@pytest.fixture
def mock_files():
    """テスト用のファイルリストフィクスチャ"""
    return [
        File("/test/file1.txt", 1000, hashlib.md5(b"test1").hexdigest(), "正常", False),
        File("/test/file2.txt", 2000, hashlib.md5(b"test2").hexdigest(), "正常", False),
    ]


@pytest.mark.linux_only
def test_disk_detection_and_mounting(app, mock_disk):
    """ディスク検出とマウントの統合テスト（Linux環境専用）"""
    # ディスク検出のモック設定
    app.disk_manager.detect_disks.return_value = [mock_disk]

    # ディスク検出とGUI更新
    app.detect_and_update_disks()
    app.window.update_disk_list.assert_called_once_with([mock_disk])

    # ディスク選択
    selected_disk = app.handle_disk_selection("/dev/sda1")
    assert selected_disk == mock_disk

    # ディスクマウント
    app.disk_manager.mount_disk.return_value = True
    assert app.mount_disk(selected_disk) is True
    app.logger.log_info.assert_called_with("ディスク /dev/sda1 をマウントしました")


@pytest.mark.linux_only
def test_file_listing_and_copying(app, mock_disk, mock_files, tmp_path):
    """ファイル一覧取得とコピーの統合テスト（Linux環境専用）"""
    # ファイル一覧取得のモック設定
    app.file_handler.list_files.return_value = mock_files

    # ファイル一覧の取得とGUI更新
    app.update_file_list(mock_disk)
    app.window.update_file_tree.assert_called_once_with(mock_files)

    # ファイルコピー
    destination = str(tmp_path / "dest")
    app.file_handler.copy_files.return_value = True
    app.copy_files(mock_files, destination)

    app.window.update_progress.assert_called_with(100, "コピーが完了しました")
    app.logger.log_info.assert_called_with("ファイルのコピーが完了しました")


@pytest.mark.linux_only
def test_disk_health_check(app, mock_disk):
    """ディスク状態チェックの統合テスト（Linux環境専用）"""
    # ディスク状態チェックのモック設定
    mock_status = FilesystemStatus(True, "正常に動作しています")
    app.disk_manager.check_filesystem.return_value = mock_status

    # 状態チェックの実行
    app.check_disk_status(mock_disk)

    app.disk_manager.check_filesystem.assert_called_once_with(mock_disk)
    app.window.display_disk_status.assert_called_once_with(mock_status)
    app.logger.log_info.assert_called_with(
        "ディスク /dev/sda1 の状態チェックが完了しました"
    )


@pytest.mark.linux_only
def test_error_handling(app, mock_disk, mock_files):
    """エラー処理の統合テスト（Linux環境専用）"""
    # マウントエラー
    app.disk_manager.mount_disk.return_value = False
    assert app.mount_disk(mock_disk) is False
    app.logger.log_error.assert_called_with(
        "ディスク /dev/sda1 のマウントに失敗しました"
    )

    # ファイルコピーエラー
    app.file_handler.copy_files.return_value = False
    app.copy_files(mock_files, "/invalid/path")
    app.logger.log_error.assert_called_with("ファイルのコピーに失敗しました")

    # ディスク状態チェックエラー
    mock_status = FilesystemStatus(False, "ファイルシステムにエラーが見つかりました")
    app.disk_manager.check_filesystem.return_value = mock_status
    app.check_disk_status(mock_disk)
    app.window.display_disk_status.assert_called_with(mock_status)


@pytest.mark.linux_only
def test_full_backup_workflow(app, mock_disk, mock_files, tmp_path):
    """完全なバックアップワークフローの統合テスト（Linux環境専用）"""
    # 初期設定
    app.disk_manager.detect_disks.return_value = [mock_disk]
    app.file_handler.list_files.return_value = mock_files
    app.disk_manager.mount_disk.return_value = True
    app.file_handler.copy_files.return_value = True

    # ワークフローの実行
    # 1. ディスク検出
    app.detect_and_update_disks()
    app.window.update_disk_list.assert_called_once_with([mock_disk])

    # 2. ディスク選択とマウント
    selected_disk = app.handle_disk_selection("/dev/sda1")
    assert selected_disk == mock_disk
    assert app.mount_disk(selected_disk) is True

    # 3. ファイル一覧取得
    app.update_file_list(selected_disk)
    app.window.update_file_tree.assert_called_once_with(mock_files)

    # 4. ファイルコピー
    destination = str(tmp_path / "backup")
    app.copy_files(mock_files, destination)
    app.window.update_progress.assert_called_with(100, "コピーが完了しました")

    # 5. ディスクアンマウント
    app.disk_manager.unmount_disk.return_value = True
    assert app.unmount_disk(selected_disk) is True

    # ログの確認
    expected_logs = [
        f"{len([mock_disk])}台のディスクを検出しました",
        "ディスク /dev/sda1 が選択されました",
        "ディスク /dev/sda1 をマウントしました",
        f"{len(mock_files)}個のファイルを検出しました",
        "ファイルのコピーが完了しました",
        "ディスク /dev/sda1 をアンマウントしました",
    ]

    for log in expected_logs:
        app.logger.log_info.assert_any_call(log)
