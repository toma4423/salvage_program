"""
JSDoc: ファイル操作モジュール
概要: 本ファイルは、ファイルとディレクトリの一覧取得、コピー、検証、属性確認、破損ファイルの検出・ハンドリングを行うFileHandlerクラスを提供します。
仕様: Python (PEP8準拠、type hint使用)
制限: Linux環境（LubuntuまたはUbuntuベース）での動作を前提とする
"""

import os
import shutil
from typing import List, Any
from ..utils.logger import Logger
from datetime import datetime


class File:
    """ファイル情報を表すクラス

    Attributes:
        path (str): ファイルパス
        size (int): ファイルサイズ
        attributes (Any): ファイル属性（詳細はFileAttributes参照）
        status (str): ファイルの状態
        is_corrupted (bool): 破損状態
    """

    def __init__(
        self, path: str, size: int, attributes: Any, status: str, is_corrupted: bool
    ) -> None:
        self.path = path
        self.size = size
        self.attributes = attributes
        self.status = status
        self.is_corrupted = is_corrupted


class FileAttributes:
    """ファイルの属性を表すクラス

    Attributes:
        creation_time (str): 作成日時
        modified_time (str): 更新日時
        permissions (str): ファイルパーミッション
        owner (str): 所有者
        is_hidden (bool): 隠しファイルかどうか
    """

    def __init__(
        self,
        creation_time: str,
        modified_time: str,
        permissions: str,
        owner: str,
        is_hidden: bool,
    ) -> None:
        self.creation_time = creation_time
        self.modified_time = modified_time
        self.permissions = permissions
        self.owner = owner
        self.is_hidden = is_hidden


class FileError:
    """ファイルエラー情報を表すクラス

    Attributes:
        error_code (int): エラーコード
        message (str): エラーメッセージ
    """

    def __init__(self, error_code: int, message: str) -> None:
        self.error_code = error_code
        self.message = message


# エラーコードの定義
FILE_001 = 1
FILE_002 = 2
FILE_003 = 3
FILE_004 = 4
FILE_005 = 5
FILE_006 = 6


