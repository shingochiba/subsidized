# データベースエラー解決スクリプト
# エラー: no such column: advisor_subsidytype.target_business_type

# 解決手順1: マイグレーションの確認と実行
print("=== データベースエラー解決手順 ===")
print()

print("1. 現在のマイグレーション状況を確認:")
print("python manage.py showmigrations")
print()

print("2. データベースの構造を確認:")
print("python manage.py dbshell")
print(".schema advisor_subsidytype")
print(".exit")
print()

print("3. 新しいマイグレーションを作成:")
print("python manage.py makemigrations advisor")
print()

print("4. マイグレーションを適用:")
print("python manage.py migrate")
print()

print("5. 補助金データを投入:")
print("python manage.py load_subsidies")
print()

# 解決手順2: データベースを完全にリセットする場合
print("=== データベース完全リセット（確実な解決法） ===")
print()

print("1. データベースファイルを削除:")
print("rm db.sqlite3")
print()

print("2. マイグレーションファイルを削除:")
print("rm advisor/migrations/0*.py")
print()

print("3. 新しいマイグレーションを作成:")
print("python manage.py makemigrations advisor")
print()

print("4. マイグレーションを適用:")
print("python manage.py migrate")
print()

print("5. スーパーユーザーを作成:")
print("python manage.py createsuperuser")
print()

print("6. 補助金データを投入:")
print("python manage.py load_subsidies")
print()

print("7. 統計データを投入:")
print("python manage.py load_adoption_data")
print()

print("8. 現実的なデータを投入:")
print("python manage.py load_realistic_data")
print()

# 解決手順3: 特定のテーブルを確認・修正
print("=== データベース構造の確認と修正 ===")

# SQLiteでのテーブル構造確認用SQL
sql_commands = """
-- 現在のテーブル構造を確認
.schema advisor_subsidytype

-- カラム一覧を確認  
PRAGMA table_info(advisor_subsidytype);

-- target_business_type カラムが存在するか確認
SELECT sql FROM sqlite_master WHERE type='table' AND name='advisor_subsidytype';
"""

print("SQLiteでテーブル構造を確認:")
print(sql_commands)
print()

# 解決手順4: 問題のコードを特定
print("=== 問題のコード特定 ===")
print()

print("1. target_business_type を検索:")
print("grep -r 'target_business_type' .")
print()

print("2. テンプレートファイルを確認:")
print("find . -name '*.html' -exec grep -l 'target_business_type' {} \\;")
print()

print("3. Pythonファイルを確認:")
print("find . -name '*.py' -exec grep -l 'target_business_type' {} \\;")
print()

# 解決手順5: 応急処置（フィールド名の統一）
print("=== 応急処置: フィールド名の統一 ===")
print()

# models.pyの現在のフィールド名を確認
current_model = """
class SubsidyType(models.Model):
    name = models.CharField(max_length=200, verbose_name="補助金名")
    description = models.TextField(verbose_name="概要")
    target_business = models.TextField(verbose_name="対象事業")  # ← これが正しいフィールド名
    application_period = models.CharField(max_length=100, verbose_name="申請期間")
    max_amount = models.IntegerField(verbose_name="最大補助額")
    subsidy_rate = models.CharField(max_length=50, verbose_name="補助率")
    requirements = models.TextField(verbose_name="申請要件")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
"""

print("現在のSubsidyTypeモデル:")
print(current_model)
print()

print("すべてのコードで 'target_business' を使用し、'target_business_type' は使用しないでください。")
print()

print("=== 実行推奨コマンド（安全な解決法） ===")
print()
print("# 1. データベースを初期化")
print("rm db.sqlite3")
print("rm advisor/migrations/0*.py")
print()
print("# 2. 新しいマイグレーション作成・適用")
print("python manage.py makemigrations advisor")
print("python manage.py migrate")
print()
print("# 3. データ投入")
print("python manage.py load_subsidies")
print()
print("# 4. サーバー起動")
print("python manage.py runserver")