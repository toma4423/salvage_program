# データサルベージプログラム

## 概要
WindowsPCが起動しない状態においても、USBブート可能なLinuxOS（Lubuntu）上で、内蔵HDD/SSDからデータを安全かつ効率的にサルベージ（復旧）するためのデスクトップアプリケーションです。

## 主な機能
- 内蔵HDD/SSDの自動検出とマウント
- ファイルシステムの整合性チェック
- データの安全なコピーと検証
- 破損ファイルの検出とハンドリング
- 直感的なGUIインターフェース
- 詳細なログ記録

## 技術スタック
- Python 3.11以上
- PySimpleGUI（GUIフレームワーク）
- pytest（テストフレームワーク）

## インストール方法

### 必要条件
- Python 3.11以上
- pip（Pythonパッケージマネージャー）
- Linux環境（実行時）：
  - fsck.ext4
  - ntfs-3g
  - smartmontools

### セットアップ手順
1. リポジトリをクローン
```bash
git clone [リポジトリURL]
cd salvage_program
```

2. 仮想環境を作成して有効化
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

## 使用方法
1. プログラムを起動
```bash
python src/main.py
```

2. GUIウィンドウが表示されたら、内蔵ディスクが自動的に検出されます
3. 検出されたディスクを選択し、マウントを実行
4. ファイルシステムの整合性チェックを実行
5. 復旧したいファイル/ディレクトリを選択
6. 保存先を指定して、データのコピーを開始

## プロジェクト構造
```
salvage_program/
├── src/
│   ├── main.py                 # メインエントリーポイント
│   ├── disk_operations/        # ディスク操作モジュール
│   │   └── disk_manager.py
│   ├── file_operations/        # ファイル操作モジュール
│   │   └── file_handler.py
│   ├── gui/                    # GUIモジュール
│   │   └── main_window.py
│   └── utils/                  # ユーティリティモジュール
│       └── logger.py
├── tests/                      # テストディレクトリ
├── docs/                       # ドキュメント
├── requirements.txt            # 依存パッケージ
└── README.md
```

## テスト
### テストの実行
```bash
# すべてのテストを実行
pytest

# 詳細なテスト結果を表示
pytest -v

# テストカバレッジを計測
pytest --cov=src --cov-report=term-missing
```

### 環境依存のテスト
一部のテストは特定の環境でのみ実行されます：
- `@pytest.mark.linux_only`: Linux環境専用のテスト
- `@pytest.mark.windows_only`: Windows環境専用のテスト

### 継続的インテグレーション
- GitHub Actionsを使用した自動テスト
- Ubuntu環境でのテスト実行
- テストカバレッジレポートの自動生成
- Codecovへのレポートアップロード

## エラーコード
エラーが発生した場合は、`ERROR_REFERENCE.md`を参照してください。主なエラーコードは以下の通りです：

- DISK_001〜006: ディスク操作関連のエラー
- FILE_001〜006: ファイル操作関連のエラー
- SYS_001〜003: システム関連のエラー

## 開発者向け情報

### コードスタイル
- PEP 8に準拠
- Type Hintsを使用
- docstringによるドキュメント化

### テストカバレッジ目標
- 全体のカバレッジ: 80%以上
- 重要なモジュール（ディスク操作、ファイル操作）: 90%以上

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。

## 注意事項
- このプログラムはLinux環境（LubuntuまたはUbuntuベース）での動作を前提としています
- データ復旧時は、元のデータを変更しないよう読み取り専用でマウントします
- 大容量データのコピー時は、十分な空き容量があることを確認してください