class FileHandler:
    """ファイル操作を管理するクラス

    Methods:
        list_files(path: str) -> List[File]
        copy_files(files: List[File], destination: str) -> bool
        verify_copy(source: str, destination: str) -> bool
        get_file_attributes(file: File) -> FileAttributes
        check_file_accessibility(file: File) -> bool
        handle_corrupted_files(files: List[File]) -> List[FileError]
    """

    def __init__(self):
        self.logger = Logger()

    def list_files(self, path: str) -> List[File]:
        """
        指定されたパスのファイル・ディレクトリ一覧を取得する

        Args:
            path (str): 対象パス

        Returns:
            List[File]: ファイル情報の一覧
        """
        files = []
        try:
            self.logger.log_info(f"{path} のファイル一覧を取得中...")

            # パスの存在確認
            if not os.path.exists(path):
                raise FileNotFoundError(f"指定されたパス {path} が見つかりません")

            # ファイル一覧を再帰的に取得
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        # ファイルの基本情報を取得
                        file_size = os.path.getsize(file_path)

                        # Fileオブジェクトを作成
                        file = File(
                            path=file_path,
                            size=file_size,
                            attributes=None,  # 属性は後で取得
                            status="normal",
                            is_corrupted=False,
                        )
                        files.append(file)

                    except OSError as e:
                        self.logger.log_warning(
                            f"ファイル {file_path} の情報取得に失敗: {e}"
                        )
                        continue

            self.logger.log_info(f"{len(files)} 個のファイルを検出しました")
            return files

        except Exception as e:
            self.logger.log_error(f"ファイル一覧の取得に失敗しました: {e}")
            self.logger.log_error(f"エラーコード: FILE_001")
            self.logger.log_error(f"パス: {path}")
            return []

    def copy_files(self, files: List[File], destination: str) -> bool:
        """
        指定されたファイルを指定先にコピーする

        Args:
            files (List[File]): コピー対象のファイルリスト
            destination (str): コピー先パス

        Returns:
            bool: コピー成功の有無
        """
        try:
            for file in files:
                # ファイル名を取得
                filename = os.path.basename(file.path)
                dest_path = os.path.join(destination, filename)

                # ファイルをコピー
                shutil.copy2(file.path, dest_path)
            self.logger.log_info(f"{destination} へのファイルコピーが完了しました")
            return True
        except Exception as e:
            self.logger.log_error(f"ファイルコピー中にエラーが発生しました: {e}")
            self.logger.log_error(f"エラーコード: FILE_002")
            self.logger.log_error(f"コピー元: {[file.path for file in files]}")
            self.logger.log_error(f"コピー先: {destination}")
            return False

    def verify_copy(self, source: str, destination: str) -> bool:
        """
        コピーされたファイルの検証を行う

        Args:
            source (str): コピー元パス
            destination (str): コピー先パス

        Returns:
            bool: コピー検証結果
        """
        try:
            self.logger.log_info(
                f"{source} から {destination} へのコピー検証を実施中..."
            )

            # ファイルの存在確認
            if not os.path.exists(source):
                raise FileNotFoundError(f"コピー元ファイル {source} が見つかりません")
            if not os.path.exists(destination):
                raise FileNotFoundError(
                    f"コピー先ファイル {destination} が見つかりません"
                )

            # ファイルサイズの比較
            source_size = os.path.getsize(source)
            dest_size = os.path.getsize(destination)

            if source_size != dest_size:
                self.logger.log_error(f"ファイルサイズが一致しません")
                self.logger.log_error(f"コピー元: {source_size} bytes")
                self.logger.log_error(f"コピー先: {dest_size} bytes")
                return False

            # ファイルのハッシュ値を計算して比較
            import hashlib

            def calculate_md5(file_path: str) -> str:
                md5_hash = hashlib.md5()
                with open(file_path, "rb") as f:
                    # ファイルを1MBずつ読み込んでハッシュ値を計算
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        md5_hash.update(chunk)
                return md5_hash.hexdigest()

            source_hash = calculate_md5(source)
            dest_hash = calculate_md5(destination)

            if source_hash != dest_hash:
                self.logger.log_error(f"ファイルのハッシュ値が一致しません")
                self.logger.log_error(f"コピー元: {source_hash}")
                self.logger.log_error(f"コピー先: {dest_hash}")
                return False

            self.logger.log_info(f"ファイルの検証が完了しました")
            return True

        except Exception as e:
            self.logger.log_error(f"コピー検証に失敗しました: {e}")
            self.logger.log_error(f"エラーコード: FILE_003")
            self.logger.log_error(f"コピー元: {source}")
            self.logger.log_error(f"コピー先: {destination}")
            return False

    def get_file_attributes(self, file: File) -> FileAttributes:
        """
        ファイルの属性情報を取得する

        Args:
            file (File): 対象ファイル

        Returns:
            FileAttributes: 取得された属性情報
        """
        try:
            self.logger.log_info(f"{file.path} の属性を取得中...")

            # ファイルの存在確認
            if not os.path.exists(file.path):
                raise FileNotFoundError(f"ファイル {file.path} が見つかりません")

            # ファイルの作成日時と更新日時を取得
            stat_info = os.stat(file.path)
            creation_time = datetime.fromtimestamp(stat_info.st_ctime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ファイルのパーミッションを8進数で取得
            permissions = oct(stat_info.st_mode & 0o777)

            # ファイルの所有者を取得
            try:
                import pwd

                owner = pwd.getpwuid(stat_info.st_uid).pw_name
            except ImportError:
                # Windowsの場合はimport pwdが失敗するため
                import getpass

                owner = getpass.getuser()

            # 隠しファイルかどうかを判定
            is_hidden = os.path.basename(file.path).startswith(".")
            if os.name == "nt":  # Windowsの場合
                import ctypes

                try:
                    attrs = ctypes.windll.kernel32.GetFileAttributesW(file.path)
                    is_hidden = bool(attrs & 2)  # FILE_ATTRIBUTE_HIDDEN
                except AttributeError:
                    pass

            attributes = FileAttributes(
                creation_time=creation_time,
                modified_time=modified_time,
                permissions=permissions,
                owner=owner,
                is_hidden=is_hidden,
            )

            self.logger.log_info(f"ファイル属性の取得が完了しました")
            return attributes

        except Exception as e:
            self.logger.log_error(f"ファイル属性の取得に失敗しました: {e}")
            self.logger.log_error(f"エラーコード: FILE_004")
            self.logger.log_error(f"ファイル: {file.path}")
            return FileAttributes("不明", "不明", "不明", "不明", False)

    def check_file_accessibility(self, file: File) -> bool:
        """
        ファイルのアクセス可能性を確認する

        Args:
            file (File): 対象ファイル

        Returns:
            bool: アクセス可能かどうか
        """
        try:
            self.logger.log_info(f"{file.path} のアクセス性を確認中...")

            # ファイルの存在確認
            if not os.path.exists(file.path):
                raise FileNotFoundError(f"ファイル {file.path} が見つかりません")

            # 読み取り権限の確認
            if not os.access(file.path, os.R_OK):
                self.logger.log_error(
                    f"ファイル {file.path} に読み取り権限がありません"
                )
                return False

            # ファイルのロック状態を確認
            try:
                with open(file.path, "rb") as f:
                    # ファイルをロックしてみる
                    import msvcrt

                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except (IOError, PermissionError):
                        self.logger.log_error(
                            f"ファイル {file.path} は他のプロセスによってロックされています"
                        )
                        return False
            except ImportError:
                # Windowsでない場合はfcntlを使用
                try:
                    import fcntl

                    with open(file.path, "rb") as f:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (ImportError, IOError):
                    self.logger.log_error(
                        f"ファイル {file.path} は他のプロセスによってロックされています"
                    )
                    return False

            self.logger.log_info(f"ファイル {file.path} はアクセス可能です")
            return True

        except Exception as e:
            self.logger.log_error(f"ファイルアクセス確認に失敗しました: {e}")
            self.logger.log_error(f"エラーコード: FILE_005")
            self.logger.log_error(f"ファイル: {file.path}")
            return False

    def handle_corrupted_files(self, files: List[File]) -> List[FileError]:
        """
        破損ファイルのハンドリングを行う

        Args:
            files (List[File]): チェック対象のファイルリスト

        Returns:
            List[FileError]: 発見されたエラー情報のリスト
        """
        errors = []
        try:
            self.logger.log_info("破損ファイルのチェックを実施中...")

            for file in files:
                try:
                    # ファイルの存在確認
                    if not os.path.exists(file.path):
                        raise FileNotFoundError(
                            f"ファイル {file.path} が見つかりません"
                        )

                    # ファイルが空でないことを確認
                    if os.path.getsize(file.path) == 0:
                        error = FileError(
                            FILE_006, f"ファイル {file.path} は空ファイルです"
                        )
                        errors.append(error)
                        file.is_corrupted = True
                        continue

                    # ファイルヘッダーの確認
                    with open(file.path, "rb") as f:
                        header = f.read(8)  # 最初の8バイトを読み込む

                    # 一般的なファイル形式のマジックナンバーをチェック
                    magic_numbers = {
                        b"\x89PNG\r\n\x1a\n": "PNG",
                        b"\xFF\xD8\xFF": "JPEG",
                        b"GIF87a": "GIF",
                        b"GIF89a": "GIF",
                        b"%PDF": "PDF",
                        b"PK\x03\x04": "ZIP",
                        b"\x50\x4B\x05\x06": "ZIP",
                        b"\x50\x4B\x07\x08": "ZIP",
                    }

                    file_type = None
                    for magic, ftype in magic_numbers.items():
                        if header.startswith(magic):
                            file_type = ftype
                            break

                    # ファイル拡張子とヘッダーの整合性チェック
                    if file_type:
                        ext = os.path.splitext(file.path)[1].lower()
                        expected_extensions = {
                            "PNG": ".png",
                            "JPEG": [".jpg", ".jpeg"],
                            "GIF": ".gif",
                            "PDF": ".pdf",
                            "ZIP": ".zip",
                        }

                        if file_type in expected_extensions:
                            expected = expected_extensions[file_type]
                            if isinstance(expected, list):
                                if ext not in expected:
                                    error = FileError(
                                        FILE_006,
                                        f"ファイル {file.path} の拡張子が不正です（期待: {expected}, 実際: {ext}）",
                                    )
                                    errors.append(error)
                                    file.is_corrupted = True
                            else:
                                if ext != expected:
                                    error = FileError(
                                        FILE_006,
                                        f"ファイル {file.path} の拡張子が不正です（期待: {expected}, 実際: {ext}）",
                                    )
                                    errors.append(error)
                                    file.is_corrupted = True

                    # ファイルの整合性チェック
                    try:
                        with open(file.path, "rb") as f:
                            while True:
                                chunk = f.read(1024 * 1024)  # 1MBずつ読み込む
                                if not chunk:
                                    break
                    except (IOError, OSError) as e:
                        error = FileError(
                            FILE_006,
                            f"ファイル {file.path} の読み込み中にエラーが発生しました: {e}",
                        )
                        errors.append(error)
                        file.is_corrupted = True

                except Exception as e:
                    error = FileError(
                        FILE_006,
                        f"ファイル {file.path} のチェック中にエラーが発生しました: {e}",
                    )
                    errors.append(error)
                    file.is_corrupted = True

            self.logger.log_info(
                f"破損ファイルのチェックが完了しました（検出: {len(errors)}件）"
            )
            return errors

        except Exception as e:
            self.logger.log_error(
                f"破損ファイルのチェック中にエラーが発生しました: {e}"
            )
            self.logger.log_error(f"エラーコード: FILE_006")
            errors.append(FileError(FILE_006, str(e)))
            return errors
