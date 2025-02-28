# 開発メモ

## 関数名
- `detect_disks`: ディスクの自動検出
- `mount_disk`: ディスクのマウント
- `unmount_disk`: ディスクのアンマウント
- `check_filesystem`: ファイルシステムのチェック
  - ext4ファイルシステムの場合は `fsck.ext4` コマンドを実行
  - ntfsファイルシステムの場合は `ntfsfix` コマンドを実行
- `get_disk_info`: ディスク情報の取得
- `_parse_size`: ディスクサイズ文字列をバイト単位の整数に変換

## 変数名
- `device_path`: デバイスパス
- `size`: ディスクのサイズ
- `filesystem`: ファイルシステムの種類
- `mounted`: マウント状態
- `health_status`: ヘルスステータス
- `is_consistent`: ファイルシステムの整合性
- `details`: 状態詳細
- `model`: ディスクのモデル
- `serial`: シリアル番号
- `partition_table`: パーティションテーブルの種類
- `smart_status`: SMARTステータス情報 

## エラーハンドリング
- `src/disk_operations/disk_manager.py`
  - `mount_disk` メソッド
    - エラーコード `DISK_002` を追加
    - エラーメッセージにディスクとマウントポイントの情報を含める
    - `print` 文を `logger.log_error` に置き換え
  - `unmount_disk` メソッド
    - エラーコード `DISK_003` を追加
    - エラーメッセージにディスクの情報を含める
    - `print` 文を `logger.log_error` に置き換え
  - `check_filesystem` メソッド
    - ext4とntfsのファイルシステムチェック失敗時のエラーハンドリングを改善
      - エラーコード `DISK_004` を追加
      - エラーメッセージにディスクの情報を含める
      - `print` 文を `logger.log_error` に置き換え
    - 未対応のファイルシステムの場合のエラーハンドリングを改善
      - エラーコード `DISK_005` を追加
      - エラーメッセージにディスクの情報を含める
      - `print` 文を `logger.log_error` に置き換え
  - `get_disk_info` メソッド
    - SMARTステータス取得失敗時のエラーハンドリングを改善
      - エラーコード `DISK_006` を追加
      - エラーメッセージにディスクの情報を含める
      - `print` 文を `logger.log_error` に置き換え

- `src/file_operations/file_handler.py`
  - `list_files` メソッド
    - エラーコード `FILE_001` を追加
    - エラーメッセージにパスの情報を含める
    - `print` 文を `logger.log_error` に置き換え
  - `copy_files` メソッド  
    - エラーコード `FILE_002` を追加
    - エラーメッセージにコピー元とコピー先の情報を含める
    - `print` 文を `logger.log_error` に置き換え
  - `verify_copy` メソッド
    - エラーコード `FILE_003` を追加
    - エラーメッセージにコピー元とコピー先の情報を含める
    - `print` 文を `logger.log_error` に置き換え
  - `get_file_attributes` メソッド
    - エラーコード `FILE_004` を追加
    - エラーメッセージにファイルの情報を含める
    - `print` 文を `logger.log_error` に置き換え
  - `check_file_accessibility` メソッド
    - エラーコード `FILE_005` を追加
    - エラーメッセージにファイルの情報を含める
    - `print` 文を `logger.log_error` に置き換え
  - `handle_corrupted_files` メソッド
    - エラーコード `FILE_006` を追加
    - エラーメッセージにファイルの情報を含める
    - `print` 文を `logger.log_error` に置き換え 