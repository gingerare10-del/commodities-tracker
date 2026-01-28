"""
Growth Monitor
==============
Tracks usage metrics, checks thresholds, triggers alerts and auto-protection.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config import THRESHOLDS, AUTO_PROTECTION, ALERTS, UPGRADE_OPTIONS


class GrowthMonitor:
    """
    Monitors growth metrics and takes protective actions when needed.
    """
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.metrics_file = self.data_dir / 'metrics.json'
        self.status_file = self.data_dir / 'status.json'
        self.alerts_file = self.data_dir / 'alerts.json'
        
    def load_metrics(self) -> dict:
        """Load historical metrics."""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                return json.load(f)
        return {
            'daily': {},
            'api_calls': {},
            'errors': {},
        }
    
    def save_metrics(self, metrics: dict):
        """Save metrics to file."""
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    def load_status(self) -> dict:
        """Load current status."""
        if self.status_file.exists():
            with open(self.status_file) as f:
                return json.load(f)
        return {
            'show_prices': True,
            'show_percentages': True,
            'update_interval': AUTO_PROTECTION['default_update_interval'],
            'last_check': None,
            'alerts_sent': [],
            'actions_taken': [],
        }
    
    def save_status(self, status: dict):
        """Save status to file."""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def record_visitors(self, count: int, date: Optional[str] = None):
        """Record daily visitor count."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        metrics = self.load_metrics()
        metrics['daily'][date] = count
        self.save_metrics(metrics)
    
    def record_api_call(self, success: bool = True, date: Optional[str] = None):
        """Record an API call."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        metrics = self.load_metrics()
        
        if date not in metrics['api_calls']:
            metrics['api_calls'][date] = {'success': 0, 'error': 0}
        
        if success:
            metrics['api_calls'][date]['success'] += 1
        else:
            metrics['api_calls'][date]['error'] += 1
        
        self.save_metrics(metrics)
    
    def get_daily_average(self, days: int = 7) -> float:
        """Get average daily visitors over past N days."""
        metrics = self.load_metrics()
        
        recent = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in metrics['daily']:
                recent.append(metrics['daily'][date])
        
        if not recent:
            return 0
        return sum(recent) / len(recent)
    
    def get_api_calls_today(self) -> int:
        """Get total API calls today."""
        metrics = self.load_metrics()
        today = datetime.now().strftime('%Y-%m-%d')
        
        if today in metrics['api_calls']:
            calls = metrics['api_calls'][today]
            return calls['success'] + calls['error']
        return 0
    
    def get_error_rate(self, days: int = 7) -> float:
        """Get error rate over past N days."""
        metrics = self.load_metrics()
        
        total_success = 0
        total_error = 0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in metrics['api_calls']:
                total_success += metrics['api_calls'][date]['success']
                total_error += metrics['api_calls'][date]['error']
        
        total = total_success + total_error
        if total == 0:
            return 0
        return total_error / total
    
    def check_thresholds(self) -> dict:
        """
        Check all thresholds and return status report.
        Returns dict with current levels and any actions needed.
        """
        daily_avg = self.get_daily_average()
        api_calls = self.get_api_calls_today()
        error_rate = self.get_error_rate()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'daily_visitors_avg': round(daily_avg, 1),
                'api_calls_today': api_calls,
                'error_rate_7d': round(error_rate * 100, 2),
            },
            'levels': {
                'visitors': self._get_level(daily_avg, 'visitors'),
                'api_calls': self._get_level(api_calls, 'api_calls'),
                'errors': self._get_error_level(error_rate),
            },
            'alerts': [],
            'actions': [],
        }
        
        # Check visitor thresholds
        if daily_avg >= THRESHOLDS['visitors_critical']:
            report['alerts'].append({
                'type': 'visitors_critical',
                'message': f'Critical: {daily_avg:.0f} daily visitors exceeds safe threshold',
                'severity': 'critical',
            })
            if AUTO_PROTECTION['enabled']:
                report['actions'].append('hide_prices')
                report['actions'].append('hide_percentages')
        
        elif daily_avg >= THRESHOLDS['visitors_warning']:
            report['alerts'].append({
                'type': 'visitors_warning',
                'message': f'Warning: {daily_avg:.0f} daily visitors approaching threshold',
                'severity': 'warning',
            })
        
        elif daily_avg >= THRESHOLDS['visitors_attention']:
            report['alerts'].append({
                'type': 'visitors_attention',
                'message': f'Attention: {daily_avg:.0f} daily visitors - review your options',
                'severity': 'info',
            })
        
        elif daily_avg >= THRESHOLDS['visitors_notice']:
            report['alerts'].append({
                'type': 'visitors_notice',
                'message': f'Notice: {daily_avg:.0f} daily visitors - you\'re growing!',
                'severity': 'info',
            })
        
        # Check API thresholds
        if api_calls >= THRESHOLDS['api_calls_critical']:
            report['alerts'].append({
                'type': 'api_critical',
                'message': f'Critical: {api_calls} API calls today - approaching limit',
                'severity': 'critical',
            })
            if AUTO_PROTECTION['enabled']:
                report['actions'].append('reduce_frequency')
        
        elif api_calls >= THRESHOLDS['api_calls_warning']:
            report['alerts'].append({
                'type': 'api_warning',
                'message': f'Warning: {api_calls} API calls today',
                'severity': 'warning',
            })
        
        # Check error rate
        if error_rate >= THRESHOLDS['error_rate_critical']:
            report['alerts'].append({
                'type': 'errors_critical',
                'message': f'Critical: {error_rate*100:.1f}% error rate',
                'severity': 'critical',
            })
        
        elif error_rate >= THRESHOLDS['error_rate_warning']:
            report['alerts'].append({
                'type': 'errors_warning',
                'message': f'Warning: {error_rate*100:.1f}% error rate',
                'severity': 'warning',
            })
        
        return report
    
    def _get_level(self, value: float, metric_type: str) -> str:
        """Determine level (ok/notice/attention/warning/critical) for a metric."""
        if metric_type == 'visitors':
            if value >= THRESHOLDS['visitors_critical']:
                return 'critical'
            elif value >= THRESHOLDS['visitors_warning']:
                return 'warning'
            elif value >= THRESHOLDS['visitors_attention']:
                return 'attention'
            elif value >= THRESHOLDS['visitors_notice']:
                return 'notice'
            return 'ok'
        
        elif metric_type == 'api_calls':
            if value >= THRESHOLDS['api_calls_critical']:
                return 'critical'
            elif value >= THRESHOLDS['api_calls_warning']:
                return 'warning'
            elif value >= THRESHOLDS['api_calls_notice']:
                return 'notice'
            return 'ok'
        
        return 'ok'
    
    def _get_error_level(self, rate: float) -> str:
        """Determine level for error rate."""
        if rate >= THRESHOLDS['error_rate_critical']:
            return 'critical'
        elif rate >= THRESHOLDS['error_rate_warning']:
            return 'warning'
        return 'ok'
    
    def execute_actions(self, actions: list) -> list:
        """
        Execute protective actions and return what was done.
        """
        status = self.load_status()
        executed = []
        
        for action in actions:
            if action == 'hide_prices' and status['show_prices']:
                status['show_prices'] = False
                executed.append({
                    'action': 'hide_prices',
                    'timestamp': datetime.now().isoformat(),
                    'reason': UPGRADE_OPTIONS['prices_hidden']['reason'],
                })
            
            elif action == 'hide_percentages' and status['show_percentages']:
                status['show_percentages'] = False
                executed.append({
                    'action': 'hide_percentages',
                    'timestamp': datetime.now().isoformat(),
                    'reason': UPGRADE_OPTIONS['prices_hidden']['reason'],
                })
            
            elif action == 'reduce_frequency':
                if status['update_interval'] == AUTO_PROTECTION['default_update_interval']:
                    status['update_interval'] = AUTO_PROTECTION['reduced_update_interval']
                    executed.append({
                        'action': 'reduce_frequency',
                        'timestamp': datetime.now().isoformat(),
                        'reason': UPGRADE_OPTIONS['api_limit_approaching']['reason'],
                        'old_interval': AUTO_PROTECTION['default_update_interval'],
                        'new_interval': AUTO_PROTECTION['reduced_update_interval'],
                    })
        
        if executed:
            status['actions_taken'].extend(executed)
            status['last_check'] = datetime.now().isoformat()
            self.save_status(status)
        
        return executed
    
    def get_display_settings(self) -> dict:
        """
        Get current display settings (what to show/hide).
        This is what the frontend reads to decide what to display.
        """
        status = self.load_status()
        return {
            'show_prices': status.get('show_prices', True),
            'show_percentages': status.get('show_percentages', True),
            'update_interval': status.get('update_interval', AUTO_PROTECTION['default_update_interval']),
        }
    
    def generate_admin_report(self) -> dict:
        """
        Generate full admin report for the admin dashboard.
        """
        metrics = self.load_metrics()
        status = self.load_status()
        threshold_report = self.check_thresholds()
        
        # Calculate totals
        total_visitors = sum(metrics['daily'].values())
        total_api_calls = sum(
            d['success'] + d['error'] 
            for d in metrics['api_calls'].values()
        )
        total_errors = sum(
            d['error'] 
            for d in metrics['api_calls'].values()
        )
        
        return {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_visitors': total_visitors,
                'total_api_calls': total_api_calls,
                'total_errors': total_errors,
                'error_rate': round(total_errors / max(total_api_calls, 1) * 100, 2),
                'days_tracked': len(metrics['daily']),
            },
            'current': threshold_report['metrics'],
            'levels': threshold_report['levels'],
            'display_settings': {
                'show_prices': status.get('show_prices', True),
                'show_percentages': status.get('show_percentages', True),
                'update_interval': status.get('update_interval', 15),
            },
            'thresholds': THRESHOLDS,
            'alerts': threshold_report['alerts'],
            'actions_pending': threshold_report['actions'],
            'actions_taken': status.get('actions_taken', []),
            'upgrade_options': UPGRADE_OPTIONS,
        }
    
    def format_alert_email(self, alert_type: str, report: dict) -> dict:
        """
        Format an alert email.
        Returns dict with subject and body.
        """
        if alert_type == 'visitors_critical':
            return {
                'subject': '🛑 Commodities Tracker — Prices Auto-Hidden',
                'body': f"""
