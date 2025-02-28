"""
メインプログラムのテストモジュール

このモジュールは、アプリケーションの初期化と実行をテストします。
"""

import pytest
from unittest.mock import patch, MagicMock, call
from src.main import Application, main
from src.disk_operations.disk_manager import Disk, FilesystemStatus
from src.file_operations.file_handler import File


@pytest.fixture
def app():
    """アプリケーションのフィクスチャ"""
    with patch("src.main.MainWindow"), patch("src.main.DiskManager"), patch(
        "src.main.FileHandler"
    ), patch("src.main.Logger"):
        return Application()


def test_main_initialization():
    """メイン関数の初期化テスト"""
    with patch("src.main.Application") as mock_app:
        mock_app.return_value.check_sudo_privileges.return_value = True
        main()
        mock_app.assert_called_once()
        mock_app.return_value.run.assert_called_once()


def test_application_initialization():
    """アプリケーション初期化のテスト"""
    with patch("src.main.MainWindow") as mock_window, patch(
        "src.main.DiskManager"
    ) as mock_disk_manager, patch("src.main.FileHandler") as mock_file_handler, patch(
        "src.main.Logger"
    ) as mock_logger:
        app = Application()
        assert mock_window.called
        assert mock_disk_manager.called
        assert mock_file_handler.called
        assert mock_logger.called


@pytest.mark.linux_only
def test_check_sudo_privileges(app):
    """sudo権限チェックのテスト（Linux環境専用）"""
    with patch("subprocess.run") as mock_run:
        # sudo権限がある場合
        mock_run.return_value = MagicMock(returncode=0)
        assert app.check_sudo_privileges() is True
        app.logger.log_info.assert_called_with("sudo権限の確認に成功しました")

        # sudo権限がない場合
        mock_run.side_effect = Exception("Permission denied")
        assert app.check_sudo_privileges() is False
        app.logger.log_error.assert_called_with(
            "sudo権限の確認に失敗しました: Permission denied"
        )


@pytest.mark.linux_only
def test_detect_and_update_disks(app):
    """ディスク検出と更新のテスト（Linux環境専用）"""
    mock_disks = [
        Disk("/dev/sda1", 1000000000, "ext4", False, "正常"),
        Disk("/dev/sdb1", 2000000000, "ntfs", False, "正常"),
    ]
    app.disk_manager.detect_disks.return_value = mock_disks

    app.detect_and_update_disks()

    app.disk_manager.detect_disks.assert_called_once()
    app.window.update_disk_list.assert_called_once_with(mock_disks)
    app.logger.log_info.assert_called_with(
        f"{len(mock_disks)}台のディスクを検出しました"
    )


@pytest.mark.linux_only
def test_handle_disk_selection(app):
    """ディスク選択処理のテスト（Linux環境専用）"""
    mock_disk = Disk("/dev/sda1", 1000000000, "ext4", False, "正常")
    app.disk_manager.detect_disks.return_value = [mock_disk]

    # 正常なディスク選択
    selected_disk = app.handle_disk_selection("/dev/sda1")
    assert selected_disk == mock_disk
    app.logger.log_info.assert_called_with("ディスク /dev/sda1 が選択されました")

    # 無効なディスク選択
    selected_disk = app.handle_disk_selection("/dev/sdb1")
    assert selected_disk is None
    app.logger.log_warning.assert_called_with(
        "選択されたディスクが見つかりません: /dev/sdb1"
    )


@pytest.mark.linux_only
def test_mount_disk(app):
    """ディスクマウントのテスト（Linux環境専用）"""
    mock_disk = Disk("/dev/sda1", 1000000000, "ext4", False, "正常")

    # マウント成功
    app.disk_manager.mount_disk.return_value = True
    assert app.mount_disk(mock_disk) is True
    app.logger.log_info.assert_called_with("ディスク /dev/sda1 をマウントしました")

    # マウント失敗
    app.disk_manager.mount_disk.return_value = False
    assert app.mount_disk(mock_disk) is False
    app.logger.log_error.assert_called_with(
        "ディスク /dev/sda1 のマウントに失敗しました"
    )


