"""
データモデルとヘルパー関数
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid


@dataclass
class Grant:
    """有給付与記録"""
    id: str
    date: str  # YYYY-MM-DD
    days: float
    reason: str


@dataclass
class Take:
    """有給取得記録"""
    id: str
    date: str  # YYYY-MM-DD
    days: float
    reason: str


@dataclass
class Employee:
    """従業員データ"""
    id: str
    employeeCode: str
    name: str
    furigana: str = ""
    department: str = ""
    employeeType: str = "Full-time"  # 'Full-time' or 'Part-time'
    weeklyDays: int = 5  # 週所定労働日数
    dailyHours: float = 8.0  # 1日の所定労働時間
    joinDate: str = ""  # YYYY-MM-DD
    resignationDate: str = ""  # YYYY-MM-DD
    grants: List[Grant] = field(default_factory=list)
    takes: List[Take] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'Employee':
        """辞書からEmployeeオブジェクトを作成"""
        grants = [Grant(**g) for g in data.get('grants', [])]
        takes = [Take(**t) for t in data.get('takes', [])]
        
        return cls(
            id=data.get('id', ''),
            employeeCode=data.get('employeeCode', ''),
            name=data.get('name', ''),
            furigana=data.get('furigana', ''),
            department=data.get('department', ''),
            employeeType=data.get('employeeType', 'Full-time'),
            weeklyDays=data.get('weeklyDays', 5),
            dailyHours=data.get('dailyHours', 8.0),
            joinDate=data.get('joinDate', ''),
            resignationDate=data.get('resignationDate', ''),
            grants=grants,
            takes=takes
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'employeeCode': self.employeeCode,
            'name': self.name,
            'furigana': self.furigana,
            'department': self.department,
            'employeeType': self.employeeType,
            'weeklyDays': self.weeklyDays,
            'dailyHours': self.dailyHours,
            'joinDate': self.joinDate,
            'resignationDate': self.resignationDate,
            'grants': [g.__dict__ for g in self.grants],
            'takes': [t.__dict__ for t in self.takes]
        }


@dataclass
class Department:
    """部署データ"""
    id: str
    name: str
    createdAt: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> 'Department':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            createdAt=data.get('createdAt', '')
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'createdAt': self.createdAt
        }


def generate_employee_code(employees: List[Employee]) -> str:
    """
    従業員コードを自動生成 (例: E001, E002...)
    """
    max_num = 0
    for emp in employees:
        if emp.employeeCode and emp.employeeCode.startswith('E'):
            try:
                num = int(emp.employeeCode[1:])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    next_num = max_num + 1
    return f"E{next_num:03d}"


def generate_uuid() -> str:
    """UUIDを生成"""
    return str(uuid.uuid4())

