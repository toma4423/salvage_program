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


@patch("subprocess.check_output")
def test_detect_disks(mock_check_output):
    # テスト用のlsblk出力を用意
    lsblk_output = """
    {
        "blockdevices": [
            {"name": "sda", "size": "10G", "fstype": "ext4", "mountpoint": "/", "health": "PASSED"},
            {"name": "sdb", "size": "500G", "fstype": "ntfs", "health": "FAILED"}
        ]
    }
    """
    mock_check_output.return_value = lsblk_output

    dm = DiskManager()
    disks = dm.detect_disks()

    assert len(disks) == 2
    assert disks[0].device_path == "/dev/sda"
    assert disks[0].size == 10 * 1024**3
    assert disks[0].filesystem == "ext4"
    assert disks[0].mounted == True
    assert disks[0].health_status == "PASSED"
    assert disks[1].device_path == "/dev/sdb"
    assert disks[1].size == 500 * 1024**3
    assert disks[1].filesystem == "ntfs"
    assert disks[1].mounted == False
    assert disks[1].health_status == "FAILED"


@patch("subprocess.run")
@patch("os.makedirs")
def test_mount_disk_success(mock_makedirs, mock_run):
    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ext4", False, "良好")
    result = dm.mount_disk(disk)

    mock_makedirs.assert_called_once_with("/mnt/sdc", exist_ok=True)
    mock_run.assert_called_once_with(["mount", "/dev/sdc", "/mnt/sdc"], check=True)
    assert result is True


@patch("subprocess.run")
def test_mount_disk_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "mount")

    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ext4", False, "良好")
    result = dm.mount_disk(disk)

    assert result is False


@patch("subprocess.run")
def test_unmount_disk_success(mock_run):
    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ext4", True, "良好")
    result = dm.unmount_disk(disk)

    mock_run.assert_called_once_with(["umount", "/dev/sdc"], check=True)
    assert result is True


@patch("subprocess.run")
def test_unmount_disk_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "umount")

    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ext4", True, "良好")
    result = dm.unmount_disk(disk)

    assert result is False


@patch("subprocess.check_output")
def test_check_filesystem_ext4_success(mock_check_output):
    mock_check_output.return_value = "fsck.ext4: /dev/sdc is clean"

    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ext4", True, "良好")
    fs_status = dm.check_filesystem(disk)

    mock_check_output.assert_called_once_with(
        ["fsck.ext4", "-n", "/dev/sdc"],
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    assert fs_status.is_consistent is True
    assert fs_status.details == "ファイルシステムは整合性が取れています"


@patch("subprocess.check_output")
def test_check_filesystem_ext4_failure(mock_check_output):
    mock_check_output.side_effect = subprocess.CalledProcessError(
        1, "fsck.ext4", output="Filesystem errors detected"
    )

    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ext4", True, "良好")
    fs_status = dm.check_filesystem(disk)

    assert fs_status.is_consistent is False
    assert fs_status.details == "Filesystem errors detected"


@patch("subprocess.check_output")
def test_check_filesystem_ntfs_success(mock_check_output):
    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ntfs", True, "良好")
    fs_status = dm.check_filesystem(disk)

    mock_check_output.assert_called_once_with(
        ["ntfsfix", "/dev/sdc"], stderr=subprocess.STDOUT, universal_newlines=True
    )
    assert fs_status.is_consistent is True
    assert fs_status.details == "ファイルシステムは整合性が取れています"


@patch("subprocess.check_output")
def test_check_filesystem_ntfs_failure(mock_check_output):
    mock_check_output.side_effect = subprocess.CalledProcessError(
        1, "ntfsfix", output="Filesystem errors detected"
    )

    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "ntfs", True, "良好")
    fs_status = dm.check_filesystem(disk)

    assert fs_status.is_consistent is False
    assert fs_status.details == "Filesystem errors detected"


def test_check_filesystem_unsupported(capsys):
    dm = DiskManager()
    disk = Disk("/dev/sdc", 1000, "exfat", True, "良好")
    fs_status = dm.check_filesystem(disk)

    captured = capsys.readouterr()
    assert "未対応のファイルシステムです: exfat" in captured.out
    assert fs_status.is_consistent is False
    assert fs_status.details == "未対応のファイルシステムです"


