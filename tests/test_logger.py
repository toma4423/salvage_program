import os
import pytest
from src.utils.logger import Logger


def test_log_info(capsys):
    """情報ログの記録テスト"""
    logger = Logger()
    test_message = "テスト情報メッセージ"

    logger.log_info(test_message)
    captured = capsys.readouterr().out

    assert "INFO" in captured
    assert test_message in captured
    assert len(logger.logs) > 0
    assert logger.logs[0].startswith("INFO")


def test_log_error(capsys):
    """エラーログの記録テスト"""
    logger = Logger()
    test_message = "テストエラーメッセージ"

    logger.log_error(test_message)
    captured = capsys.readouterr().out

    assert "ERROR" in captured
    assert test_message in captured
    assert len(logger.logs) > 0
    assert logger.logs[0].startswith("ERROR")


def test_log_warning(capsys):
    """警告ログの記録テスト"""
    logger = Logger()
    test_message = "テスト警告メッセージ"

    logger.log_warning(test_message)
    captured = capsys.readouterr().out

    assert "WARNING" in captured
    assert test_message in captured
    assert len(logger.logs) > 0
    assert logger.logs[0].startswith("WARNING")


def test_save_logs(tmp_path):
    """ログの保存テスト"""
    logger = Logger()
    logger.log_info("テスト情報1")
    logger.log_error("テストエラー1")

    log_file = tmp_path / "test_log.txt"
    result = logger.save_logs(str(log_file))

    assert result is True
    assert os.path.exists(log_file)

    with open(log_file, "r", encoding="utf-8") as f:
        log_contents = f.read()
        assert "テスト情報1" in log_contents
        assert "テストエラー1" in log_contents


def test_save_logs_failure(tmp_path):
    """ログ保存失敗のテスト"""
    logger = Logger()
    logger.log_info("テスト情報2")

    # 書き込み権限のないディレクトリを指定
    invalid_path = tmp_path / "non_existent_dir" / "log.txt"

    result = logger.save_logs(str(invalid_path))

    assert result is False


def test_export_operation_history():
    """操作履歴のエクスポートテスト"""
    logger = Logger()
    logger.log_info("テスト情報3")
    logger.log_error("テストエラー3")

    history = logger.export_operation_history()

    assert isinstance(history, str)
    assert "テスト情報3" in history
    assert "テストエラー3" in history
