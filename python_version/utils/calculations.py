"""
有給休暇の計算ロジック
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Tuple, Optional
from .data_models import Employee, Grant, Take, generate_uuid


# 有給休暇の比例付与日数マトリックス
GRANT_DAYS_MATRIX = {
    5: [10, 11, 12, 14, 16, 18, 20],  # 正社員（週5日）
    4: [7, 8, 9, 10, 12, 13, 15],     # パート（週4日）
    3: [5, 6, 6, 8, 9, 10, 11],       # パート（週3日）
    2: [3, 4, 4, 5, 6, 6, 7],         # パート（週2日）
    1: [1, 2, 2, 2, 3, 3, 3],         # パート（週1日）
}


def round_to_decimal(num: float) -> float:
    """数値を小数点以下1桁で丸める"""
    return round(num * 10) / 10


def days_to_units(days: float) -> int:
    """日数を単位（10倍した整数）に変換"""
    return round(days * 10)


def units_to_days(units: int) -> float:
    """単位を日数に変換"""
    return units / 10


def is_statutory_grant(reason: str) -> bool:
    """付与理由が法定付与によるものか判定"""
    return reason and (reason.startswith('正社員') or reason.startswith('パート'))


def get_statutory_grant_schedule(
    join_date: datetime, 
    employee_type: str, 
    weekly_days: int
) -> List[dict]:
    """
    有給休暇の法定付与スケジュールを取得
    
    Args:
        join_date: 入社日
        employee_type: 従業員種別 ('Full-time' or 'Part-time')
        weekly_days: 週所定労働日数 (1-5)
    
    Returns:
        付与スケジュールのリスト [{date, days, reason, expiryDate}]
    """
    if not join_date:
        return []
    
    schedule = []
    
    # 週所定労働日数の決定
    days_key = 5 if employee_type == 'Full-time' else min(weekly_days, 4)
    
    grant_days_array = GRANT_DAYS_MATRIX.get(days_key)
    if not grant_days_array:
        return []
    
    # 勤続年数（N.5年）
    service_years = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
    
    for i, year in enumerate(service_years):
        years = int(year)
        months = int((year % 1) * 12)
        
        grant_date = join_date + relativedelta(years=years, months=months)
        days = grant_days_array[i]
        expiry_date = grant_date + relativedelta(years=2)
        
        reason_prefix = f"パート(週{days_key}日)" if employee_type == 'Part-time' else "正社員"
        reason = f"{reason_prefix} {year}年勤続"
        
        schedule.append({
            'date': grant_date,
            'days': days,
            'reason': reason,
            'expiryDate': expiry_date,
        })
        
        # 6.5年以降は毎年付与
        if i == len(service_years) - 1:
            current_year = grant_date.year + 1
            limit_year = datetime.now().year + 1
            
            while current_year <= limit_year:
                subsequent_grant_date = datetime(
                    current_year, grant_date.month, grant_date.day
                )
                schedule.append({
                    'date': subsequent_grant_date,
                    'days': days,
                    'reason': f"{reason_prefix} {current_year - join_date.year - 0.5}年勤続（法定最大）",
                    'expiryDate': subsequent_grant_date + relativedelta(years=2),
                })
                current_year += 1
    
    # 古い順にソート
    schedule.sort(key=lambda x: x['date'])
    return schedule


def auto_populate_grants(employee: Employee) -> Employee:
    """
    入社日を基に法定付与を自動で「付与履歴」に追加（手動付与を維持）
    
    Args:
        employee: 従業員データ
    
    Returns:
        更新された従業員データ
    """
    if not employee.joinDate:
        return employee
    
    today = datetime.now()
    join_date = datetime.strptime(employee.joinDate, '%Y-%m-%d')
    resignation_date = (
        datetime.strptime(employee.resignationDate, '%Y-%m-%d')
        if employee.resignationDate else None
    )
    
    # 法定付与スケジュールを取得
    statutory_schedule = get_statutory_grant_schedule(
        join_date, employee.employeeType, employee.weeklyDays
    )
    
    # 既存の手動付与のみを保持
    manual_grants = [g for g in employee.grants if not is_statutory_grant(g.reason)]
    
    # 新しい自動付与リストを作成
    auto_grants = []
    for sch in statutory_schedule:
        grant_date = sch['date']
        if grant_date <= today and (not resignation_date or grant_date < resignation_date):
            auto_grants.append(Grant(
                id=generate_uuid(),
                date=grant_date.strftime('%Y-%m-%d'),
                days=sch['days'],
                reason=sch['reason']
            ))
    
    # 自動付与と手動付与をマージし、日付順にソート
    final_grants = auto_grants + manual_grants
    final_grants.sort(key=lambda x: datetime.strptime(x.date, '%Y-%m-%d'))
    
    employee.grants = final_grants
    return employee


def calculate_remaining_days(
    grants: List[Grant], 
    takes: List[Take], 
    resignation_date_str: Optional[str] = None
) -> float:
    """
    残日数を計算する（FIFO & 2年時効ロジック）
    
    Args:
        grants: 付与履歴
        takes: 取得履歴
        resignation_date_str: 退社日 (YYYY-MM-DD)
    
    Returns:
        残日数
    """
    if not grants:
        return 0.0
    
    today = datetime.now()
    resignation_date = (
        datetime.strptime(resignation_date_str, '%Y-%m-%d')
        if resignation_date_str else None
    )
    
    # 付与をDateオブジェクトに変換し、日付順にソート
    grant_stack = []
    for g in grants:
        grant_date = datetime.strptime(g.date, '%Y-%m-%d')
        grant_stack.append({
            'grantDate': grant_date,
            'initialUnits': days_to_units(g.days),
            'remainingUnits': days_to_units(g.days),
        })
    grant_stack.sort(key=lambda x: x['grantDate'])
    
    # 取得履歴を日付順にソートし、消化を行う（FIFO）
    takes_sorted = []
    for t in takes:
        take_date = datetime.strptime(t.date, '%Y-%m-%d')
        takes_sorted.append({
            'date': take_date,
            'units': days_to_units(t.days)
        })
    takes_sorted.sort(key=lambda x: x['date'])
    
    # 時効を先に適用（取得処理の前に時効済みの付与を除外）
    # 退社日がある場合は退社日を基準に、ない場合は今日を基準に時効を判定
    check_date = resignation_date if resignation_date else today
    valid_grants = []
    for grant in grant_stack:
        expiry_date = grant['grantDate'] + relativedelta(years=2)
        # 退社日がある場合：退社日と時効日の早い方を基準に判定
        if resignation_date:
            effective_expiry_date = min(expiry_date, resignation_date)
        else:
            effective_expiry_date = expiry_date
        
        if check_date < effective_expiry_date:
            # 時効前かつ退社前: 有効な付与として保持
            valid_grants.append(grant)
        # else: 時効後または退社後は失効（除外）
    
    # 有効な付与のみでFIFO方式で消化
    for take in takes_sorted:
        take_date = take['date']
        
        # 退職日以降の取得は無視
        if resignation_date and take_date >= resignation_date:
            continue
        
        units_to_consume = take['units']
        
        for grant in valid_grants:
            if grant['remainingUnits'] > 0:
                consumed_units = min(units_to_consume, grant['remainingUnits'])
                grant['remainingUnits'] -= consumed_units
                units_to_consume -= consumed_units
                
                if units_to_consume <= 0:
                    break
    
    # 最終残高を計算
    final_remaining_units = 0
    for grant in valid_grants:
        final_remaining_units += grant['remainingUnits']
    
    # 最終結果を日数に戻して丸めて返す
    return round_to_decimal(units_to_days(final_remaining_units))

