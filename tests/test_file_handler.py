import os
import pytest
from src.file_operations.file_handler import (
    FileHandler,
    File,
    FileAttributes,
    FileError,
)


@pytest.mark.linux_only
def test_list_files(capsys, tmp_path):
    """ファイル一覧取得のテスト（Linux環境専用）"""
    fh = FileHandler()
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # テスト用のダミーファイルを作成
    (test_dir / "file1.txt").write_text("テストファイル1")
    (test_dir / "file2.txt").write_text("テストファイル2")

    files = fh.list_files(str(test_dir))

    assert len(files) == 2
    assert any(f.path.endswith("file1.txt") for f in files)
    assert any(f.path.endswith("file2.txt") for f in files)


@pytest.mark.linux_only
def test_list_files_error(capsys, tmp_path):
    """ファイル一覧取得エラーのテスト（Linux環境専用）"""
    fh = FileHandler()
    non_existent_dir = tmp_path / "non_existent"

    with pytest.raises(FileNotFoundError):
        fh.list_files(str(non_existent_dir))

    captured = capsys.readouterr()
    assert "エラー" in captured.out


@pytest.mark.linux_only
def test_copy_files(tmp_path):
    """ファイルコピーのテスト（Linux環境専用）"""
    fh = FileHandler()
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    source_dir.mkdir()
    dest_dir.mkdir()

    # テスト用のダミーファイルを作成
    source_file = source_dir / "test.txt"
    source_file.write_text("テストデータ")

    test_file = File(
        path=str(source_file),
        size=len("テストデータ"),
        attributes=None,
        status="正常",
        is_corrupted=False,
    )

    assert fh.copy_files([test_file], str(dest_dir)) is True
    assert (dest_dir / "test.txt").exists()
    assert (dest_dir / "test.txt").read_text() == "テストデータ"


@pytest.mark.linux_only
def test_copy_files_error(tmp_path):
    """ファイルコピーエラーのテスト（Linux環境専用）"""
    fh = FileHandler()
    source_dir = tmp_path / "source"
    non_existent_dir = tmp_path / "non_existent"
    source_dir.mkdir()

    # テスト用のダミーファイルを作成
    source_file = source_dir / "test.txt"
    source_file.write_text("テストデータ")

    test_file = File(
        path=str(source_file),
        size=len("テストデータ"),
        attributes=None,
        status="正常",
        is_corrupted=False,
    )

    assert fh.copy_files([test_file], str(non_existent_dir)) is False


@pytest.mark.linux_only
def test_verify_copy(capsys, tmp_path):
    """コピー検証のテスト（Linux環境専用）"""
    fh = FileHandler()
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    source_dir.mkdir()
    dest_dir.mkdir()

    # テスト用のダミーファイルを作成
    source_file = source_dir / "test.txt"
    source_file.write_text("テストデータ")
    dest_file = dest_dir / "test.txt"
    dest_file.write_text("テストデータ")

    assert fh.verify_copy(str(source_file), str(dest_file)) is True


@pytest.mark.linux_only
def test_verify_copy_error(capsys, tmp_path):
    """コピー検証エラーのテスト（Linux環境専用）"""
    fh = FileHandler()
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    source_dir.mkdir()
    dest_dir.mkdir()

    # テスト用のダミーファイルを作成（内容が異なる）
    source_file = source_dir / "test.txt"
    source_file.write_text("テストデータ1")
    dest_file = dest_dir / "test.txt"
    dest_file.write_text("テストデータ2")

    assert fh.verify_copy(str(source_file), str(dest_file)) is False


@pytest.mark.linux_only
def test_get_file_attributes(capsys, tmp_path):
    """ファイル属性取得のテスト（Linux環境専用）"""
    fh = FileHandler()
    test_file = tmp_path / "test.txt"
    test_file.write_text("テストデータ")

    test_file_obj = File(
        path=str(test_file),
        size=len("テストデータ"),
        attributes=None,
        status="正常",
        is_corrupted=False,
    )

    attrs = fh.get_file_attributes(test_file_obj)

    assert isinstance(attrs, FileAttributes)
    assert attrs.creation_time is not None
    assert attrs.modified_time is not None
    assert attrs.permissions is not None
    assert attrs.owner is not None
    assert isinstance(attrs.is_hidden, bool)


@pytest.mark.linux_only
def test_get_file_attributes_error(capsys, tmp_path):
    """ファイル属性取得エラーのテスト（Linux環境専用）"""
    fh = FileHandler()
    non_existent_file = tmp_path / "non_existent.txt"

    test_file_obj = File(
        path=str(non_existent_file),
        size=0,
        attributes=None,
        status="エラー",
        is_corrupted=False,
    )

    with pytest.raises(FileNotFoundError):
        fh.get_file_attributes(test_file_obj)

    captured = capsys.readouterr()
    assert "エラー" in captured.out


@pytest.mark.linux_only
def test_check_file_accessibility(capsys, tmp_path):
    """ファイルアクセス確認のテスト（Linux環境専用）"""
    fh = FileHandler()
    test_file = tmp_path / "test.txt"
    test_file.write_text("テストデータ")

    test_file_obj = File(
        path=str(test_file),
        size=len("テストデータ"),
        attributes=None,
        status="正常",
        is_corrupted=False,
    )

    assert fh.check_file_accessibility(test_file_obj) is True


@pytest.mark.linux_only
def test_check_file_accessibility_error(capsys, tmp_path):
    """ファイルアクセス確認エラーのテスト（Linux環境専用）"""
    fh = FileHandler()
    non_existent_file = tmp_path / "non_existent.txt"

    test_file_obj = File(
        path=str(non_existent_file),
        size=0,
        attributes=None,
        status="エラー",
        is_corrupted=False,
    )

    assert fh.check_file_accessibility(test_file_obj) is False

    captured = capsys.readouterr()
    assert "エラー" in captured.out


@pytest.mark.linux_only
def test_handle_corrupted_files(capsys, tmp_path):
    """破損ファイル処理のテスト（Linux環境専用）"""
    fh = FileHandler()
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # テスト用の破損ファイルを作成
    corrupted_file = test_dir / "corrupted.txt"
    corrupted_file.write_text("破損データ")

    test_file_obj = File(
        path=str(corrupted_file),
        size=len("破損データ"),
        attributes=None,
        status="破損",
        is_corrupted=True,
    )

    errors = fh.handle_corrupted_files([test_file_obj])

    assert len(errors) == 1
    assert isinstance(errors[0], FileError)
    assert errors[0].error_code == 6  # FILE_006
    assert "破損" in errors[0].message


@pytest.mark.linux_only
def test_handle_corrupted_files_multiple(capsys, tmp_path):
    """複数の破損ファイル処理のテスト（Linux環境専用）"""
    fh = FileHandler()
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # テスト用の破損ファイルを複数作成
    files = []
    for i in range(3):
        corrupted_file = test_dir / f"corrupted{i}.txt"
        corrupted_file.write_text(f"破損データ{i}")
        files.append(
            File(
                path=str(corrupted_file),
                size=len(f"破損データ{i}"),
                attributes=None,
                status="破損",
                is_corrupted=True,
            )
        )

    errors = fh.handle_corrupted_files(files)

    assert len(errors) == 3
    for error in errors:
        assert isinstance(error, FileError)
        assert error.error_code == 6  # FILE_006
        assert "破損" in error.message
