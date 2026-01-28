#!/usr/bin/env python3
"""
Main Update Script
==================
Run by GitHub Actions every 15 minutes (or 30 if auto-reduced).
Fetches data, calculates compass, saves JSON, and runs growth monitor.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources.fetcher import fetch_all_prices
from calculations.rrg import calculate_compass
from monitor import GrowthMonitor
from config import SHOW_PRICES, SHOW_PERCENTAGES


def main():
    print("=" * 60)
    print("COMMODITIES TRACKER - DATA UPDATE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize monitor
    monitor = GrowthMonitor(data_dir=str(Path(__file__).parent.parent / 'data'))
    
    # Get current display settings (may have been auto-adjusted)
    display_settings = monitor.get_display_settings()
    
    # Step 1: Fetch prices
    print("\n[1/3] Fetching price data...")
    try:
        prices_df = fetch_all_prices('1y')
        monitor.record_api_call(success=True)
    except Exception as e:
        print(f"ERROR fetching prices: {e}")
        monitor.record_api_call(success=False)
        sys.exit(1)
    
    if len(prices_df.columns) < 10:
        print(f"ERROR: Only got {len(prices_df.columns)} commodities, need at least 10")
        sys.exit(1)
    
    # Step 2: Calculate Momentum Compass
    print("\n[2/3] Calculating Momentum Compass (percentile rank method)...")
    try:
        compass_data = calculate_compass(prices_df, tail_length=5)
    except Exception as e:
        print(f"ERROR calculating compass: {e}")
        sys.exit(1)
    
    # Term structure disabled - free data sources unreliable
    # Will re-enable when we have a reliable data source
    compass_data['term_structure'] = {
        'status': 'coming_soon',
        'message': 'Term structure analysis coming soon'
    }
    
    # Step 3: Add display settings to output
    print("\n[3/3] Applying display settings and saving...")
    compass_data['display_settings'] = {
        'show_prices': display_settings['show_prices'],
        'show_percentages': display_settings['show_percentages'],
    }
    
    # If prices should be hidden, remove them from output
    if not display_settings['show_prices']:
        print("  → Prices hidden (threshold exceeded)")
        for commodity in compass_data['commodities']:
            del commodity['price']
            del commodity['price_change']
    
    if not display_settings['show_percentages']:
        print("  → Percentages hidden (threshold exceeded)")
        for commodity in compass_data['commodities']:
            if 'price_change_pct' in commodity:
                del commodity['price_change_pct']
    
    # Save to JSON
    output_dir = Path(__file__).parent.parent / 'public'
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'compass.json'
    
    with open(output_file, 'w') as f:
        json.dump(compass_data, f, indent=2)
    
    print(f"Saved to: {output_file}")
    
    # Run growth monitor check
    print("\n" + "-" * 60)
    print("GROWTH MONITOR CHECK")
    print("-" * 60)
    
    report = monitor.check_thresholds()
    
    print(f"  Daily visitors (avg): {report['metrics']['daily_visitors_avg']}")
    print(f"  API calls today: {report['metrics']['api_calls_today']}")
    print(f"  Error rate (7d): {report['metrics']['error_rate_7d']}%")
    print(f"  Levels: {report['levels']}")
    
    # Execute any auto-protection actions
    if report['actions']:
        print(f"\n  Auto-protection actions needed: {report['actions']}")
        executed = monitor.execute_actions(report['actions'])
        for action in executed:
            print(f"  ✓ Executed: {action['action']}")
    
    # Show alerts
    if report['alerts']:
        print(f"\n  Alerts:")
        for alert in report['alerts']:
            severity_icon = {'info': 'ℹ️', 'warning': '⚠️', 'critical': '🛑'}.get(alert['severity'], '')
            print(f"    {severity_icon} [{alert['severity']}] {alert['message']}")
    else:
        print(f"\n  ✓ No alerts - all systems normal")
    
    # Print summary
    print("\n" + "=" * 60)
    print("UPDATE COMPLETE")
    print("=" * 60)
    print(f"Commodities: {len(compass_data['commodities'])}")
    print(f"Data range: {compass_data['data_start'][:10]} to {compass_data['data_end'][:10]}")
    print(f"Method: {compass_data['parameters']['normalization']}")
    
    print(f"\nQuadrant distribution:")
    for quadrant, count in compass_data['summary'].items():
        print(f"  {quadrant.capitalize():12}: {count}")
    
    print(f"\nDisplay settings:")
    print(f"  Show prices: {display_settings['show_prices']}")
    print(f"  Show percentages: {display_settings['show_percentages']}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
