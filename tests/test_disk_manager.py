import pytest
from unittest.mock import patch
from src.disk_operations.disk_manager import (
    DiskManager,
    Disk,
    FilesystemStatus,
    DiskInfo,
)
import subprocess
import os


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_detect_disks(mock_check_output):
    """ディスク検出のテスト（Linux環境専用）"""
    # テスト用のlsblk出力を用意
    lsblk_output = """
    {
        "blockdevices": [
            {"name": "sda", "size": "10G", "fstype": "ext4", "mountpoint": "/", "health": "PASSED"},
            {"name": "sdb", "size": "500G", "fstype": "ntfs", "health": "FAILED"}
        ]
    }
    """
    mock_check_output.return_value = lsblk_output.encode()

    disk_manager = DiskManager()
    disks = disk_manager.detect_disks()

    assert len(disks) == 2
    assert disks[0].device_path == "/dev/sda"
    assert disks[0].size == 10 * 1024 * 1024 * 1024  # 10GB
    assert disks[0].filesystem == "ext4"
    assert disks[0].mounted is True
    assert disks[0].health_status == "PASSED"


@pytest.mark.linux_only
@patch("subprocess.run")
@patch("os.makedirs")
def test_mount_disk_success(mock_makedirs, mock_run):
    """ディスクマウントの成功テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", False, "PASSED")

    mock_run.return_value.returncode = 0
    assert disk_manager.mount_disk(disk) is True


@pytest.mark.linux_only
@patch("subprocess.run")
def test_mount_disk_failure(mock_run):
    """ディスクマウントの失敗テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", False, "PASSED")

    mock_run.return_value.returncode = 1
    assert disk_manager.mount_disk(disk) is False


@pytest.mark.linux_only
@patch("subprocess.run")
def test_unmount_disk_success(mock_run):
    """ディスクアンマウントの成功テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", True, "PASSED")

    mock_run.return_value.returncode = 0
    assert disk_manager.unmount_disk(disk) is True


@pytest.mark.linux_only
@patch("subprocess.run")
def test_unmount_disk_failure(mock_run):
    """ディスクアンマウントの失敗テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", True, "PASSED")

    mock_run.return_value.returncode = 1
    assert disk_manager.unmount_disk(disk) is False


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ext4_success(mock_check_output):
    """ext4ファイルシステムチェックの成功テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ext4", False, "PASSED")

    mock_check_output.return_value = b"Pass 1: Checking inodes, blocks, and sizes"
    status = disk_manager.check_filesystem(disk)

    assert status.is_consistent is True
    assert "Pass 1" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ext4_failure(mock_check_output):
    """ext4ファイルシステムチェックの失敗テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ext4", False, "PASSED")

    mock_check_output.side_effect = subprocess.CalledProcessError(1, "fsck.ext4")
    status = disk_manager.check_filesystem(disk)

    assert status.is_consistent is False
    assert "エラー" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ntfs_success(mock_check_output):
    """ntfsファイルシステムチェックの成功テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", False, "PASSED")

    mock_check_output.return_value = b"NTFS volume version 3.1"
    status = disk_manager.check_filesystem(disk)

    assert status.is_consistent is True
    assert "NTFS" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_check_filesystem_ntfs_failure(mock_check_output):
    """ntfsファイルシステムチェックの失敗テスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "ntfs", False, "PASSED")

    mock_check_output.side_effect = subprocess.CalledProcessError(1, "ntfsfix")
    status = disk_manager.check_filesystem(disk)

    assert status.is_consistent is False
    assert "エラー" in status.details


@pytest.mark.linux_only
def test_check_filesystem_unsupported(capsys):
    """未対応ファイルシステムのテスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb1", 500 * 1024 * 1024 * 1024, "hfs+", False, "PASSED")

    status = disk_manager.check_filesystem(disk)

    assert status.is_consistent is False
    assert "未対応" in status.details


@pytest.mark.linux_only
@patch("subprocess.check_output")
def test_get_disk_info(mock_check_output):
    """ディスク情報取得のテスト（Linux環境専用）"""
    disk_manager = DiskManager()
    disk = Disk("/dev/sdb", 500 * 1024 * 1024 * 1024, "ntfs", False, "PASSED")

    # テスト用のコマンド出力を用意
    lsblk_output = b'{"model": "Samsung SSD 860 EVO", "serial": "S3YJNB0K500001"}'
    blkid_output = b'TYPE="gpt"'
    smartctl_output = b'{"smart_status": {"passed": true}}'

    mock_check_output.side_effect = [lsblk_output, blkid_output, smartctl_output]

    disk_info = disk_manager.get_disk_info(disk)

    assert disk_info.model == "Samsung SSD 860 EVO"
    assert disk_info.serial == "S3YJNB0K500001"
    assert disk_info.partition_table == "gpt"
    assert disk_info.smart_status["passed"] is True
