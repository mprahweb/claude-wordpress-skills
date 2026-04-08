from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Customer:
    id: Optional[int]
    number: str
    name: str
    created_at: Optional[str] = None


@dataclass
class Project:
    id: Optional[int]
    customer_id: int
    name: str
    description: str = ""
    created_at: Optional[str] = None
    customer_name: Optional[str] = None


@dataclass
class Task:
    id: Optional[int]
    name: str
    is_global: bool = True
    project_id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class TimeEntry:
    id: Optional[int]
    customer_id: int
    project_id: int
    task_id: Optional[int]
    start_time: str
    end_time: str
    duration_minutes: int
    note: str = ""
    invoiced: bool = False
    not_billable: bool = False
    created_at: Optional[str] = None
    customer_name: Optional[str] = None
    project_name: Optional[str] = None
    task_name: Optional[str] = None
    customer_number: Optional[str] = None
