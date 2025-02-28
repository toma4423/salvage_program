"""テスト設定モジュール"""

import sys
import pytest


def pytest_runtest_setup(item):
    """テスト実行前の環境チェック"""
    for marker in item.iter_markers():
        if marker.name == "linux_only" and sys.platform != "linux":
            pytest.skip("このテストはLinux環境でのみ実行されます")
        elif marker.name == "windows_only" and sys.platform != "win32":
            pytest.skip("このテストはWindows環境でのみ実行されます")
