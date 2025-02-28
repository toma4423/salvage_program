"""
DiskManagerクラスのテストモジュール

このモジュールは、ディスク操作の機能をテストします。
"""

import pytest
from unittest.mock import patch, MagicMock
from src.disk_operations.disk_manager import (
    DiskManager,
    Disk,
    FilesystemStatus,
    DiskInfo,
)
import subprocess
import os
import json


@pytest.fixture
def disk_manager():
    """DiskManagerのフィクスチャ"""
    return DiskManager()


@pytest.fixture
def mock_disk():
    """テスト用のディスクフィクスチャ"""
    return Disk("/dev/sda1", 500 * 1024 * 1024 * 1024, "ext4", False, "PASSED")


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_detect_disks(mock_check_output, disk_manager):
    """ディスク検出のテスト（Linux環境専用）"""
    # テスト用のlsblk出力を用意
    lsblk_output = {
        "blockdevices": [
            {
                "name": "sda",
                "size": "10G",
                "fstype": "ext4",
                "mountpoint": "/",
                "health": "PASSED",
            },
            {
                "name": "sdb",
                "size": "500G",
                "fstype": "ntfs",
                "health": "FAILED",
            },
        ]
    }
    mock_check_output.return_value = json.dumps(lsblk_output).encode()

    disks = disk_manager.detect_disks()

    assert len(disks) == 2
    assert disks[0].device_path == "/dev/sda"
    assert disks[0].size == 10 * 1024 * 1024 * 1024  # 10GB
    assert disks[0].filesystem == "ext4"
    assert disks[0].mounted is True
    assert disks[0].health_status == "PASSED"


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_detect_disks_error(mock_check_output, disk_manager):
    """ディスク検出のエラーテスト（Linux環境専用）"""
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "lsblk")
    disks = disk_manager.detect_disks()
    assert len(disks) == 0


@pytest.mark.linux_only
@patch("subprocess.run")
@patch("os.makedirs")
def test_mount_disk_success(mock_makedirs, mock_run, disk_manager, mock_disk):
    """ディスクマウントの成功テスト（Linux環境専用）"""
    mock_run.return_value.returncode = 0
    assert disk_manager.mount_disk(mock_disk) is True
    mock_makedirs.assert_called_once()
    mock_run.assert_called_once()


@pytest.mark.linux_only
@patch("subprocess.run")
def test_mount_disk_failure(mock_run, disk_manager, mock_disk):
    """ディスクマウントの失敗テスト（Linux環境専用）"""
    mock_run.return_value.returncode = 1
    assert disk_manager.mount_disk(mock_disk) is False


@pytest.mark.linux_only
@patch("subprocess.run")
def test_unmount_disk_success(mock_run, disk_manager, mock_disk):
    """ディスクアンマウントの成功テスト（Linux環境専用）"""
    mock_run.return_value.returncode = 0
    assert disk_manager.unmount_disk(mock_disk) is True


@pytest.mark.linux_only
@patch("subprocess.run")
def test_unmount_disk_failure(mock_run, disk_manager, mock_disk):
    """ディスクアンマウントの失敗テスト（Linux環境専用）"""
    mock_run.return_value.returncode = 1
    assert disk_manager.unmount_disk(mock_disk) is False


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ext4_success(mock_check_output, disk_manager, mock_disk):
    """ext4ファイルシステムチェックの成功テスト（Linux環境専用）"""
    mock_check_output.return_value = b"Pass 1: Checking inodes, blocks, and sizes"
    status = disk_manager.check_filesystem(mock_disk)

    assert status.is_consistent is True
    assert "Pass 1" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ext4_failure(mock_check_output, disk_manager, mock_disk):
    """ext4ファイルシステムチェックの失敗テスト（Linux環境専用）"""
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "fsck.ext4")
    status = disk_manager.check_filesystem(mock_disk)

    assert status.is_consistent is False
    assert "エラー" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ntfs_success(mock_check_output, disk_manager):
    """ntfsファイルシステムチェックの成功テスト（Linux環境専用）"""
    ntfs_disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", False, "PASSED")
    mock_check_output.return_value = b"NTFS volume version 3.1"
    status = disk_manager.check_filesystem(ntfs_disk)

    assert status.is_consistent is True
    assert "NTFS" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ntfs_failure(mock_check_output, disk_manager):
    """ntfsファイルシステムチェックの失敗テスト（Linux環境専用）"""
    ntfs_disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", False, "PASSED")
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "ntfsfix")
    status = disk_manager.check_filesystem(ntfs_disk)

    assert status.is_consistent is False
    assert "エラー" in status.details


@pytest.mark.linux_only
def test_check_filesystem_unsupported(disk_manager):
    """未対応ファイルシステムのテスト（Linux環境専用）"""
    unsupported_disk = Disk(
        "/dev/sdb1", 500 * 1024 * 1024 * 1024, "hfs+", False, "PASSED"
    )
    status = disk_manager.check_filesystem(unsupported_disk)

    assert status.is_consistent is False
    assert "未対応" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_get_disk_info_success(mock_check_output, disk_manager, mock_disk):
    """ディスク情報取得の成功テスト（Linux環境専用）"""
    # テスト用のコマンド出力を用意
    mock_check_output.side_effect = [
        json.dumps(
            {"model": "Samsung SSD 860 EVO", "serial": "S3YJNB0K500001"}
        ).encode(),
        b'TYPE="gpt"',
        json.dumps({"smart_status": {"passed": True}}).encode(),
    ]

    disk_info = disk_manager.get_disk_info(mock_disk)

    assert disk_info.model == "Samsung SSD 860 EVO"
    assert disk_info.serial == "S3YJNB0K500001"
    assert disk_info.partition_table == "gpt"
    assert disk_info.smart_status["passed"] is True


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_get_disk_info_failure(mock_check_output, disk_manager, mock_disk):
    """ディスク情報取得の失敗テスト（Linux環境専用）"""
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "lsblk")
    disk_info = disk_manager.get_disk_info(mock_disk)

    assert disk_info.model == "不明"
    assert disk_info.serial == "不明"
    assert disk_info.partition_table == "不明"
    assert disk_info.smart_status == {}


@pytest.mark.parametrize(
    "size_str,expected",
    [
        ("10G", 10 * 1024 * 1024 * 1024),
        ("500M", 500 * 1024 * 1024),
        ("1T", 1024 * 1024 * 1024 * 1024),
        ("invalid", 0),
    ],
)
def test_parse_size(size_str, expected, disk_manager):
    """サイズ文字列のパース処理テスト"""
    assert disk_manager._parse_size(size_str) == expected
