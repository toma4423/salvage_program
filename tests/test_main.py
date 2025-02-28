"""
メインプログラムのテストモジュール

このモジュールは、アプリケーションの初期化と実行をテストします。
"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from src.main import Application, main
from src.disk_operations.disk_manager import Disk
from src.file_operations.file_handler import File


def test_main_initialization():
    """メイン関数の初期化テスト"""
    with patch("src.main.Application") as mock_app:
        # モックの設定
        mock_app.return_value.check_sudo_privileges.return_value = True

        # メイン関数を実行
        main()

        # 期待される呼び出しを確認
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

        # 各コンポーネントが正しく初期化されているか確認
        assert mock_window.called
        assert mock_disk_manager.called
        assert mock_file_handler.called
        assert mock_logger.called


@pytest.mark.linux_only
def test_check_sudo_privileges():
    """sudo権限チェックのテスト（Linux環境専用）"""
    with patch("subprocess.run") as mock_run:
        app = Application()

        # sudo権限がある場合
        mock_run.return_value = MagicMock(returncode=0)
        assert app.check_sudo_privileges() is True

        # sudo権限がない場合
        mock_run.side_effect = Exception("Permission denied")
        assert app.check_sudo_privileges() is False


@pytest.mark.linux_only
def test_detect_and_update_disks():
    """ディスク検出と更新のテスト（Linux環境専用）"""
    with patch("src.main.DiskManager") as mock_disk_manager, patch(
        "src.main.MainWindow"
    ) as mock_window:
        app = Application()
        mock_disks = [MagicMock(), MagicMock()]
        app.disk_manager.detect_disks.return_value = mock_disks

        app.detect_and_update_disks()

        # ディスク検出とGUI更新が行われたか確認
        app.disk_manager.detect_disks.assert_called_once()
        app.window.update_disk_list.assert_called_once_with(mock_disks)


@pytest.mark.linux_only
def test_handle_disk_selection():
    """ディスク選択処理のテスト（Linux環境専用）"""
    with patch("src.main.DiskManager") as mock_disk_manager:
        app = Application()
        mock_disk = MagicMock()
        mock_disk.device_path = "/dev/sda1"
        app.disk_manager.detect_disks.return_value = [mock_disk]

        # 正常なディスク選択
        selected_disk = app.handle_disk_selection("/dev/sda1 (500GB)")
        assert selected_disk == mock_disk

        # 無効なディスク選択
        selected_disk = app.handle_disk_selection("/dev/sdb1 (250GB)")
        assert selected_disk is None


@pytest.mark.linux_only
def test_mount_disk():
    """ディスクマウントのテスト（Linux環境専用）"""
    with patch("src.main.DiskManager") as mock_disk_manager:
        app = Application()
        mock_disk = MagicMock()

        # マウント成功
        app.disk_manager.mount_disk.return_value = True
        assert app.mount_disk(mock_disk) is True

        # マウント失敗
        app.disk_manager.mount_disk.return_value = False
        assert app.mount_disk(mock_disk) is False


@pytest.mark.linux_only
def test_unmount_disk():
    """ディスクアンマウントのテスト（Linux環境専用）"""
    with patch("src.main.DiskManager") as mock_disk_manager:
        app = Application()
        mock_disk = MagicMock()

        # アンマウント成功
        app.disk_manager.unmount_disk.return_value = True
        assert app.unmount_disk(mock_disk) is True

        # アンマウント失敗
        app.disk_manager.unmount_disk.return_value = False
        assert app.unmount_disk(mock_disk) is False


@pytest.mark.linux_only
def test_check_disk_status():
    """ディスク状態チェックのテスト（Linux環境専用）"""
    with patch("src.main.DiskManager") as mock_disk_manager:
        app = Application()
        mock_disk = MagicMock()
        mock_status = MagicMock()
        app.disk_manager.check_filesystem.return_value = mock_status

        app.check_disk_status(mock_disk)

        # ファイルシステムチェックとGUI更新が行われたか確認
        app.disk_manager.check_filesystem.assert_called_once_with(mock_disk)
        app.window.display_disk_status.assert_called_once_with(mock_status)


def test_update_file_list():
    """ファイル一覧更新のテスト"""
    with patch("src.main.FileHandler") as mock_file_handler:
        app = Application()
        mock_disk = MagicMock()
        mock_files = [MagicMock(), MagicMock()]
        app.file_handler.list_files.return_value = mock_files

        app.update_file_list(mock_disk)

        # ファイル一覧取得とGUI更新が行われたか確認
        app.file_handler.list_files.assert_called_once()
        app.window.update_file_tree.assert_called_once_with(mock_files)


def test_copy_files():
    """ファイルコピーのテスト"""
    with patch("src.main.FileHandler") as mock_file_handler:
        app = Application()
        mock_files = [MagicMock(), MagicMock()]
        destination = "/path/to/destination"

        # コピー成功
        app.file_handler.copy_files.return_value = True
        app.copy_files(mock_files, destination)

        # プログレスバーの更新とファイルコピーが行われたか確認
        app.window.update_progress.assert_called()
        app.file_handler.copy_files.assert_called_once_with(mock_files, destination)


@pytest.mark.linux_only
def test_run():
    """アプリケーション実行のテスト（Linux環境専用）"""
    with patch("src.main.MainWindow") as mock_window:
        app = Application()

        # イベントループのシミュレーション
        mock_window.return_value.window.read.side_effect = [
            ("-MOUNT-", {}),  # マウントボタンクリック
            ("-COPY-", {}),  # コピーボタンクリック
            ("-EXIT-", None),  # 終了ボタンクリック
        ]

        app.run()

        # ウィンドウが作成され、イベントループが実行されたか確認
        assert mock_window.return_value.create_window.called
        assert mock_window.return_value.window.read.call_count == 3
        assert mock_window.return_value.close.called