@patch("subprocess.check_output")
def test_get_disk_info(mock_check_output):
    # テスト用のlsblk、blkid、smartctlの出力を用意
    lsblk_output = "TOSHIBA_DT01ACA050 1234ABCD"
    blkid_output = "gpt"
    smartctl_output = """
    Model Family:     TOSHIBA DT01ACA050
    Device Model:     TOSHIBA DT01ACA050
    Serial Number:    1234ABCD
    LU WWN Device Id: 5 000039 ff6c120003
    Firmware Version: MS1OA750
    User Capacity:    500,107,862,016 bytes [500 GB]
    Sector Sizes:     512 bytes logical, 4096 bytes physical
    Rotation Rate:    7200 rpm
    Form Factor:      3.5 inches
    Device is:        In smartctl database [for details use: -P show]
    ATA Version is:   ATA8-ACS T13/1699-D revision 4
    SATA Version is:  SATA 3.0, 6.0 Gb/s (current: 6.0 Gb/s)
    Local Time is:    Mon Apr 24 10:00:00 2023 JST
    SMART support is: Available - device has SMART capability.
    SMART support is: Enabled
    
    === START OF READ SMART DATA SECTION ===
    SMART overall-health self-assessment test result: PASSED
    
    General SMART Values:
    Offline data collection status:  (0x00) Offline data collection activity
                        was never started.
                        Auto Offline Data Collection: Disabled.
    Self-test execution status:      (   0) The previous self-test routine completed
                        without error or no self-test has ever 
                        been run.
    Total time to complete Offline 
    data collection:        (  120) seconds.
    Offline data collection
    capabilities:            (0x5b) SMART execute Offline immediate.
                        Auto Offline data collection on/off support.
                        Suspend Offline collection upon new
                        command.
                        Offline surface scan supported.
                        Self-test supported.
                        No Conveyance Self-test supported.
                        Selective Self-test supported.
    SMART capabilities:            (0x0003) Saves SMART data before entering
                        power-saving mode.
                        Supports SMART auto save timer.
    Error logging capability:        (0x01) Error logging supported.
                        General Purpose Logging supported.
    Short self-test routine 
    recommended polling time:    (   2) minutes.
    Extended self-test routine
    recommended polling time:    ( 255) minutes.
    SCT capabilities:          (0x003d) SCT Status supported.
                        SCT Error Recovery Control supported.
                        SCT Feature Control supported.
                        SCT Data Table supported.
    
    SMART Attributes Data Structure revision number: 16
    Vendor Specific SMART Attributes with Thresholds:
    ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
      1 Raw_Read_Error_Rate     0x000b   100   100   050    Pre-fail  Always       -       0
      2 Throughput_Performance  0x0005   100   100   050    Pre-fail  Offline      -       0
      3 Spin_Up_Time            0x0007   100   100   001    Pre-fail  Always       -       3092
      4 Start_Stop_Count        0x0012   100   100   000    Old_age   Always       -       1
      5 Reallocated_Sector_Ct   0x0033   100   100   050    Pre-fail  Always       -       0
      7 Seek_Error_Rate         0x000b   100   100   050    Pre-fail  Always       -       0
      8 Seek_Time_Performance   0x0005   100   100   050    Pre-fail  Offline      -       0
      9 Power_On_Hours          0x0012   100   100   000    Old_age   Always       -       0
     10 Spin_Retry_Count        0x0013   100   100   030    Pre-fail  Always       -       0
     12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       1
    191 G-Sense_Error_Rate      0x000a   100   100   000    Old_age   Always       -       0
    192 Power-Off_Retract_Count 0x0032   100   100   000    Old_age   Always       -       0
    193 Load_Cycle_Count        0x0012   100   100   000    Old_age   Always       -       1
    194 Temperature_Celsius     0x0002   169   169   000    Old_age   Always       -       31 (Min/Max 20/50)
    196 Reallocated_Event_Count 0x0032   100   100   000    Old_age   Always       -       0
    197 Current_Pending_Sector  0x0022   100   100   000    Old_age   Always       -       0
    198 Offline_Uncorrectable   0x0008   100   100   000    Old_age   Offline      -       0
    199 UDMA_CRC_Error_Count    0x000a   200   200   000    Old_age   Always       -       0
    
    SMART Error Log Version: 1
    No Errors Logged
    
    SMART Self-test log structure revision number 1
    No self-tests have been logged.  [To run self-tests, use: smartctl -t]
    
    
    SMART Selective self-test log data structure revision number 1
     SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS
        1        0        0  Not_testing
        2        0        0  Not_testing
        3        0        0  Not_testing
        4        0        0  Not_testing
        5        0        0  Not_testing
    Selective self-test flags (0x0):
      After scanning selected spans, do NOT read-scan remainder of disk.
    If Selective self-test is pending on power-up, resume after 0 minute delay.
    """

    mock_check_output.side_effect = [lsblk_output, blkid_output, smartctl_output]

    dm = DiskManager()
    disk = Disk("/dev/sda", 500 * 1024**3, "ext4", True, "PASSED")
    info = dm.get_disk_info(disk)

    assert info.model == "TOSHIBA_DT01ACA050"
    assert info.serial == "1234ABCD"
    assert info.partition_table == "gpt"
    assert "Device Model" in info.smart_status
    assert info.smart_status["Device Model"] == "TOSHIBA DT01ACA050"
    assert "Serial Number" in info.smart_status
    assert info.smart_status["Serial Number"] == "1234ABCD"
    assert "SMART overall-health self-assessment test result" in info.smart_status
    assert (
        info.smart_status["SMART overall-health self-assessment test result"]
        == "PASSED"
    )