Your Commodities Tracker has crossed {THRESHOLDS['visitors_critical']} daily visitors.

AUTOMATIC ACTION TAKEN:
- Prices and percentages are now hidden
- Your site still works, showing relative strength labels instead

CURRENT METRICS:
- Daily visitors (avg): {report['metrics']['daily_visitors_avg']}
- API calls today: {report['metrics']['api_calls_today']}

TO RESTORE PRICES, choose one:

1. Twelve Data Pro ($99/month)
   → {UPGRADE_OPTIONS['prices_hidden']['options'][0]['url']}
   → Add API key, set SHOW_PRICES = True

2. Polygon.io ($29/month)  
   → {UPGRADE_OPTIONS['prices_hidden']['options'][1]['url']}
   
3. Keep prices hidden ($0)
   → No action needed, site works fine

Congrats on the growth!
                """.strip()
            }
        
        elif alert_type == 'visitors_attention':
            return {
                'subject': '📈 Commodities Tracker — Growth Alert',
                'body': f"""
Your Commodities Tracker is growing!

CURRENT METRICS:
- Daily visitors (avg): {report['metrics']['daily_visitors_avg']}
- API calls today: {report['metrics']['api_calls_today']}

STATUS: Still safe, but plan ahead.

UPCOMING THRESHOLDS:
- At {THRESHOLDS['visitors_warning']} visitors/day: Warning alert
- At {THRESHOLDS['visitors_critical']} visitors/day: Prices auto-hidden

