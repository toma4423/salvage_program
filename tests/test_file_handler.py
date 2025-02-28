"""
FileHandlerクラスのテストモジュール

このモジュールは、ファイル操作の機能をテストします。
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import hashlib
from src.file_operations.file_handler import (
    FileHandler,
    File,
    FileAttributes,
    FileError,
)


@pytest.fixture
def file_handler():
    """FileHandlerのフィクスチャ"""
    return FileHandler()


@pytest.fixture
def test_file(tmp_path):
    """テストファイルのフィクスチャ"""
    test_file = tmp_path / "test.txt"
    test_data = "テストデータ"
    test_file.write_text(test_data)
    return {
        "path": test_file,
        "data": test_data,
        "size": len(test_data.encode()),
        "hash": hashlib.md5(test_data.encode()).hexdigest(),
    }


@pytest.fixture
def test_file_obj(test_file):
    """テストファイルオブジェクトのフィクスチャ"""
    return File(
        path=str(test_file["path"]),
        size=test_file["size"],
        hash=test_file["hash"],
        status="正常",
        is_corrupted=False,
    )


@pytest.mark.linux_only
@patch("os.walk")
def test_list_files(mock_walk, file_handler, tmp_path):
    """ファイル一覧取得のテスト（Linux環境専用）"""
    mock_walk.return_value = [
        (str(tmp_path), ["dir1"], ["file1.txt", "file2.txt"]),
        (str(tmp_path / "dir1"), [], ["file3.txt"]),
    ]

    with patch("os.path.getsize") as mock_size, patch(
        "os.path.isfile"
    ) as mock_isfile, patch("hashlib.md5") as mock_md5:
        mock_size.return_value = 1000
        mock_isfile.return_value = True
        mock_md5.return_value.hexdigest.return_value = "test_hash"

        files = file_handler.list_files(str(tmp_path))

        assert len(files) == 3
        assert all(isinstance(f, File) for f in files)
        assert all(f.size == 1000 for f in files)
        assert all(f.hash == "test_hash" for f in files)
        assert all(not f.is_corrupted for f in files)


@pytest.mark.linux_only
@patch("os.walk")
def test_list_files_error(mock_walk, file_handler, tmp_path):
    """ファイル一覧取得エラーのテスト（Linux環境専用）"""
    mock_walk.side_effect = OSError("アクセス拒否")

    with pytest.raises(FileNotFoundError):
        file_handler.list_files(str(tmp_path))


@pytest.mark.linux_only
@patch("shutil.copy2")
@patch("os.path.exists")
@patch("os.makedirs")
def test_copy_files(
    mock_makedirs, mock_exists, mock_copy, file_handler, test_file_obj, tmp_path
):
    """ファイルコピーのテスト（Linux環境専用）"""
    dest_dir = tmp_path / "dest"
    mock_exists.return_value = False

    assert file_handler.copy_files([test_file_obj], str(dest_dir)) is True
    mock_makedirs.assert_called_once_with(str(dest_dir), exist_ok=True)
    mock_copy.assert_called_once()


@pytest.mark.linux_only
@patch("shutil.copy2")
def test_copy_files_error(mock_copy, file_handler, test_file_obj, tmp_path):
    """ファイルコピーエラーのテスト（Linux環境専用）"""
    mock_copy.side_effect = IOError("コピーエラー")
    assert file_handler.copy_files([test_file_obj], str(tmp_path)) is False


@pytest.mark.linux_only
@patch("hashlib.md5")
def test_verify_copy(mock_md5, file_handler, test_file):
    """コピー検証のテスト（Linux環境専用）"""
    mock_md5.return_value.hexdigest.return_value = test_file["hash"]
    assert (
        file_handler.verify_copy(str(test_file["path"]), str(test_file["path"])) is True
    )


@pytest.mark.linux_only
@patch("hashlib.md5")
def test_verify_copy_error(mock_md5, file_handler, test_file, tmp_path):
    """コピー検証エラーのテスト（Linux環境専用）"""
    mock_md5.return_value.hexdigest.side_effect = ["hash1", "hash2"]
    assert (
        file_handler.verify_copy(str(test_file["path"]), str(tmp_path / "dest.txt"))
        is False
    )


@pytest.mark.linux_only
@patch("os.stat")
def test_get_file_attributes(mock_stat, file_handler, test_file_obj):
    """ファイル属性取得のテスト（Linux環境専用）"""
    mock_stat_result = MagicMock()
    mock_stat_result.st_mode = 0o644
    mock_stat_result.st_uid = 1000
    mock_stat_result.st_gid = 1000
    mock_stat_result.st_ctime = 1000000000
    mock_stat_result.st_mtime = 1000000000
    mock_stat.return_value = mock_stat_result

    attrs = file_handler.get_file_attributes(test_file_obj)

    assert isinstance(attrs, FileAttributes)
    assert attrs.permissions == "644"
    assert attrs.owner == "1000:1000"
    assert attrs.creation_time is not None
    assert attrs.modified_time is not None


@pytest.mark.linux_only
def test_get_file_attributes_error(file_handler, tmp_path):
    """ファイル属性取得エラーのテスト（Linux環境専用）"""
    non_existent_file = File(
        path=str(tmp_path / "non_existent.txt"),
        size=0,
        hash=None,
        status="エラー",
        is_corrupted=False,
    )

    with pytest.raises(FileNotFoundError):
        file_handler.get_file_attributes(non_existent_file)


@pytest.mark.linux_only
@patch("os.access")
@pytest.mark.parametrize(
    "permissions",
    [
        (True, True, True),  # 読み取り、書き込み、実行可能
        (True, False, False),  # 読み取りのみ
        (False, False, False),  # アクセス不可
    ],
)
def test_check_file_accessibility(
    mock_access, permissions, file_handler, test_file_obj
):
    """ファイルアクセス確認のテスト（Linux環境専用）"""
    mock_access.side_effect = permissions
    expected = all(permissions)
    assert file_handler.check_file_accessibility(test_file_obj) is expected


@pytest.mark.linux_only
def test_handle_corrupted_files(file_handler, tmp_path):
    """破損ファイル処理のテスト（Linux環境専用）"""
    corrupted_files = [
        File(
            path=str(tmp_path / "corrupted1.txt"),
            size=100,
            hash="invalid_hash",
            status="破損",
            is_corrupted=True,
        ),
        File(
            path=str(tmp_path / "normal.txt"),
            size=100,
            hash="valid_hash",
            status="正常",
            is_corrupted=False,
        ),
    ]

    errors = file_handler.handle_corrupted_files(corrupted_files)

    assert len(errors) == 1
    assert isinstance(errors[0], FileError)
    assert errors[0].error_code == 6  # FILE_006
    assert "破損" in errors[0].message


@pytest.mark.linux_only
@pytest.mark.parametrize("num_corrupted", [1, 3, 5])
def test_handle_corrupted_files_multiple(file_handler, tmp_path, num_corrupted):
    """複数の破損ファイル処理のテスト（Linux環境専用）"""
    corrupted_files = []
    for i in range(num_corrupted):
        corrupted_files.append(
            File(
                path=str(tmp_path / f"corrupted{i}.txt"),
                size=100,
                hash=f"invalid_hash_{i}",
                status="破損",
                is_corrupted=True,
            )
        )

    errors = file_handler.handle_corrupted_files(corrupted_files)

    assert len(errors) == num_corrupted
    assert all(isinstance(e, FileError) for e in errors)
    assert all(e.error_code == 6 for e in errors)  # FILE_006
    assert all("破損" in e.message for e in errors)
