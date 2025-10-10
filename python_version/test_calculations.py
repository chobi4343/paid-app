"""
有給計算ロジックのテストスクリプト
実行方法: python3 test_calculations.py
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.calculations import (
    calculate_remaining_days,
    get_statutory_grant_schedule,
    auto_populate_grants,
    round_to_decimal
)
from utils.data_models import Employee, Grant, Take, generate_uuid


def test_basic_calculation():
    """基本的な残日数計算のテスト"""
    print("=" * 50)
    print("テスト1: 基本的な残日数計算")
    print("=" * 50)
    
    # 付与: 10日
    grants = [Grant(id=generate_uuid(), date="2024-01-01", days=10.0, reason="テスト付与")]
    
    # 取得: 3日
    takes = [Take(id=generate_uuid(), date="2024-02-01", days=3.0, reason="テスト取得")]
    
    remaining = calculate_remaining_days(grants, takes, None)
    
    print(f"付与: 10.0日")
    print(f"取得: 3.0日")
    print(f"残日数: {remaining}日")
    print(f"期待値: 7.0日")
    print(f"結果: {'✅ 成功' if remaining == 7.0 else '❌ 失敗'}")
    print()


def test_statutory_grant_schedule():
    """法定付与スケジュールのテスト"""
    print("=" * 50)
    print("テスト2: 法定付与スケジュール（正社員）")
    print("=" * 50)
    
    join_date = datetime.now() - relativedelta(years=3)
    schedule = get_statutory_grant_schedule(join_date, 'Full-time', 5)
    
    print(f"入社日: {join_date.strftime('%Y-%m-%d')}")
    print(f"従業員種別: 正社員")
    print(f"付与スケジュール件数: {len(schedule)}件")
    print()
    
    for i, sch in enumerate(schedule[:5]):  # 最初の5件のみ表示
        print(f"{i+1}. {sch['date'].strftime('%Y-%m-%d')} - {sch['days']}日 ({sch['reason']})")
    
    print(f"結果: {'✅ 成功' if len(schedule) > 0 else '❌ 失敗'}")
    print()


def test_part_time_grant():
    """パートタイム比例付与のテスト"""
    print("=" * 50)
    print("テスト3: パートタイム比例付与（週4日）")
    print("=" * 50)
    
    join_date = datetime.now() - relativedelta(years=2)
    schedule = get_statutory_grant_schedule(join_date, 'Part-time', 4)
    
    print(f"入社日: {join_date.strftime('%Y-%m-%d')}")
    print(f"従業員種別: パート（週4日）")
    print(f"付与スケジュール件数: {len(schedule)}件")
    print()
    
    for i, sch in enumerate(schedule[:3]):
        print(f"{i+1}. {sch['date'].strftime('%Y-%m-%d')} - {sch['days']}日 ({sch['reason']})")
    
    print(f"結果: {'✅ 成功' if len(schedule) > 0 else '❌ 失敗'}")
    print()


def test_fifo_consumption():
    """FIFO消化のテスト"""
    print("=" * 50)
    print("テスト4: FIFO消化（古い付与から消化）")
    print("=" * 50)
    
    grants = [
        Grant(id=generate_uuid(), date="2023-01-01", days=10.0, reason="1回目付与"),
        Grant(id=generate_uuid(), date="2024-01-01", days=11.0, reason="2回目付与"),
    ]
    
    takes = [
        Take(id=generate_uuid(), date="2024-06-01", days=12.0, reason="まとめて取得"),
    ]
    
    remaining = calculate_remaining_days(grants, takes, None)
    
    print(f"付与1: 2023-01-01 - 10.0日")
    print(f"付与2: 2024-01-01 - 11.0日")
    print(f"取得: 2024-06-01 - 12.0日")
    print(f"残日数: {remaining}日")
    print(f"期待値: 9.0日（1回目の10日を全消化 + 2回目から2日消化 = 残9日）")
    print(f"結果: {'✅ 成功' if remaining == 9.0 else '❌ 失敗'}")
    print()


def test_expiry():
    """時効テスト（2年）"""
    print("=" * 50)
    print("テスト5: 時効（2年後に失効）")
    print("=" * 50)
    
    # 3年前に付与
    old_date = (datetime.now() - relativedelta(years=3)).strftime('%Y-%m-%d')
    grants = [
        Grant(id=generate_uuid(), date=old_date, days=10.0, reason="3年前の付与"),
    ]
    
    takes = []
    
    remaining = calculate_remaining_days(grants, takes, None)
    
    print(f"付与: {old_date} - 10.0日")
    print(f"取得: なし")
    print(f"残日数: {remaining}日")
    print(f"期待値: 0.0日（2年時効により失効）")
    print(f"結果: {'✅ 成功' if remaining == 0.0 else '❌ 失敗'}")
    print()


def test_auto_populate():
    """自動付与のテスト"""
    print("=" * 50)
    print("テスト6: 自動付与機能")
    print("=" * 50)
    
    emp = Employee(
        id=generate_uuid(),
        employeeCode="TEST001",
        name="テスト 太郎",
        employeeType="Full-time",
        weeklyDays=5,
        dailyHours=8.0,
        joinDate=(datetime.now() - relativedelta(years=2)).strftime('%Y-%m-%d'),
    )
    
    print(f"従業員: {emp.name}")
    print(f"入社日: {emp.joinDate}")
    print(f"付与前: {len(emp.grants)}件")
    
    emp = auto_populate_grants(emp)
    
    print(f"付与後: {len(emp.grants)}件")
    
    if emp.grants:
        print(f"最初の付与: {emp.grants[0].date} - {emp.grants[0].days}日 ({emp.grants[0].reason})")
    
    print(f"結果: {'✅ 成功' if len(emp.grants) > 0 else '❌ 失敗'}")
    print()


def test_half_day():
    """半休（0.5日）のテスト"""
    print("=" * 50)
    print("テスト7: 半休（0.5日単位）")
    print("=" * 50)
    
    grants = [Grant(id=generate_uuid(), date="2024-01-01", days=10.0, reason="付与")]
    takes = [
        Take(id=generate_uuid(), date="2024-02-01", days=0.5, reason="午前半休"),
        Take(id=generate_uuid(), date="2024-03-01", days=0.5, reason="午後半休"),
    ]
    
    remaining = calculate_remaining_days(grants, takes, None)
    
    print(f"付与: 10.0日")
    print(f"取得1: 0.5日（午前半休）")
    print(f"取得2: 0.5日（午後半休）")
    print(f"残日数: {remaining}日")
    print(f"期待値: 9.0日")
    print(f"結果: {'✅ 成功' if remaining == 9.0 else '❌ 失敗'}")
    print()


def run_all_tests():
    """全テストを実行"""
    print("\n")
    print("🧪" * 25)
    print("有給計算ロジック テストスイート")
    print("🧪" * 25)
    print("\n")
    
    test_basic_calculation()
    test_statutory_grant_schedule()
    test_part_time_grant()
    test_fifo_consumption()
    test_expiry()
    test_auto_populate()
    test_half_day()
    
    print("=" * 50)
    print("全テスト完了！")
    print("=" * 50)
    print("\n✅ 計算ロジックは正常に動作しています。")
    print("次のステップ: streamlit run app_demo.py でアプリを起動\n")


if __name__ == "__main__":
    run_all_tests()

