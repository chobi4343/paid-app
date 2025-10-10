"""
有給休暇管理システム - Streamlit版
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Optional

from utils.firebase_client import FirebaseClient
from utils.data_models import Employee, Department, Grant, Take, generate_employee_code, generate_uuid
from utils.calculations import (
    calculate_remaining_days, 
    auto_populate_grants,
    get_statutory_grant_schedule,
    is_statutory_grant,
    round_to_decimal
)


# ページ設定
st.set_page_config(
    page_title="有給休暇管理システム",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4F46E5;
    }
    .remaining-days {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4F46E5;
    }
</style>
""", unsafe_allow_html=True)


# セッション状態の初期化
if 'firebase_client' not in st.session_state:
    st.session_state.firebase_client = FirebaseClient()

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'list'  # 'list', 'edit', 'settings'

if 'selected_employee' not in st.session_state:
    st.session_state.selected_employee = None

if 'employees' not in st.session_state:
    st.session_state.employees = []

if 'departments' not in st.session_state:
    st.session_state.departments = []


def load_data():
    """データを読み込む"""
    firebase = st.session_state.firebase_client
    
    # 従業員データ
    emp_data = firebase.get_employees()
    st.session_state.employees = [Employee.from_dict(e) for e in emp_data]
    
    # 部署データ
    dept_data = firebase.get_departments()
    st.session_state.departments = [Department.from_dict(d) for d in dept_data]


def show_employee_list():
    """従業員一覧画面"""
    st.markdown("<div class='main-header'><h1>📅 有給休暇管理システム</h1><p>労働基準法に基づく有給休暇の付与・取得・時効を記録・管理します。</p></div>", unsafe_allow_html=True)
    
    # ヘッダーボタン
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader(f"従業員一覧 ({len(st.session_state.employees)}名)")
    with col2:
        if st.button("⚙️ 設定", use_container_width=True):
            st.session_state.current_view = 'settings'
            st.rerun()
    with col3:
        if st.button("➕ 新規登録", use_container_width=True, type="primary"):
            # 新しい従業員コードを生成
            new_code = generate_employee_code(st.session_state.employees)
            st.session_state.selected_employee = Employee(
                id='',
                employeeCode=new_code,
                name='',
                employeeType='Full-time',
                weeklyDays=5,
                dailyHours=8.0
            )
            st.session_state.current_view = 'edit'
            st.rerun()
    
    st.divider()
    
    # 検索・フィルタリング
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 検索", placeholder="名前、コード、ふりがなで検索...")
    with col2:
        dept_names = ['全部署'] + [d.name for d in st.session_state.departments]
        filter_dept = st.selectbox("部署フィルター", dept_names)
    
    # フィルタリング
    filtered_employees = st.session_state.employees
    
    if search_term:
        filtered_employees = [
            emp for emp in filtered_employees
            if search_term.lower() in emp.name.lower() or 
               search_term.lower() in emp.furigana.lower() or 
               search_term.lower() in emp.employeeCode.lower()
        ]
    
    if filter_dept != '全部署':
        filtered_employees = [emp for emp in filtered_employees if emp.department == filter_dept]
    
    # 従業員コード順にソート
    filtered_employees.sort(key=lambda x: x.employeeCode)
    
    # テーブル表示
    if filtered_employees:
        table_data = []
        for emp in filtered_employees:
            remaining = calculate_remaining_days(emp.grants, emp.takes, emp.resignationDate)
            emp_type = f"パート(週{emp.weeklyDays}日)" if emp.employeeType == 'Part-time' else '正社員'
            
            table_data.append({
                'コード': emp.employeeCode,
                '名前': emp.name,
                '部署': emp.department or '未設定',
                '種別': emp_type,
                '入社日': emp.joinDate or '未設定',
                '退社日': emp.resignationDate or '在籍中',
                '残日数': f"{remaining:.1f}",
                'id': emp.id  # 内部用
            })
        
        df = pd.DataFrame(table_data)
        
        # インタラクティブな表示
        st.dataframe(
            df[['コード', '名前', '部署', '種別', '入社日', '退社日', '残日数']],
            use_container_width=True,
            hide_index=True
        )
        
        # 編集ボタン（別セクション）
        st.write("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_code = st.selectbox(
                "編集する従業員を選択",
                [emp.employeeCode for emp in filtered_employees],
                format_func=lambda code: f"{code} - {next(e.name for e in filtered_employees if e.employeeCode == code)}"
            )
        with col2:
            if st.button("編集", use_container_width=True, type="secondary"):
                selected_emp = next(e for e in filtered_employees if e.employeeCode == selected_code)
                st.session_state.selected_employee = selected_emp
                st.session_state.current_view = 'edit'
                st.rerun()
    else:
        st.info("該当する従業員が見つかりませんでした。")


