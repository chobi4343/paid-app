"""
有給休暇管理システム - デスクトップアプリ版（Tkinter）
ブラウザ不要、Pythonのみで動作
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime
from typing import List

from utils.data_models import Employee, Department, Grant, Take, generate_employee_code, generate_uuid
from utils.calculations import calculate_remaining_days, auto_populate_grants, get_statutory_grant_schedule


# データファイルのパス
DATA_DIR = "demo_data"
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")
DEPARTMENTS_FILE = os.path.join(DATA_DIR, "departments.json")


class EmployeeManagementApp:
    """有給管理デスクトップアプリ"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("有給休暇管理システム")
        self.root.geometry("1200x700")
        
        # データ初期化
        self.init_data_dir()
        self.employees: List[Employee] = []
        self.departments: List[Department] = []
        self.load_data()
        
        # UIセットアップ
        self.setup_ui()
        self.refresh_employee_list()
    
    def init_data_dir(self):
        """データディレクトリを初期化"""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # データファイルが存在しない場合はデモデータを作成
        if not os.path.exists(EMPLOYEES_FILE) or not os.path.exists(DEPARTMENTS_FILE):
            self.create_demo_data()
    
    def create_demo_data(self):
        """デモデータを作成"""
        from dateutil.relativedelta import relativedelta
        today = datetime.now()
        
        # 部署データ
        departments = [
            {"id": "dept1", "name": "営業部", "createdAt": today.isoformat()},
            {"id": "dept2", "name": "開発部", "createdAt": today.isoformat()},
            {"id": "dept3", "name": "総務部", "createdAt": today.isoformat()},
        ]
        self.save_json(DEPARTMENTS_FILE, departments)
        
        # 従業員データ
        employees = [
            {
                "id": "emp1", "employeeCode": "E001", "name": "佐藤 太郎",
                "furigana": "サトウ タロウ", "department": "営業部",
                "employeeType": "Full-time", "weeklyDays": 5, "dailyHours": 8.0,
                "joinDate": (today - relativedelta(years=3)).strftime('%Y-%m-%d'),
                "resignationDate": "", "grants": [], "takes": []
            },
            {
                "id": "emp2", "employeeCode": "E002", "name": "田中 花子",
                "furigana": "タナカ ハナコ", "department": "開発部",
                "employeeType": "Part-time", "weeklyDays": 4, "dailyHours": 6.5,
                "joinDate": (today - relativedelta(months=8)).strftime('%Y-%m-%d'),
                "resignationDate": "", "grants": [], "takes": []
            },
        ]
        
        # 法定付与を自動追加
        for emp_data in employees:
            emp = Employee.from_dict(emp_data)
            emp = auto_populate_grants(emp)
            emp_data.update(emp.to_dict())
        
        self.save_json(EMPLOYEES_FILE, employees)
    
    def load_json(self, file_path: str, default_value: list) -> list:
        """JSONファイルからデータを読み込む"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("エラー", f"データ読み込みエラー: {e}")
                return default_value
        return default_value
    
    def save_json(self, file_path: str, data: list):
        """JSONファイルにデータを保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("エラー", f"データ保存エラー: {e}")
            return False
    
    def load_data(self):
        """データを読み込む"""
        emp_data = self.load_json(EMPLOYEES_FILE, [])
        self.employees = [Employee.from_dict(e) for e in emp_data]
        
        dept_data = self.load_json(DEPARTMENTS_FILE, [])
        self.departments = [Department.from_dict(d) for d in dept_data]
    
    def save_employees(self):
        """従業員データを保存"""
        data = [emp.to_dict() for emp in self.employees]
        return self.save_json(EMPLOYEES_FILE, data)
    
    def setup_ui(self):
        """UIをセットアップ"""
        # タイトル
        title_frame = tk.Frame(self.root, bg="#4F46E5", height=80)
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame, 
            text="📅 有給休暇管理システム（デスクトップ版）",
            font=("Arial", 20, "bold"),
            bg="#4F46E5",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # ボタンフレーム
        button_frame = tk.Frame(self.root, bg="#F0F2F6", height=60)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            button_frame, 
            text="🔄 再読込", 
            command=self.reload_data,
            font=("Arial", 12),
            bg="#6B7280",
            fg="white",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="➕ 新規登録", 
            command=self.add_employee,
            font=("Arial", 12),
            bg="#10B981",
            fg="white",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="⚙️ 設定", 
            command=self.show_settings,
            font=("Arial", 12),
            bg="#6366F1",
            fg="white",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        # 検索フレーム
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 検索:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_employee_list())
        tk.Entry(
            search_frame, 
            textvariable=self.search_var, 
            font=("Arial", 11),
            width=30
        ).pack(side=tk.LEFT, padx=5)
        
        # 従業員リスト（Treeview）
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ("コード", "名前", "部署", "種別", "入社日", "残日数")
        self.tree = ttk.Treeview(
            list_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=scrollbar.set,
            height=20
        )
        scrollbar.config(command=self.tree.yview)
        
        # カラム設定
        self.tree.heading("コード", text="コード")
        self.tree.heading("名前", text="名前")
        self.tree.heading("部署", text="部署")
        self.tree.heading("種別", text="種別")
        self.tree.heading("入社日", text="入社日")
        self.tree.heading("残日数", text="残日数")
        
        self.tree.column("コード", width=100)
        self.tree.column("名前", width=150)
        self.tree.column("部署", width=120)
        self.tree.column("種別", width=150)
        self.tree.column("入社日", width=120)
        self.tree.column("残日数", width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # ダブルクリックで編集
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # ステータスバー
        self.status_bar = tk.Label(
            self.root, 
            text="準備完了", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=("Arial", 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def refresh_employee_list(self):
        """従業員リストを更新"""
        # 既存のアイテムをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 検索フィルター
        search_term = self.search_var.get().lower()
        filtered_employees = [
            emp for emp in self.employees
            if search_term in emp.name.lower() or 
               search_term in emp.employeeCode.lower() or
               search_term in emp.furigana.lower()
        ]
        
        # ソート
        filtered_employees.sort(key=lambda x: x.employeeCode)
        
        # データを追加
        for emp in filtered_employees:
            remaining = calculate_remaining_days(emp.grants, emp.takes, emp.resignationDate)
            emp_type = f"パート(週{emp.weeklyDays}日)" if emp.employeeType == 'Part-time' else '正社員'
            
            self.tree.insert("", tk.END, values=(
                emp.employeeCode,
                emp.name,
                emp.department or '未設定',
                emp_type,
                emp.joinDate or '未設定',
                f"{remaining:.1f}日"
            ), tags=(emp.id,))
        
        # ステータス更新
        self.status_bar.config(text=f"従業員数: {len(filtered_employees)}名")
    
    def on_double_click(self, event):
        """ダブルクリックで編集"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            emp_id = item['tags'][0]
            emp = next((e for e in self.employees if e.id == emp_id), None)
            if emp:
                self.edit_employee(emp)
    
    def add_employee(self):
        """新規従業員を追加"""
        new_code = generate_employee_code(self.employees)
        emp = Employee(
            id=generate_uuid(),
            employeeCode=new_code,
            name='',
            employeeType='Full-time',
            weeklyDays=5,
            dailyHours=8.0
        )
        self.edit_employee(emp, is_new=True)
    
    def edit_employee(self, emp: Employee, is_new: bool = False):
        """従業員を編集"""
        # 編集ウィンドウを開く
        edit_window = tk.Toplevel(self.root)
        edit_window.title("従業員編集" if not is_new else "新規従業員登録")
        edit_window.geometry("800x600")
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(edit_window)
        scrollbar = ttk.Scrollbar(edit_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 基本情報
        tk.Label(scrollable_frame, text="基本情報", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        tk.Label(scrollable_frame, text="従業員コード*:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        code_entry = tk.Entry(scrollable_frame, width=30)
        code_entry.insert(0, emp.employeeCode)
        code_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(scrollable_frame, text="名前*:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        name_entry = tk.Entry(scrollable_frame, width=30)
        name_entry.insert(0, emp.name)
        name_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(scrollable_frame, text="ふりがな:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        furigana_entry = tk.Entry(scrollable_frame, width=30)
        furigana_entry.insert(0, emp.furigana)
        furigana_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(scrollable_frame, text="部署:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        dept_var = tk.StringVar(value=emp.department)
        dept_combo = ttk.Combobox(
            scrollable_frame, 
            textvariable=dept_var,
            values=[d.name for d in self.departments],
            width=28
        )
        dept_combo.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(scrollable_frame, text="入社日:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        join_entry = tk.Entry(scrollable_frame, width=30)
        join_entry.insert(0, emp.joinDate)
        join_entry.grid(row=5, column=1, padx=5, pady=5)
        
        # 残日数表示
        remaining = calculate_remaining_days(emp.grants, emp.takes, emp.resignationDate)
        tk.Label(
            scrollable_frame, 
            text=f"現在の残日数: {remaining:.1f}日",
            font=("Arial", 12, "bold"),
            fg="#4F46E5"
        ).grid(row=6, column=0, columnspan=2, pady=15)
        
        # 保存ボタン
        def save():
            if not code_entry.get() or not name_entry.get():
                messagebox.showerror("エラー", "従業員コードと名前は必須です")
                return
            
            emp.employeeCode = code_entry.get()
            emp.name = name_entry.get()
            emp.furigana = furigana_entry.get()
            emp.department = dept_var.get()
            emp.joinDate = join_entry.get()
            
            # 法定付与を自動追加
            emp_updated = auto_populate_grants(emp)
            
            if is_new:
                self.employees.append(emp_updated)
            else:
                idx = next(i for i, e in enumerate(self.employees) if e.id == emp.id)
                self.employees[idx] = emp_updated
            
            if self.save_employees():
                messagebox.showinfo("成功", "保存しました")
                self.refresh_employee_list()
                edit_window.destroy()
        
        button_frame = tk.Frame(scrollable_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="💾 保存", command=save, bg="#10B981", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="キャンセル", command=edit_window.destroy, padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        
        if not is_new:
            tk.Button(
                button_frame, 
                text="🗑️ 削除", 
                command=lambda: self.delete_employee(emp, edit_window),
                bg="#EF4444",
                fg="white",
                padx=20,
                pady=5
            ).pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def delete_employee(self, emp: Employee, window):
        """従業員を削除"""
        if messagebox.askyesno("確認", f"{emp.name}を削除しますか？"):
            self.employees = [e for e in self.employees if e.id != emp.id]
            if self.save_employees():
                messagebox.showinfo("成功", "削除しました")
                self.refresh_employee_list()
                window.destroy()
    
    def reload_data(self):
        """データを再読込"""
        self.load_data()
        self.refresh_employee_list()
        messagebox.showinfo("完了", "データを再読込しました")
    
    def show_settings(self):
        """設定画面を表示"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("設定 - 部署マスター")
        settings_window.geometry("500x400")
        
        tk.Label(settings_window, text="部署マスター管理", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 部署リスト
        listbox_frame = tk.Frame(settings_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        dept_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Arial", 11))
        scrollbar.config(command=dept_listbox.yview)
        dept_listbox.pack(fill=tk.BOTH, expand=True)
        
        def refresh_dept_list():
            dept_listbox.delete(0, tk.END)
            for dept in self.departments:
                emp_count = sum(1 for emp in self.employees if emp.department == dept.name)
                dept_listbox.insert(tk.END, f"{dept.name} ({emp_count}名)")
        
        refresh_dept_list()
        
        # ボタン
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=10)
        
        def add_dept():
            name = simpledialog.askstring("新規部署", "部署名を入力してください:")
            if name:
                new_dept = Department(id=generate_uuid(), name=name.strip(), createdAt=datetime.now().isoformat())
                self.departments.append(new_dept)
                self.save_json(DEPARTMENTS_FILE, [d.to_dict() for d in self.departments])
                refresh_dept_list()
        
        tk.Button(button_frame, text="➕ 追加", command=add_dept, padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="閉じる", command=settings_window.destroy, padx=15, pady=5).pack(side=tk.LEFT, padx=5)


def main():
    """メイン関数"""
    root = tk.Tk()
    app = EmployeeManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

