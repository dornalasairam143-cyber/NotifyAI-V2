"""
NotifyAI V4 - Report Generator Module
Provides the ReportGenerator class to compile operational statistics and export them
into high-quality CSV, Excel, JSON, and responsive HTML dashboard reports.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

import pandas as pd

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ReportGenerator:
    """
    Generates system performance reports and exports data into multiple formats
    including CSV, Excel, JSON, and responsive HTML dashboards.
    """

    def __init__(self, dashboard: Any, statistics_engine: Any, notification_db: Any) -> None:
        """
        Initializes the ReportGenerator and automatically creates the reports directory.

        Args:
            dashboard (Any): Instance of the Dashboard module.
            statistics_engine (Any): Instance of the StatisticsEngine module.
            notification_db (Any): Instance of the NotificationDatabase module.
        """
        self.dashboard = dashboard
        self.stats_engine = statistics_engine
        self.db = notification_db
        
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"ReportGenerator initialized. Output directory set to: {self.output_dir}")

    def generate_daily_report(self) -> Dict[str, Any]:
        """
        Compiles all core metrics for the daily system operations.

        Returns:
            Dict[str, Any]: Consolidated daily report data matches target schema.
        """
        logger.info("Compiling daily report metrics.")
        try:
            daily_stats = self.stats_engine.get_daily_statistics()
            runtime_stats = self.stats_engine.get_runtime_statistics()
            
            return {
                "date": daily_stats.get("date", datetime.utcnow().strftime('%Y-%m-%d')),
                "articles": daily_stats.get("articles", 0),
                "notifications": daily_stats.get("notifications", 0),
                "new_notifications": daily_stats.get("new_notifications", 0),
                "duplicates": daily_stats.get("duplicates", 0),
                "telegram_sent": daily_stats.get("telegram_sent", 0),
                "failed_scans": daily_stats.get("failed_scans", 0),
                "successful_scans": daily_stats.get("successful_scans", 0),
                "runtime": daily_stats.get("runtime", 0.0),
                "average_scan_time": runtime_stats.get("average_scan_time", 0.0)
            }
        except Exception as e:
            logger.error(f"Error compiling daily report: {e}")
            return {
                "date": datetime.utcnow().strftime('%Y-%m-%d'),
                "articles": 0, "notifications": 0, "new_notifications": 0, "duplicates": 0,
                "telegram_sent": 0, "failed_scans": 0, "successful_scans": 0, "runtime": 0.0, "average_scan_time": 0.0
            }

    def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Compiles core metrics for weekly system operations.

        Returns:
            Dict[str, Any]: Weekly report data.
        """
        logger.info("Compiling weekly report metrics.")
        try:
            weekly_stats = self.stats_engine.get_weekly_statistics()
            scan_stats = self.stats_engine.get_scan_statistics()
            
            report = dict(weekly_stats)
            report.update(scan_stats)
            return report
        except Exception as e:
            logger.error(f"Error compiling weekly report: {e}")
            return {"week": datetime.utcnow().strftime('%Y-W%W'), "articles": 0, "notifications": 0, "telegram": 0, "failed": 0, "runtime": 0.0}

    def generate_monthly_report(self) -> Dict[str, Any]:
        """
        Compiles core metrics for monthly system operations.

        Returns:
            Dict[str, Any]: Monthly report data.
        """
        logger.info("Compiling monthly report metrics.")
        try:
            monthly_stats = self.stats_engine.get_monthly_statistics()
            db_stats = self.stats_engine.get_database_statistics()
            
            report = dict(monthly_stats)
            report.update(db_stats)
            return report
        except Exception as e:
            logger.error(f"Error compiling monthly report: {e}")
            return {"month": datetime.utcnow().strftime('%Y-%m'), "articles": 0, "notifications": 0, "telegram": 0, "failed": 0, "runtime": 0.0}

    def export_csv(self, data: Dict[str, Any], filename: str = "daily_report.csv") -> str:
        """
        Exports report dictionary payload to a CSV file.

        Args:
            data (Dict[str, Any]): The report metrics dictionary.
            filename (str): Target filename inside the reports folder.

        Returns:
            str: Absolute or relative output filepath.
        """
        filepath = os.path.join(self.output_dir, filename)
        logger.info(f"Exporting report to CSV: {filepath}")
        try:
            df = pd.DataFrame([data])
            df.to_csv(filepath, index=False)
            return filepath
        except Exception as e:
            logger.error(f"Failed to export CSV report: {e}")
            raise

    def export_excel(self, data: Dict[str, Any], filename: str = "daily_report.xlsx") -> str:
        """
        Exports report dictionary payload to a styled Excel sheet using openpyxl.

        Args:
            data (Dict[str, Any]): The report metrics dictionary.
            filename (str): Target filename inside the reports folder.

        Returns:
            str: Absolute or relative output filepath.
        """
        filepath = os.path.join(self.output_dir, filename)
        logger.info(f"Exporting report to Excel: {filepath}")
        try:
            df = pd.DataFrame([data])
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Operations Summary")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export Excel report: {e}")
            raise

    def export_json(self, data: Dict[str, Any], filename: str = "daily_report.json") -> str:
        """
        Exports report dictionary payload to a formatted JSON configuration file.

        Args:
            data (Dict[str, Any]): The report metrics dictionary.
            filename (str): Target filename inside the reports folder.

        Returns:
            str: Absolute or relative output filepath.
        """
        filepath = os.path.join(self.output_dir, filename)
        logger.info(f"Exporting report to JSON: {filepath}")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return filepath
        except Exception as e:
            logger.error(f"Failed to export JSON report: {e}")
            raise

    def export_html(self, data: Dict[str, Any], filename: str = "daily_report.html") -> str:
        """
        Generates a modern, responsive HTML dashboard report matching system specifications.

        Args:
            data (Dict[str, Any]): The report metrics dictionary.
            filename (str): Target filename inside the reports folder.

        Returns:
            str: Absolute or relative output filepath.
        """
        filepath = os.path.join(self.output_dir, filename)
        logger.info(f"Exporting report to Dashboard HTML: {filepath}")

        # Compute accurate rate for progress visualization
        total_scans = int(data.get("successful_scans", 0)) + int(data.get("failed_scans", 0))
        success_rate = round((int(data.get("successful_scans", 0)) / total_scans * 100), 1) if total_scans > 0 else 0.0

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NotifyAI V4 - Performance Dashboard</title>
    <style>
        :root {{
            --bg-primary: #f8f9fa;
            --surface: #ffffff;
            --text-main: #212529;
            --text-muted: #6c757d;
            --primary: #0d6efd;
            --success: #198754;
            --danger: #dc3545;
            --border: #dee2e6;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header .date {{ color: var(--text-muted); font-weight: 500; }}
        
        /* Grid Layouts */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }}
        .card-title {{
            font-size: 14px;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: 700;
            margin: 0;
        }}
        
        /* Progress Visualization */
        .progress-section {{
            margin-bottom: 30px;
        }}
        .progress-container {{
            background: #e9ecef;
            border-radius: 50px;
            overflow: hidden;
            height: 20px;
            margin-top: 10px;
        }}
        .progress-bar {{
            background: var(--success);
            height: 100%;
            text-align: right;
            padding-right: 10px;
            color: white;
            font-size: 12px;
            line-height: 20px;
            font-weight: bold;
            transition: width 0.6s ease;
        }}
        
        /* Data Tables */
        .table-responsive {{
            overflow-x: auto;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background-color: #f1f3f5;
            font-weight: 600;
        }}
        
        /* Chart Placeholder styling */
        .chart-placeholder {{
            background: #e9ecef;
            border: 2px dashed var(--text-muted);
            border-radius: 8px;
            height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            font-weight: 500;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NotifyAI V4 Operational Report</h1>
            <div class="date">Report Context: {data.get('date', 'N/A')}</div>
        </div>

        <div class="metrics-grid">
            <div class="card">
                <div class="card-title">Monitored Articles</div>
                <div class="card-value">{data.get('articles', 0)}</div>
            </div>
            <div class="card">
                <div class="card-title">Total Notifications</div>
                <div class="card-value">{data.get('notifications', 0)}</div>
            </div>
            <div class="card">
                <div class="card-title">New Notifications</div>
                <div class="card-value" style="color: var(--primary);">{data.get('new_notifications', 0)}</div>
            </div>
            <div class="card">
                <div class="card-title">Dispatched Telegrams</div>
                <div class="card-value" style="color: var(--success);">{data.get('telegram_sent', 0)}</div>
            </div>
        </div>

        <div class="card progress-section">
            <div class="card-title">System Scan Accuracy & Health Rate</div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {success_rate}%;">{success_rate}%</div>
            </div>
        </div>

        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Operational Metric</th>
                        <th>Value Output</th>
                        <th>Classification Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Successful Crawling Events</td>
                        <td>{data.get('successful_scans', 0)}</td>
                        <td style="color: var(--success); font-weight:600;">Optimal</td>
                    </tr>
                    <tr>
                        <td>Failed Execution Cycles</td>
                        <td>{data.get('failed_scans', 0)}</td>
                        <td style="color: { 'var(--danger)' if data.get('failed_scans', 0) > 0 else 'var(--text-muted)' }; font-weight:600;">
                            { 'Requires Review' if data.get('failed_scans', 0) > 0 else 'Nominal' }
                        </td>
                    </tr>
                    <tr>
                        <td>Identified Duplicates (Skipped)</td>
                        <td>{data.get('duplicates', 0)}</td>
                        <td style="color: var(--text-muted);">Cached</td>
                    </tr>
                    <tr>
                        <td>Total System Execution Runtime</td>
                        <td>{data.get('runtime', 0.0)}s</td>
                        <td style="color: var(--primary);">Active Processing</td>
                    </tr>
                    <tr>
                        <td>Mean Processing Cost (Per Scan)</td>
                        <td>{data.get('average_scan_time', 0.0)}s</td>
                        <td style="color: var(--primary);">Performance Target</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <div class="card-title">Analytics Engine Distribution Visualization</div>
            <div class="chart-placeholder">
                [Intelligent Data Graphic Placeholder: Processing Time vs Content Density Matrix Visualization Area]
            </div>
        </div>
    </div>
</body>
</html>
"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_template)
            return filepath
        except Exception as e:
            logger.error(f"Failed to generate dashboard style HTML report: {e}")
            raise