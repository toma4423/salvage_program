"""
JSDoc: ディスク操作モジュール
概要: 本ファイルは、内蔵ディスクの自動検出、マウント・アンマウント、ファイルシステムのチェック、及びディスク情報の取得を行うDiskManagerクラスを提供します。
仕様: Python (PEP8準拠、type hint使用)
制限: Linux環境（LubuntuまたはUbuntuベース）での動作を前提とする
"""

import os
import subprocess
import json
from typing import List, Any
from ..utils.logger import Logger


class Disk:
    """ディスク情報を表すクラス

    Attributes:
        device_path (str): デバイスパス
        size (int): ディスクのサイズ
        filesystem (str): ファイルシステムの種類
        mounted (bool): マウント状態
        health_status (str): ヘルスステータス
    """

    def __init__(
        self,
        device_path: str,
        size: int,
        filesystem: str,
        mounted: bool,
        health_status: str,
    ) -> None:
        self.device_path = device_path
        self.size = size
        self.filesystem = filesystem
        self.mounted = mounted
        self.health_status = health_status


class FilesystemStatus:
    """ファイルシステムの状態を表すクラス

    Attributes:
        is_consistent (bool): ファイルシステムの整合性
        details (str): 状態詳細
    """

    def __init__(self, is_consistent: bool, details: str) -> None:
        self.is_consistent = is_consistent
        self.details = details


class DiskInfo:
    """ディスクの詳細情報を表すクラス

    Attributes:
        model (str): ディスクのモデル
        serial (str): シリアル番号
        partition_table (str): パーティションテーブルの種類
        smart_status (Any): SMARTステータス情報
    """

    def __init__(
        self, model: str, serial: str, partition_table: str, smart_status: Any
    ) -> None:
        self.model = model
        self.serial = serial
        self.partition_table = partition_table
        self.smart_status = smart_status