OPTIONS (no action required yet):
1. Do nothing — you're fine for now
2. Get Twelve Data license ($99/mo) — removes all risk
3. Review your analytics and plan ahead

Keep it up!
                """.strip()
            }
        
        elif alert_type == 'api_critical':
            return {
                'subject': '⚠️ Commodities Tracker — API Limit Warning',
                'body': f"""
Your Commodities Tracker is approaching API limits.

CURRENT: {report['metrics']['api_calls_today']} calls today
LIMIT: ~800 calls/day on free tier

AUTOMATIC ACTION TAKEN:
- Update frequency reduced from 15min to 30min

TO RESTORE FULL FREQUENCY:
1. Twelve Data Pro ($99/month) — unlimited calls
2. Or keep reduced frequency (still works fine)
                """.strip()
            }
        
        return {
            'subject': 'Commodities Tracker — Alert',
            'body': f"Alert: {alert_type}\n\nMetrics: {report['metrics']}"
        }


def run_monitor():
    """
    Run the growth monitor check.
    Called by cron job after each data update.
    """
    monitor = GrowthMonitor()
    
    # Check thresholds
    report = monitor.check_thresholds()
    
    print(f"Growth Monitor Check - {report['timestamp']}")
    print(f"  Visitors (avg): {report['metrics']['daily_visitors_avg']}/day")
    print(f"  API calls: {report['metrics']['api_calls_today']} today")
    print(f"  Error rate: {report['metrics']['error_rate_7d']}%")
    print(f"  Levels: {report['levels']}")
    
    # Execute any needed actions
    if report['actions']:
        print(f"\n  Actions needed: {report['actions']}")
        executed = monitor.execute_actions(report['actions'])
        for action in executed:
            print(f"  ✓ Executed: {action['action']}")
    
    # Show alerts
    if report['alerts']:
        print(f"\n  Alerts:")
        for alert in report['alerts']:
            print(f"    [{alert['severity']}] {alert['message']}")
    
    return report


if __name__ == '__main__':
    # Test the monitor
    monitor = GrowthMonitor()
    
    # Simulate some data
    print("Simulating metrics...")
    monitor.record_visitors(50)
    for _ in range(100):
        monitor.record_api_call(success=True)
    for _ in range(5):
        monitor.record_api_call(success=False)
    
    # Run check
    print("\nRunning monitor check...")
    report = run_monitor()
    
    # Show admin report
    print("\n" + "="*50)
    print("ADMIN REPORT")
    print("="*50)
    admin = monitor.generate_admin_report()
    print(json.dumps(admin, indent=2))
