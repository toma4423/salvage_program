"""
JSDoc: GUIモジュール
概要: 本ファイルは、デスクトップアプリケーションのGUIを構築するためのMainWindowクラスを提供します。
仕様: Python (PEP8準拠、type hint使用)
制限: Linux環境（LubuntuまたはUbuntuベース）での動作を前提とする
"""

from typing import List, Any, Optional, Dict
import PySimpleGUI as sg
from ..disk_operations.disk_manager import Disk, FilesystemStatus
from ..file_operations.file_handler import File
import os


class MainWindow:
    """
    GUIウィンドウを管理するクラス

    Attributes:
        window (Optional[sg.Window]): PySimpleGUIウィンドウオブジェクト
        current_disk (Optional[Disk]): 現在選択中のディスク
        selected_files (List[File]): 選択されたファイルのリスト
    """

    def __init__(self) -> None:
        """MainWindowクラスの初期化"""
        self.window: Optional[sg.Window] = None
        self.current_disk: Optional[Disk] = None
        self.selected_files: List[File] = []

    def create_layout(self) -> List[List[sg.Element]]:
        """GUIレイアウトの作成

        Returns:
            List[List[sg.Element]]: 作成されたレイアウト
        """
        # ディスク情報セクション
        disk_section = [
            [sg.Text("検出されたディスク", font=("", 12))],
            [
                sg.Tree(
                    data=sg.TreeData(),
                    headings=["サイズ", "状態"],
                    auto_size_columns=True,
                    num_rows=10,
                    col0_width=30,
                    key="-DISK_TREE-",
                    enable_events=True,
                )
            ],
            [
                sg.Text("ディスク状態:", size=(12, 1)),
                sg.Text("", size=(38, 1), key="-DISK_STATUS-"),
            ],
        ]

        # ファイル操作セクション
        file_section = [
            [sg.Text("ファイル一覧", font=("", 12))],
            [
                sg.Tree(
                    data=sg.TreeData(),
                    headings=["サイズ", "状態"],
                    auto_size_columns=True,
                    num_rows=10,
                    col0_width=30,
                    key="-FILE_TREE-",
                    enable_events=True,
                )
            ],
            [
                sg.Button("選択", key="-SELECT-"),
                sg.Button("すべて選択", key="-SELECT_ALL-"),
                sg.Button("選択解除", key="-DESELECT-"),
            ],
        ]

        # 操作セクション
        operation_section = [
            [sg.Text("操作", font=("", 12))],
            [
                sg.Button("マウント", key="-MOUNT-"),
                sg.Button("アンマウント", key="-UNMOUNT-"),
                sg.Button("コピー開始", key="-COPY-"),
            ],
            [sg.Text("保存先:")],
            [
                sg.Input(key="-DEST_PATH-", size=(35, 1)),
                sg.FolderBrowse("参照", key="-BROWSE-"),
            ],
        ]

        # プログレスセクション
        progress_section = [
            [sg.Text("進捗状況", font=("", 12))],
            [sg.ProgressBar(100, orientation="h", size=(40, 20), key="-PROGRESS-")],
            [sg.Text("", size=(50, 2), key="-STATUS-")],
        ]

        # レイアウトの組み立て
        layout = [
            [sg.Text("データサルベージプログラム", font=("", 16))],
            [sg.Column(disk_section)],
            [sg.Column(file_section)],
            [sg.Column(operation_section)],
            [sg.Column(progress_section)],
            [sg.Button("ヘルプ", key="-HELP-"), sg.Button("終了", key="-EXIT-")],
        ]

        return layout

    def create_window(self) -> None:
        """GUIウィンドウを作成する"""
        layout = self.create_layout()
        self.window = sg.Window(
            "データサルベージプログラム",
            layout,
            finalize=True,
            resizable=True,
        )

    def update_disk_list(self, disks: List[Disk]) -> None:
        """ディスク一覧を更新する

        Args:
            disks (List[Disk]): 更新するディスクリスト
        """
        if self.window:
            disk_list = [
                f"{disk.device_path} ({disk.size / (1024**3):.1f}GB, {disk.filesystem})"
                for disk in disks
            ]
            self.window["-DISK_LIST-"].update(values=disk_list)

    def update_file_tree(self, files: List[File]) -> None:
        """ファイル一覧ツリーを更新する

        Args:
            files (List[File]): 更新するファイルリスト
        """
        if self.window:
            treedata = sg.TreeData()

            # ルートディレクトリを追加
            treedata.Insert("", "/", "ルート", ["", ""])

            # ファイルをツリーに追加
            for file in files:
                # ファイルサイズを適切な単位に変換
                size = self._format_size(file.size)
                # ファイルの状態を日本語で表示
                status = "正常" if not file.is_corrupted else "破損"
                # ファイルパスから親ディレクトリを取得
                parent = os.path.dirname(file.path)
                if not parent:
                    parent = "/"
                # 親ディレクトリが存在しない場合は作成
                if parent not in treedata.tree_dict:
                    treedata.Insert("/", parent, parent, ["", ""])
                # ファイル名を取得
                filename = os.path.basename(file.path)
                # ツリーにデータを追加
                treedata.Insert(parent, file.path, filename, [size, status])

            self.window["-FILE_TREE-"].update(values=treedata)

    def _format_size(self, size: int) -> str:
        """ファイルサイズを読みやすい形式に変換する

        Args:
            size (int): バイト単位のサイズ

        Returns:
            str: 変換後のサイズ文字列
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}PB"

    def update_progress(self, value: int, message: str) -> None:
        """プログレスバーとステータスメッセージを更新する

        Args:
            value (int): 進捗値（0-100）
            message (str): 表示するメッセージ
        """
        if self.window:
            self.window["-PROGRESS-"].update(value)
            self.window["-STATUS-"].update(value=message)

    def show_error(self, message: str) -> None:
        """エラーメッセージを表示する

        Args:
            message (str): エラーメッセージ
        """
        sg.popup_error(f"エラー: {message}", title="エラー")

    def show_help(self) -> None:
        """ヘルプ情報を表示する"""
        help_text = """
データサルベージプログラムのヘルプ

1. ディスクの選択
   - 検出されたディスク一覧から対象のディスクを選択してください
   - マウントボタンをクリックしてディスクをマウントします

2. ファイルの選択
   - ファイル一覧から復旧したいファイルを選択してください
   - 「選択」または「すべて選択」ボタンで選択できます

3. コピー先の指定
   - 「参照」ボタンをクリックして保存先を指定してください
   - 十分な空き容量があることを確認してください

4. コピーの実行
   - 「コピー開始」ボタンをクリックしてコピーを開始します
   - プログレスバーで進捗状況を確認できます

注意事項:
- 破損マークのついたファイルは、正常にコピーできない可能性があります
- コピー中はプログラムを終了しないでください
- エラーが発生した場合は、エラーメッセージを確認してください
"""
        sg.popup_scrolled(
            help_text,
            title="ヘルプ",
            size=(60, 20),
        )

    def display_disk_status(self, status: FilesystemStatus) -> None:
        """ディスクの状態を表示する

        Args:
            status (FilesystemStatus): ディスクの状態情報
        """
        if self.window:
            status_text = (
                "正常" if status.is_consistent else f"問題あり: {status.details}"
            )
            self.window["-DISK_STATUS-"].update(status_text)

    def close(self) -> None:
        """ウィンドウを閉じる"""
        if self.window:
            self.window.close()
