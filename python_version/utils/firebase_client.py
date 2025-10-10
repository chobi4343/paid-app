"""
Firebase接続管理
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Optional
import os


class FirebaseClient:
    """Firebaseクライアント"""
    
    def __init__(self, config_path: str = "firebase_config.json", app_id: str = "default-app-id"):
        self.app_id = app_id
        self.db = None
        
        if not firebase_admin._apps:
            try:
                # Firebase Admin SDKの初期化
                if os.path.exists(config_path):
                    cred = credentials.Certificate(config_path)
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                else:
                    print(f"警告: {config_path} が見つかりません。デモモードで動作します。")
            except Exception as e:
                print(f"Firebase初期化エラー: {e}")
        else:
            self.db = firestore.client()
    
    def get_collection_path(self, collection_name: str) -> str:
        """コレクションパスを生成"""
        return f"artifacts/{self.app_id}/public/data/{collection_name}"
    
    def get_employees(self) -> List[dict]:
        """全従業員データを取得"""
        if not self.db:
            return []
        
        try:
            docs = self.db.collection(self.get_collection_path('employees')).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"従業員データ取得エラー: {e}")
            return []
    
    def get_departments(self) -> List[dict]:
        """全部署データを取得"""
        if not self.db:
            return []
        
        try:
            docs = self.db.collection(self.get_collection_path('departments')).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"部署データ取得エラー: {e}")
            return []
    
    def save_employee(self, employee_data: dict) -> bool:
        """従業員データを保存"""
        if not self.db:
            return False
        
        try:
            emp_id = employee_data.get('id')
            if not emp_id:
                # 新規作成
                doc_ref = self.db.collection(self.get_collection_path('employees')).document()
                employee_data['id'] = doc_ref.id
                doc_ref.set(employee_data)
            else:
                # 更新
                self.db.collection(self.get_collection_path('employees')).document(emp_id).set(
                    employee_data, merge=True
                )
            return True
        except Exception as e:
            print(f"従業員データ保存エラー: {e}")
            return False
    
    def delete_employee(self, employee_id: str) -> bool:
        """従業員データを削除"""
        if not self.db:
            return False
        
        try:
            self.db.collection(self.get_collection_path('employees')).document(employee_id).delete()
            return True
        except Exception as e:
            print(f"従業員データ削除エラー: {e}")
            return False
    
    def save_department(self, department_data: dict) -> bool:
        """部署データを保存"""
        if not self.db:
            return False
        
        try:
            dept_id = department_data.get('id')
            if not dept_id:
                # 新規作成
                doc_ref = self.db.collection(self.get_collection_path('departments')).document()
                department_data['id'] = doc_ref.id
                doc_ref.set(department_data)
            else:
                # 更新
                self.db.collection(self.get_collection_path('departments')).document(dept_id).set(
                    department_data, merge=True
                )
            return True
        except Exception as e:
            print(f"部署データ保存エラー: {e}")
            return False
    
    def delete_department(self, department_id: str) -> bool:
        """部署データを削除"""
        if not self.db:
            return False
        
        try:
            self.db.collection(self.get_collection_path('departments')).document(department_id).delete()
            return True
        except Exception as e:
            print(f"部署データ削除エラー: {e}")
            return False