class DiskManager:
    """ディスクの操作を管理するクラス

    Methods:
        detect_disks() -> List[Disk]: 内蔵ディスクの自動検出
        mount_disk(disk: Disk) -> bool: ディスクのマウント
        unmount_disk(disk: Disk) -> bool: ディスクのアンマウント
        check_filesystem(disk: Disk) -> FilesystemStatus: ファイルシステムのチェック
        get_disk_info(disk: Disk) -> DiskInfo: ディスク情報の取得
    """

    def __init__(self):
        self.logger = Logger()

    def detect_disks(self) -> List[Disk]:
        """内蔵ディスクの自動検出を行う

        Returns:
            List[Disk]: 検出されたディスクのリスト
        """
        disks = []

        # lsblkコマンドを実行してディスク情報を取得
        output = subprocess.check_output(
            ["lsblk", "-J", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,HEALTH"],
            universal_newlines=True,
        )
        disk_info = json.loads(output)

        for disk in disk_info["blockdevices"]:
            # ディスク情報をDiskオブジェクトに変換
            device_path = f"/dev/{disk['name']}"
            size = self._parse_size(disk["size"])
            filesystem = disk.get("fstype", "")
            mounted = "mountpoint" in disk
            health_status = disk.get("health", "")

            disk_obj = Disk(device_path, size, filesystem, mounted, health_status)
            disks.append(disk_obj)

        return disks

    def _parse_size(self, size_str: str) -> int:
        """ディスクサイズ文字列をバイト単位の整数に変換する

        Args:
            size_str (str): ディスクサイズの文字列（例: "10G"）

        Returns:
            int: バイト単位のディスクサイズ
        """
        units = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
        size = float(size_str[:-1])
        unit = size_str[-1].upper()
        return int(size * units[unit])

    def mount_disk(self, disk: Disk) -> bool:
        """指定されたディスクのマウントを実施する

        Args:
            disk (Disk): マウント対象のディスク

        Returns:
            bool: マウントに成功したかどうか
        """
        mount_point = f"/mnt/{disk.device_path.split('/')[-1]}"

        try:
            # マウントポイントのディレクトリが存在しない場合は作成
            os.makedirs(mount_point, exist_ok=True)

            # マウントコマンドを実行
            subprocess.run(["mount", disk.device_path, mount_point], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(f"ディスクのマウントに失敗しました: {e}")
            self.logger.log_error(f"エラーコード: DISK_002")
            self.logger.log_error(f"ディスク: {disk.device_path}")
            self.logger.log_error(f"マウントポイント: {mount_point}")
            return False

    def unmount_disk(self, disk: Disk) -> bool:
        """指定されたディスクのアンマウントを実施する

        Args:
            disk (Disk): アンマウント対象のディスク

        Returns:
            bool: アンマウントに成功したかどうか
        """
        try:
            # アンマウントコマンドを実行
            subprocess.run(["umount", disk.device_path], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(f"ディスクのアンマウントに失敗しました: {e}")
            self.logger.log_error(f"エラーコード: DISK_003")
            self.logger.log_error(f"ディスク: {disk.device_path}")
            return False

    def check_filesystem(self, disk: Disk) -> FilesystemStatus:
        """マウントされたディスクのファイルシステムの状態を検査する

        Args:
            disk (Disk): チェック対象のディスク

        Returns:
            FilesystemStatus: 検査結果
        """
        if disk.filesystem == "ext4":
            # ext4ファイルシステムの場合はfsck.ext4コマンドを実行
            try:
                output = subprocess.check_output(
                    ["fsck.ext4", "-n", disk.device_path],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
                if "clean" in output:
                    return FilesystemStatus(
                        is_consistent=True,
                        details="ファイルシステムは整合性が取れています",
                    )
                else:
                    return FilesystemStatus(is_consistent=False, details=output)
            except subprocess.CalledProcessError as e:
                self.logger.log_error(
                    f"ファイルシステムチェックに失敗しました: {e.output}"
                )
                self.logger.log_error(f"エラーコード: DISK_004")
                self.logger.log_error(f"ディスク: {disk.device_path}")
                return FilesystemStatus(is_consistent=False, details=e.output)

        elif disk.filesystem == "ntfs":
            # ntfsファイルシステムの場合はntfsfixコマンドを実行
            try:
                subprocess.check_output(
                    ["ntfsfix", disk.device_path],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
                return FilesystemStatus(
                    is_consistent=True, details="ファイルシステムは整合性が取れています"
                )
            except subprocess.CalledProcessError as e:
                self.logger.log_error(
                    f"ファイルシステムチェックに失敗しました: {e.output}"
                )
                self.logger.log_error(f"エラーコード: DISK_004")
                self.logger.log_error(f"ディスク: {disk.device_path}")
                return FilesystemStatus(is_consistent=False, details=e.output)

        else:
            self.logger.log_error(f"未対応のファイルシステムです: {disk.filesystem}")
            self.logger.log_error(f"エラーコード: DISK_005")
            self.logger.log_error(f"ディスク: {disk.device_path}")
            return FilesystemStatus(
                is_consistent=False, details="未対応のファイルシステムです"
            )

    def get_disk_info(self, disk: Disk) -> DiskInfo:
        """指定されたディスクの詳細情報を取得する

        Args:
            disk (Disk): 対象のディスク

        Returns:
            DiskInfo: ディスクの詳細情報
        """
        # lsblkコマンドを実行してモデル名とシリアル番号を取得
        output = subprocess.check_output(
            ["lsblk", "-dno", "MODEL,SERIAL", disk.device_path],
            universal_newlines=True,
        )
        model, serial = output.strip().split(" ")

        # blkidコマンドを実行してパーティションテーブルの種類を取得
        output = subprocess.check_output(
            ["blkid", "-o", "value", "-s", "PTTYPE", disk.device_path],
            universal_newlines=True,
        )
        partition_table = output.strip()

        # smartctlコマンドを実行してSMARTステータス情報を取得
        try:
            output = subprocess.check_output(
                ["smartctl", "-i", "-H", "-c", "-A", disk.device_path],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            smart_status = self._parse_smart_status(output)
        except subprocess.CalledProcessError as e:
            self.logger.log_error(f"SMARTステータスの取得に失敗しました: {e.output}")
            self.logger.log_error(f"エラーコード: DISK_006")
            self.logger.log_error(f"ディスク: {disk.device_path}")
            smart_status = {}

        return DiskInfo(model, serial, partition_table, smart_status)

    def _parse_smart_status(self, output: str) -> dict:
        """smartctlコマンドの出力からSMARTステータス情報を解析する

        Args:
            output (str): smartctlコマンドの出力

        Returns:
            dict: SMARTステータス情報
        """
        smart_status = {}

        for line in output.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                smart_status[key.strip()] = value.strip()

        return smart_status
