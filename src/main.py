"""
JSDoc: プロジェクトのエントリーポイント
概要: 本ファイルは、データサルベージプログラムのアプリケーションを初期化し、GUIウィンドウの設定、イベントループ、sudo権限取得、全体のエラーハンドリングを行います。
仕様: Python (PEP8準拠、type hint使用)
制限: Linux環境（LubuntuまたはUbuntuベース）での動作を前提とする
"""

import sys
import os
import subprocess
from typing import Optional, Tuple, List
import PySimpleGUI as sg

from .gui.main_window import MainWindow
from .disk_operations.disk_manager import DiskManager, Disk
from .file_operations.file_handler import FileHandler, File
from .utils.logger import Logger


class Application:
    """アプリケーションのメインクラス

    Attributes:
        window (MainWindow): GUIウィンドウ
        disk_manager (DiskManager): ディスク操作マネージャー
        file_handler (FileHandler): ファイル操作ハンドラー
        logger (Logger): ログ管理
    """

    def __init__(self) -> None:
        """アプリケーションの初期化"""
        self.window = MainWindow()
        self.disk_manager = DiskManager()
        self.file_handler = FileHandler()
        self.logger = Logger()

    def check_sudo_privileges(self) -> bool:
        """sudo権限があるかチェックする

        Returns:
            bool: sudo権限がある場合はTrue、ない場合はFalse
        """
        try:
            subprocess.run(["sudo", "-n", "true"])
            return True
        except Exception as e:
            self.logger.log_error(f"sudo権限の取得に失敗しました: {e}")
            self.logger.log_error("エラーコード: SYS_001")
            return False

    def detect_and_update_disks(self) -> None:
        """ディスクを検出してGUIを更新する"""
        try:
            disks = self.disk_manager.detect_disks()
            self.window.update_disk_list(disks)
            self.logger.log_info(f"{len(disks)}台のディスクを検出しました")
        except Exception as e:
            self.logger.log_error(f"ディスクの検出に失敗しました: {e}")
            self.logger.log_error("エラーコード: DISK_001")
            self.window.show_error("ディスクの検出に失敗しました")

    def handle_disk_selection(self, selected_disk: str) -> Optional[Disk]:
        """ディスク選択を処理する

        Args:
            selected_disk (str): 選択されたディスクの文字列表現

        Returns:
            Optional[Disk]: 選択されたディスクオブジェクト
        """
        try:
            # 文字列からデバイスパスを抽出
            device_path = selected_disk.split(" ")[0]
            # 選択されたデバイスパスに一致するディスクを検索
            disks = self.disk_manager.detect_disks()
            for disk in disks:
                if disk.device_path == device_path:
                    return disk
        except Exception as e:
            self.logger.log_error(f"ディスクの選択に失敗しました: {e}")
            self.window.show_error("ディスクの選択に失敗しました")
        return None

    def mount_disk(self, disk: Disk) -> bool:
        """ディスクをマウントする

        Args:
            disk (Disk): マウント対象のディスク

        Returns:
            bool: マウントに成功した場合はTrue
        """
        try:
            if self.disk_manager.mount_disk(disk):
                self.logger.log_info(f"{disk.device_path} をマウントしました")
                return True
            else:
                self.window.show_error(f"{disk.device_path} のマウントに失敗しました")
                return False
        except Exception as e:
            self.logger.log_error(f"マウント処理でエラーが発生しました: {e}")
            self.window.show_error("マウント処理でエラーが発生しました")
            return False

    def unmount_disk(self, disk: Disk) -> bool:
        """ディスクをアンマウントする

        Args:
            disk (Disk): アンマウント対象のディスク

        Returns:
            bool: アンマウントに成功した場合はTrue
        """
        try:
            if self.disk_manager.unmount_disk(disk):
                self.logger.log_info(f"{disk.device_path} をアンマウントしました")
                return True
            else:
                self.window.show_error(
                    f"{disk.device_path} のアンマウントに失敗しました"
                )
                return False
        except Exception as e:
            self.logger.log_error(f"アンマウント処理でエラーが発生しました: {e}")
            self.window.show_error("アンマウント処理でエラーが発生しました")
            return False

    def check_disk_status(self, disk: Disk) -> None:
        """ディスクの状態をチェックしてGUIを更新する

        Args:
            disk (Disk): チェック対象のディスク
        """
        try:
            status = self.disk_manager.check_filesystem(disk)
            self.window.display_disk_status(status)
            self.logger.log_info(f"{disk.device_path} の状態チェックが完了しました")
        except Exception as e:
            self.logger.log_error(f"ディスク状態のチェックに失敗しました: {e}")
            self.window.show_error("ディスク状態のチェックに失敗しました")

    def update_file_list(self, disk: Disk) -> None:
        """ファイル一覧を更新する

        Args:
            disk (Disk): 対象のディスク
        """
        try:
            mount_point = f"/mnt/{disk.device_path.split('/')[-1]}"
            files = self.file_handler.list_files(mount_point)
            self.window.update_file_tree(files)
            self.logger.log_info(f"{len(files)}個のファイルを検出しました")
        except Exception as e:
            self.logger.log_error(f"ファイル一覧の更新に失敗しました: {e}")
            self.window.show_error("ファイル一覧の更新に失敗しました")

    def copy_files(self, files: List[File], destination: str) -> None:
        """ファイルをコピーする

        Args:
            files (List[File]): コピー対象のファイル
            destination (str): コピー先のパス
        """
        try:
            total_files = len(files)
            for i, file in enumerate(files, 1):
                progress = int((i / total_files) * 100)
                self.window.update_progress(
                    progress, f"{file.path} をコピー中... ({i}/{total_files})"
                )

                if self.file_handler.copy_files([file], destination):
                    if self.file_handler.verify_copy(
                        file.path,
                        os.path.join(destination, os.path.basename(file.path)),
                    ):
                        self.logger.log_info(f"{file.path} のコピーが完了しました")
                    else:
                        self.logger.log_error(f"{file.path} のコピー検証に失敗しました")
                        self.window.show_error(
                            f"{file.path} のコピー検証に失敗しました"
                        )
                else:
                    self.logger.log_error(f"{file.path} のコピーに失敗しました")
                    self.window.show_error(f"{file.path} のコピーに失敗しました")

            self.window.update_progress(100, "すべてのファイルのコピーが完了しました")
        except Exception as e:
            self.logger.log_error(f"ファイルコピー中にエラーが発生しました: {e}")
            self.window.show_error("ファイルコピー中にエラーが発生しました")

    def run(self) -> None:
        """アプリケーションのメインループを実行する"""
        if not self.check_sudo_privileges():
            sg.popup_error("sudo権限が必要です。sudo権限を付与して再実行してください。")
            return

        self.window.create_window()
        self.detect_and_update_disks()

        while True:
            if not self.window.window:
                break

            event, values = self.window.window.read()

            if event in (sg.WIN_CLOSED, "-EXIT-"):
                break

            elif event == "-HELP-":
                self.window.show_help()

            elif event == "-DISK_LIST-" and values["-DISK_LIST-"]:
                disk = self.handle_disk_selection(values["-DISK_LIST-"][0])
                if disk:
                    self.window.current_disk = disk
                    self.check_disk_status(disk)

            elif event == "-MOUNT-":
                if self.window.current_disk:
                    if self.mount_disk(self.window.current_disk):
                        self.update_file_list(self.window.current_disk)

            elif event == "-UNMOUNT-":
                if self.window.current_disk:
                    self.unmount_disk(self.window.current_disk)

            elif event == "-FILE_TREE-":
                if values["-FILE_TREE-"]:
                    self.window.selected_files = values["-FILE_TREE-"]

            elif event == "-SELECT_ALL-":
                if self.window.window["-FILE_TREE-"].get_children():
                    self.window.selected_files = self.window.window[
                        "-FILE_TREE-"
                    ].get_children()

            elif event == "-DESELECT-":
                self.window.selected_files = []

            elif event == "-COPY-":
                if not self.window.selected_files:
                    self.window.show_error("コピーするファイルを選択してください")
                    continue

                if not values["-DEST_PATH-"]:
                    self.window.show_error("コピー先を指定してください")
                    continue

                self.copy_files(self.window.selected_files, values["-DEST_PATH-"])

        self.window.close()
        self.logger.save_logs("salvage_program.log")


def main() -> None:
    """アプリケーションのメイン処理

    Returns:
        None
    """
    try:
        app = Application()
        app.run()
    except Exception as e:
        sg.popup_error(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