def show_employee_form():
    """従業員編集/新規登録画面"""
    emp = st.session_state.selected_employee
    is_new = not emp.id
    
    st.title("🆕 新規従業員登録" if is_new else "✏️ 従業員情報の編集")
    
    # 戻るボタン
    if st.button("← 従業員一覧に戻る"):
        st.session_state.current_view = 'list'
        st.session_state.selected_employee = None
        st.rerun()
    
    st.divider()
    
    # 残日数サマリー
    remaining = calculate_remaining_days(emp.grants, emp.takes, emp.resignationDate)
    st.markdown(f"""
    <div class='stat-card'>
        <h3>現在の残日数（時効考慮）</h3>
        <div class='remaining-days'>{remaining:.1f} <span style='font-size: 1.2rem; font-weight: normal;'>日</span></div>
        {f"<p style='color: red; margin-top: 0.5rem;'>※退社日 ({emp.resignationDate}) 以降の付与・取得は計算対象外です。</p>" if emp.resignationDate else ""}
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # 基本情報
    with st.expander("📝 基本情報", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            emp.employeeCode = st.text_input("従業員コード（必須）*", value=emp.employeeCode)
            emp.name = st.text_input("名前（必須）*", value=emp.name)
            emp.furigana = st.text_input("ふりがな", value=emp.furigana)
            
            dept_options = [''] + [d.name for d in st.session_state.departments]
            dept_index = dept_options.index(emp.department) if emp.department in dept_options else 0
            emp.department = st.selectbox("所属部署", dept_options, index=dept_index)
        
        with col2:
            emp.employeeType = st.selectbox(
                "従業員の種別", 
                ['Full-time', 'Part-time'],
                index=0 if emp.employeeType == 'Full-time' else 1,
                format_func=lambda x: '正社員' if x == 'Full-time' else 'パート'
            )
            
            if emp.employeeType == 'Part-time':
                emp.weeklyDays = st.selectbox("週所定労働日数（比例付与用）", [1, 2, 3, 4], index=min(emp.weeklyDays - 1, 3))
                emp.dailyHours = st.number_input("1日の所定労働時間", min_value=0.0, max_value=24.0, value=emp.dailyHours, step=0.5)
            else:
                emp.weeklyDays = 5
                emp.dailyHours = 8.0
            
            emp.joinDate = st.date_input(
                "入社日",
                value=datetime.strptime(emp.joinDate, '%Y-%m-%d') if emp.joinDate else None
            ).strftime('%Y-%m-%d') if st.session_state.get('join_date_input') is not None or emp.joinDate else ''
            
            resignation_input = st.date_input(
                "退社日（任意）",
                value=datetime.strptime(emp.resignationDate, '%Y-%m-%d') if emp.resignationDate else None
            )
            emp.resignationDate = resignation_input.strftime('%Y-%m-%d') if resignation_input else ''
    
    # 法定付与スケジュールガイド
    if emp.joinDate:
        join_dt = datetime.strptime(emp.joinDate, '%Y-%m-%d')
        schedule = get_statutory_grant_schedule(join_dt, emp.employeeType, emp.weeklyDays)
        
        if schedule:
            with st.expander("📅 法定付与スケジュール（ガイド）", expanded=False):
                st.info(f"入社日({emp.joinDate})と種別に基づき、以下の付与記録が自動追加されます。")
                
                schedule_data = []
                for sch in schedule:
                    schedule_data.append({
                        '付与日': sch['date'].strftime('%Y-%m-%d'),
                        '日数': f"{sch['days']}日",
                        '理由': sch['reason'],
                        '時効日': sch['expiryDate'].strftime('%Y-%m-%d')
                    })
                
                st.dataframe(pd.DataFrame(schedule_data), use_container_width=True, hide_index=True)
    
    # 付与履歴
    with st.expander("➕ 付与履歴（手動追加）", expanded=True):
        st.write("##### 新しい付与を追加")
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        
        with col1:
            grant_date = st.date_input("付与日", key="grant_date_input")
        with col2:
            grant_days = st.number_input("付与日数", min_value=0.0, step=0.5, key="grant_days_input")
        with col3:
            grant_reason = st.text_input("理由", value="手動付与", key="grant_reason_input")
        with col4:
            st.write("")
            st.write("")
            if st.button("付与追加", type="primary"):
                if grant_date and grant_days > 0:
                    new_grant = Grant(
                        id=generate_uuid(),
                        date=grant_date.strftime('%Y-%m-%d'),
                        days=round_to_decimal(grant_days),
                        reason=grant_reason or '手動付与'
                    )
                    emp.grants.append(new_grant)
                    emp.grants.sort(key=lambda x: x.date)
                    st.success("付与を追加しました")
                    st.rerun()
                else:
                    st.error("付与日と日数を正しく入力してください")
        
        st.write("---")
        st.write("##### 付与履歴一覧")
        
        if emp.grants:
            for i, grant in enumerate(emp.grants):
                expiry_date = datetime.strptime(grant.date, '%Y-%m-%d') + pd.DateOffset(years=2)
                is_expired = expiry_date.date() < datetime.now().date()
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 3, 2, 1])
                with col1:
                    st.write(grant.date)
                with col2:
                    st.write(f"**{grant.days:.1f}日**")
                with col3:
                    st.write(f"_{grant.reason}_")
                with col4:
                    st.write(f"時効日: {expiry_date.strftime('%Y-%m-%d')}")
                    if is_expired:
                        st.caption("🔴 時効")
                with col5:
                    if st.button("削除", key=f"del_grant_{i}"):
                        emp.grants.pop(i)
                        st.rerun()
        else:
            st.info("付与履歴がありません")
    
    # 取得履歴
    with st.expander("📤 取得履歴", expanded=True):
        st.write("##### 新しい取得を追加")
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        
        with col1:
            take_date = st.date_input("取得日", key="take_date_input")
        with col2:
            take_days = st.number_input("取得日数", min_value=0.0, step=0.5, key="take_days_input")
        with col3:
            take_reason = st.text_input("理由", value="", key="take_reason_input")
        with col4:
            st.write("")
            st.write("")
            if st.button("取得追加", type="primary"):
                if take_date and take_days > 0:
                    new_take = Take(
                        id=generate_uuid(),
                        date=take_date.strftime('%Y-%m-%d'),
                        days=round_to_decimal(take_days),
                        reason=take_reason or '有給休暇取得'
                    )
                    emp.takes.append(new_take)
                    emp.takes.sort(key=lambda x: x.date)
                    st.success("取得を追加しました")
                    st.rerun()
                else:
                    st.error("取得日と日数を正しく入力してください")
        
        st.write("---")
        st.write("##### 取得履歴一覧")
        
        if emp.takes:
            for i, take in enumerate(emp.takes):
                col1, col2, col3, col4 = st.columns([2, 1, 4, 1])
                with col1:
                    st.write(take.date)
                with col2:
                    st.write(f"**-{take.days:.1f}日**")
                with col3:
                    st.write(f"_{take.reason}_")
                with col4:
                    if st.button("削除", key=f"del_take_{i}"):
                        emp.takes.pop(i)
                        st.rerun()
        else:
            st.info("取得履歴がありません")
    
    st.divider()
    
    # アクションボタン
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if st.button("💾 基本情報を保存", type="primary", use_container_width=True):
            if not emp.employeeCode or not emp.name:
                st.error("従業員コードと名前は必須です")
            else:
                # 法定付与の自動追加
                emp = auto_populate_grants(emp)
                
                # 保存
                firebase = st.session_state.firebase_client
                if firebase.save_employee(emp.to_dict()):
                    st.success("保存しました！")
                    load_data()
                    st.session_state.current_view = 'list'
                    st.session_state.selected_employee = None
                    st.rerun()
                else:
                    st.error("保存に失敗しました")
    
    with col2:
        if st.button("キャンセル", use_container_width=True):
            st.session_state.current_view = 'list'
            st.session_state.selected_employee = None
            st.rerun()
    
    with col3:
        if not is_new:
            if st.button("🗑️ 従業員を削除", use_container_width=True):
                if st.session_state.get('confirm_delete'):
                    firebase = st.session_state.firebase_client
                    if firebase.delete_employee(emp.id):
                        st.success("削除しました")
                        load_data()
                        st.session_state.current_view = 'list'
                        st.session_state.selected_employee = None
                        st.session_state.confirm_delete = False
                        st.rerun()
                else:
                    st.session_state.confirm_delete = True
                    st.warning("もう一度クリックすると削除されます")
                    st.rerun()


def show_settings():
    """設定画面（部署マスター管理）"""
    st.title("⚙️ 部署マスター管理")
    
    if st.button("← 従業員一覧に戻る"):
        st.session_state.current_view = 'list'
        st.rerun()
    
    st.divider()
    
    # 新規追加フォーム
    with st.container():
        st.subheader("新規部署の追加")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_dept_name = st.text_input("新しい部署名を入力", key="new_dept_input")
        with col2:
            st.write("")
            st.write("")
            if st.button("追加", type="primary", use_container_width=True):
                if new_dept_name.strip():
                    firebase = st.session_state.firebase_client
                    new_dept = Department(
                        id='',
                        name=new_dept_name.strip(),
                        createdAt=datetime.now().isoformat()
                    )
                    if firebase.save_department(new_dept.to_dict()):
                        st.success(f"部署「{new_dept_name}」を追加しました")
                        load_data()
                        st.rerun()
                else:
                    st.error("部署名を入力してください")
    
    st.divider()
    
    # 部署リスト
    st.subheader("部署一覧")
    
    if st.session_state.departments:
        for dept in st.session_state.departments:
            # 割り当て従業員数をカウント
            employee_count = sum(1 for emp in st.session_state.employees if emp.department == dept.name)
            is_assigned = employee_count > 0
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{dept.name}**")
            with col2:
                st.write(f"割り当て従業員: {employee_count}名")
            with col3:
                if is_assigned:
                    st.caption("削除不可")
                else:
                    if st.button("削除", key=f"del_dept_{dept.id}"):
                        firebase = st.session_state.firebase_client
                        if firebase.delete_department(dept.id):
                            st.success(f"部署「{dept.name}」を削除しました")
                            load_data()
                            st.rerun()
            
            st.divider()
    else:
        st.info("部署がありません。最初の部署を追加してください。")


def main():
    """メイン関数"""
    # データ読み込み
    if not st.session_state.employees:
        with st.spinner("データを読み込み中..."):
            load_data()
    
    # サイドバー
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/4F46E5/FFFFFF?text=有給管理", use_column_width=True)
        st.title("ナビゲーション")
        
        if st.button("🏠 従業員一覧", use_container_width=True):
            st.session_state.current_view = 'list'
            st.rerun()
        
        if st.button("⚙️ 設定", use_container_width=True):
            st.session_state.current_view = 'settings'
            st.rerun()
        
        st.divider()
        
        if st.button("🔄 データを再読込", use_container_width=True):
            load_data()
            st.success("再読込しました")
            st.rerun()
        
        st.divider()
        st.caption(f"従業員数: {len(st.session_state.employees)}名")
        st.caption(f"部署数: {len(st.session_state.departments)}部署")
    
    # ビュー表示
    if st.session_state.current_view == 'list':
        show_employee_list()
    elif st.session_state.current_view == 'edit':
        show_employee_form()
    elif st.session_state.current_view == 'settings':
        show_settings()


if __name__ == "__main__":
    main()