@pytest.mark.linux_only
def test_unmount_disk(app):
    """ディスクアンマウントのテスト（Linux環境専用）"""
    mock_disk = Disk("/dev/sda1", 1000000000, "ext4", True, "正常")

    # アンマウント成功
    app.disk_manager.unmount_disk.return_value = True
    assert app.unmount_disk(mock_disk) is True
    app.logger.log_info.assert_called_with("ディスク /dev/sda1 をアンマウントしました")

    # アンマウント失敗
    app.disk_manager.unmount_disk.return_value = False
    assert app.unmount_disk(mock_disk) is False
    app.logger.log_error.assert_called_with(
        "ディスク /dev/sda1 のアンマウントに失敗しました"
    )


@pytest.mark.linux_only
def test_check_disk_status(app):
    """ディスク状態チェックのテスト（Linux環境専用）"""
    mock_disk = Disk("/dev/sda1", 1000000000, "ext4", True, "正常")
    mock_status = FilesystemStatus(True, "正常に動作しています")
    app.disk_manager.check_filesystem.return_value = mock_status

    app.check_disk_status(mock_disk)

    app.disk_manager.check_filesystem.assert_called_once_with(mock_disk)
    app.window.display_disk_status.assert_called_once_with(mock_status)
    app.logger.log_info.assert_called_with(
        "ディスク /dev/sda1 の状態チェックが完了しました"
    )


def test_update_file_list(app):
    """ファイル一覧更新のテスト"""
    mock_disk = Disk("/dev/sda1", 1000000000, "ext4", True, "正常")
    mock_files = [
        File("/test/file1.txt", 1000, None, "正常", False),
        File("/test/file2.txt", 2000, None, "正常", False),
    ]
    app.file_handler.list_files.return_value = mock_files

    app.update_file_list(mock_disk)

    app.file_handler.list_files.assert_called_once()
    app.window.update_file_tree.assert_called_once_with(mock_files)
    app.logger.log_info.assert_called_with(
        f"{len(mock_files)}個のファイルを検出しました"
    )


def test_copy_files(app):
    """ファイルコピーのテスト"""
    mock_files = [
        File("/test/file1.txt", 1000, None, "正常", False),
        File("/test/file2.txt", 2000, None, "正常", False),
    ]
    destination = "/path/to/destination"

    # コピー成功
    app.file_handler.copy_files.return_value = True
    app.copy_files(mock_files, destination)

    app.window.update_progress.assert_has_calls(
        [call(0, "コピーを開始します..."), call(100, "コピーが完了しました")]
    )
    app.file_handler.copy_files.assert_called_once_with(mock_files, destination)
    app.logger.log_info.assert_called_with("ファイルのコピーが完了しました")

    # コピー失敗
    app.file_handler.copy_files.return_value = False
    app.copy_files(mock_files, destination)
    app.logger.log_error.assert_called_with("ファイルのコピーに失敗しました")


@pytest.mark.linux_only
def test_run(app):
    """アプリケーション実行のテスト（Linux環境専用）"""
    # イベントループのシミュレーション
    app.window.window.read.side_effect = [
        ("-MOUNT-", {"device": "/dev/sda1"}),  # マウントボタンクリック
        ("-COPY-", {"destination": "/path/to/dest"}),  # コピーボタンクリック
        ("-EXIT-", None),  # 終了ボタンクリック
    ]

    # テスト用のモックオブジェクト
    mock_disk = Disk("/dev/sda1", 1000000000, "ext4", False, "正常")
    app.handle_disk_selection.return_value = mock_disk
    app.mount_disk.return_value = True
    app.file_handler.copy_files.return_value = True

    # アプリケーションを実行
    app.run()

    # 期待される呼び出しを確認
    assert app.window.create_window.called
    assert app.window.window.read.call_count == 3
    assert app.window.close.called
    app.logger.log_info.assert_called_with("アプリケーションを終了します")
