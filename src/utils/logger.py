"""
JSDoc: ユーティリティモジュール - ログ機能
概要: 本ファイルは、操作履歴やエラー情報のログ記録、ログファイルへの保存、及び操作履歴のエクスポートを行うLoggerクラスを提供します。
仕様: Python (PEP8準拠、type hint使用)
制限: Linux環境（LubuntuまたはUbuntuベース）での動作を前提とする
"""

from typing import Optional
import datetime


class Logger:
    """
    ログ管理を行うクラス

    Methods:
        log_info(message: str) -> None: 情報ログの記録
        log_error(message: str) -> None: エラーログの記録
        log_warning(message: str) -> None: 警告ログの記録
        save_logs(path: str) -> bool: ログファイル保存
        export_operation_history() -> str: 操作履歴のエクスポート
    """

    def __init__(self) -> None:
        self.logs = []

    def log_info(self, message: str) -> None:
        """情報ログを記録する

        Args:
            message (str): 記録するメッセージ
        """
        log_entry = f"INFO [{datetime.datetime.now()}]: {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def log_error(self, message: str) -> None:
        """エラーログを記録する

        Args:
            message (str): 記録するエラーメッセージ
        """
        log_entry = f"ERROR [{datetime.datetime.now()}]: {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def log_warning(self, message: str) -> None:
        """警告ログを記録する

        Args:
            message (str): 記録する警告メッセージ
        """
        log_entry = f"WARNING [{datetime.datetime.now()}]: {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def save_logs(self, path: str) -> bool:
        """ログファイルを指定のパスに保存する

        Args:
            path (str): 保存先のファイルパス

        Returns:
            bool: 保存に成功したかどうか
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                for entry in self.logs:
                    f.write(entry + "\n")
            return True
        except Exception as e:
            self.log_error(f"ログの保存に失敗しました: {e}")
            return False

    def export_operation_history(self) -> str:
        """操作履歴をエクスポートする

        Returns:
            str: エクスポートされた操作履歴
        """
        # TODO: 必要に応じて操作履歴の形式を整形して返す
        return "\n".join(self.logs)
