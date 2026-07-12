"""
NotifyAI V4.2 Professional
Core Package
"""

from .engine import NotifyEngine

from .database import Database

from .notification_db import NotificationDatabase

from .crawler import Crawler

from .discovery import WebsiteDiscovery

from .parser import Parser

from .matcher import Matcher

from .ai_classifier import AIClassifier

from .notifier import TelegramNotifier

from .dashboard import Dashboard

from .statistics import StatisticsEngine

from .report_generator import ReportGenerator

from .daily_report import DailyReport

from .workflow import WorkflowEngine

from .scheduler import Scheduler

__version__ = "4.2.0"

__author__ = "NotifyAI"

__license__ = "MIT"

__all__ = [

    "NotifyEngine",

    "Database",

    "NotificationDatabase",

    "Crawler",

    "WebsiteDiscovery",

    "Parser",

    "Matcher",

    "AIClassifier",

    "TelegramNotifier",

    "Dashboard",

    "StatisticsEngine",

    "ReportGenerator",

    "DailyReport",

    "WorkflowEngine",

    "Scheduler",

]
