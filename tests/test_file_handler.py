import os
import pytest
from src.file_operations.file_handler import (
    FileHandler,
    File,
    FileAttributes,
    FileError,
)


def test_list_files(capsys, tmp_path):
    """ファイル一覧取得のテスト"""
    fh = FileHandler()
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # テスト用のダミーファイルを作成
    (test_dir / "file1.txt").write_text("テストファイル1")
    (test_dir / "file2.txt").write_text("テストファイル2")

    files = fh.list_files(str(test_dir))
    captured = capsys.readouterr().out

    assert f"{test_dir} のファイル一覧を取得中..." in captured
    assert isinstance(files, list)


def test_copy_files(tmp_path):
    """ファイルコピーのテスト"""
    fh = FileHandler()
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()

    # テスト用のダミーファイルを作成
    source_file = source_dir / "test_file.txt"
    source_file.write_text("コピーテスト")

    test_file = File(
        path=str(source_file),
        size=len("コピーテスト"),
        attributes=None,
        status="normal",
        is_corrupted=False,
    )

    result = fh.copy_files([test_file], str(dest_dir))

    assert any(
        f"{str(dest_dir)} へのファイルコピーが完了しました" in entry
        for entry in fh.logger.logs
    )
    assert result is True
    assert os.path.exists(os.path.join(str(dest_dir), "test_file.txt"))


def test_verify_copy(capsys, tmp_path):
    """コピー検証のテスト"""
    fh = FileHandler()
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()

    source_file = source_dir / "test_file.txt"
    source_file.write_text("検証テスト")
    dest_file = dest_dir / "test_file.txt"
    dest_file.write_text("検証テスト")

    result = fh.verify_copy(str(source_file), str(dest_file))
    captured = capsys.readouterr().out

    assert f"{source_file} から {dest_file} へのコピー検証を実施中..." in captured
    assert result is True


def test_get_file_attributes(capsys, tmp_path):
    """ファイル属性取得のテスト"""
    fh = FileHandler()
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("属性テスト")

    file_obj = File(
        path=str(test_file),
        size=len("属性テスト"),
        attributes=None,
        status="normal",
        is_corrupted=False,
    )

    attributes = fh.get_file_attributes(file_obj)
    captured = capsys.readouterr().out

    assert f"{test_file} の属性を取得中..." in captured
    assert isinstance(attributes, FileAttributes)


def test_check_file_accessibility(capsys, tmp_path):
    """ファイルアクセス可能性のテスト"""
    fh = FileHandler()
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("アクセステスト")

    file_obj = File(
        path=str(test_file),
        size=len("アクセステスト"),
        attributes=None,
        status="normal",
        is_corrupted=False,
    )

    result = fh.check_file_accessibility(file_obj)
    captured = capsys.readouterr().out

    assert f"{test_file} のアクセス性を確認中..." in captured
    assert result is True


def test_handle_corrupted_files(capsys, tmp_path):
    """破損ファイルハンドリングのテスト"""
    fh = FileHandler()
    test_file = tmp_path / "corrupted_file.txt"
    test_file.write_text("破損ファイルテスト")

    file_obj = File(
        path=str(test_file),
        size=len("破損ファイルテスト"),
        attributes=None,
        status="corrupted",
        is_corrupted=True,
    )

    errors = fh.handle_corrupted_files([file_obj])
    captured = capsys.readouterr().out

    assert "破損ファイルのチェックを実施中..." in captured
    assert isinstance(errors, list)
