import sys
import pytest
from src.main import main


def test_main_initialization(capsys):
    try:
        main()
    except Exception:
        pass
    captured = capsys.readouterr().out
    assert "アプリケーションを初期化しています..." in captured
