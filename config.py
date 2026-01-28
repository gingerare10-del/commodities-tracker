"""
Commodities Tracker - Configuration
====================================
This file controls everything: display settings, thresholds, and auto-protection.
"""

import os

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================
# These can be toggled manually OR automatically by the growth monitor

SHOW_PRICES = True              # Show actual prices ($2,847.30)
SHOW_PERCENTAGES = True         # Show percentage changes (+1.2%)
SHOW_DETAILED_METRICS = True    # Show RS-Ratio, RS-Momentum numbers

# When prices are hidden, show these instead:
# "Strong", "Weak", "Accelerating", "Fading"


# =============================================================================
# API KEYS (Use environment variables in production)
# =============================================================================
EIA_API_KEY = os.getenv('EIA_API_KEY', 'cBzUOwDAWEFeo5XEZDz9dU13HE3KL742mtuoQ0lI')

# Future paid upgrades (empty until you need them)
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', '')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')


# =============================================================================
# GROWTH THRESHOLDS
# =============================================================================
# The system monitors these and alerts/acts when crossed

THRESHOLDS = {
    # Visitor thresholds (daily average)
    'visitors_notice': 100,       # "You're growing!"
    'visitors_attention': 1000,   # "Review your options"
    'visitors_warning': 5000,     # "Decision time approaching"
    'visitors_critical': 10000,   # Auto-hide prices
    
    # API call thresholds (daily)
    'api_calls_notice': 300,      # 40% of typical free tier
    'api_calls_warning': 600,     # 75% of typical free tier
    'api_calls_critical': 800,    # 95% - approaching limit
    
    # Error rate thresholds
    'error_rate_warning': 0.05,   # 5% errors
    'error_rate_critical': 0.15,  # 15% errors
}


# =============================================================================
# AUTO-PROTECTION SETTINGS
# =============================================================================
# What happens automatically when thresholds are crossed

AUTO_PROTECTION = {
    'enabled': True,
    
    # Automatically hide prices at this visitor count
    'auto_hide_prices_at': 10000,
    
    # Automatically hide percentages at this visitor count  
    'auto_hide_percentages_at': 10000,
    
    # Reduce API call frequency when approaching limits
    'auto_reduce_frequency_at': 600,  # API calls/day
    
    # Update interval in minutes (can be auto-adjusted)
    'default_update_interval': 15,
    'reduced_update_interval': 30,
}


# =============================================================================
# ALERT SETTINGS
# =============================================================================
ALERTS = {
    'enabled': True,
    'email': os.getenv('ALERT_EMAIL', ''),  # Set your email
    
    # Which events trigger emails
    'on_threshold_crossed': True,
    'on_auto_action_taken': True,
    'on_error_spike': True,
    'daily_summary': False,  # Set True for daily status emails
}


# =============================================================================
# UPGRADE PATHS
# =============================================================================
# Information shown to you when action is needed

UPGRADE_OPTIONS = {
    'prices_hidden': {
        'reason': 'Traffic exceeded safe threshold for displaying prices without a data license',
        'action_taken': 'Prices and percentages are now hidden automatically',
        'options': [
            {
                'name': 'Twelve Data Pro',
                'cost': '$99/month',
                'url': 'https://twelvedata.com/pricing',
                'benefit': 'Real-time data, commercial license, restore all features',
            },
            {
                'name': 'Polygon.io Starter',
                'cost': '$29/month', 
                'url': 'https://polygon.io/pricing',
                'benefit': 'Delayed data, commercial license, restore all features',
            },
            {
                'name': 'Keep prices hidden',
                'cost': '$0',
                'url': None,
                'benefit': 'Site still works, shows relative strength labels instead',
            },
        ]
    },
    'api_limit_approaching': {
        'reason': 'Approaching free tier API limits',
        'action_taken': 'Update frequency reduced to stay within limits',
        'options': [
            {
                'name': 'Twelve Data Pro',
                'cost': '$99/month',
                'url': 'https://twelvedata.com/pricing',
                'benefit': '610 API calls/minute, no limits',
            },
            {
                'name': 'Keep reduced frequency',
                'cost': '$0',
                'url': None,
                'benefit': 'Updates every 30min instead of 15min',
            },
        ]
    },
    'data_source_unstable': {
        'reason': 'Yahoo Finance is returning errors frequently',
        'action_taken': 'None - monitoring',
        'options': [
            {
                'name': 'Switch to Twelve Data',
                'cost': '$99/month',
                'url': 'https://twelvedata.com/pricing',
                'benefit': 'Reliable official API',
            },
            {
                'name': 'Wait it out',
                'cost': '$0',
                'url': None,
                'benefit': 'Yahoo usually recovers within hours',
            },
        ]
    },
}


# =============================================================================
# RRG CALCULATION PARAMETERS
# =============================================================================
RS_RATIO_PERIOD = 100       # Standard: 100-period smoothing
RS_MOMENTUM_PERIOD = 35     # Standard: 35-period rate of change
TAIL_LENGTH = 5             # Number of historical points to show


# =============================================================================
# COMMODITIES TO TRACK
# =============================================================================
COMMODITIES = {
    # === ENERGY ===
    'CL': {
        'name': 'WTI Crude Oil',
        'short': 'Crude',
        'yahoo': 'CL=F',
        'category': 'energy',
    },
    'BZ': {
        'name': 'Brent Crude',
        'short': 'Brent',
        'yahoo': 'BZ=F',
        'category': 'energy',
    },
    'NG': {
        'name': 'Natural Gas',
        'short': 'NatGas',
        'yahoo': 'NG=F',
        'category': 'energy',
    },
    'HO': {
        'name': 'Heating Oil',
        'short': 'Heat',
        'yahoo': 'HO=F',
        'category': 'energy',
    },
    
    # === PRECIOUS METALS ===
    'GC': {
        'name': 'Gold',
        'short': 'Gold',
        'yahoo': 'GC=F',
        'category': 'precious_metals',
    },
    'SI': {
        'name': 'Silver',
        'short': 'Silver',
        'yahoo': 'SI=F',
        'category': 'precious_metals',
    },
    'PL': {
        'name': 'Platinum',
        'short': 'Plat',
        'yahoo': 'PL=F',
        'category': 'precious_metals',
    },
    'PA': {
        'name': 'Palladium',
        'short': 'Pallad',
        'yahoo': 'PA=F',
        'category': 'precious_metals',
    },
    
    # === INDUSTRIAL METALS ===
    'HG': {
        'name': 'Copper',
        'short': 'Copper',
        'yahoo': 'HG=F',
        'category': 'industrial',
    },
    
    # === GRAINS ===
    'ZC': {
        'name': 'Corn',
        'short': 'Corn',
        'yahoo': 'ZC=F',
        'category': 'grains',
    },
    'ZW': {
        'name': 'Wheat',
        'short': 'Wheat',
        'yahoo': 'ZW=F',
        'category': 'grains',
    },
    'ZS': {
        'name': 'Soybeans',
        'short': 'Soy',
        'yahoo': 'ZS=F',
        'category': 'grains',
    },
    'ZL': {
        'name': 'Soybean Oil',
        'short': 'SoyOil',
        'yahoo': 'ZL=F',
        'category': 'grains',
    },
    'ZM': {
        'name': 'Soybean Meal',
        'short': 'SoyMeal',
        'yahoo': 'ZM=F',
        'category': 'grains',
    },
    
    # === SOFTS ===
    'KC': {
        'name': 'Coffee',
        'short': 'Coffee',
        'yahoo': 'KC=F',
        'category': 'softs',
    },
    'SB': {
        'name': 'Sugar',
        'short': 'Sugar',
        'yahoo': 'SB=F',
        'category': 'softs',
    },
    'CC': {
        'name': 'Cocoa',
        'short': 'Cocoa',
        'yahoo': 'CC=F',
        'category': 'softs',
    },
    'CT': {
        'name': 'Cotton',
        'short': 'Cotton',
        'yahoo': 'CT=F',
        'category': 'softs',
    },
    
    # === LIVESTOCK ===
    'LE': {
        'name': 'Live Cattle',
        'short': 'Cattle',
        'yahoo': 'LE=F',
        'category': 'livestock',
    },
    'HE': {
        'name': 'Lean Hogs',
        'short': 'Hogs',
        'yahoo': 'HE=F',
        'category': 'livestock',
    },
}


# =============================================================================
# UI SETTINGS
# =============================================================================
CATEGORY_COLORS = {
    'energy': '#f97316',
    'precious_metals': '#fbbf24',
    'industrial': '#a855f7',
    'grains': '#22c55e',
    'softs': '#ec4899',
    'livestock': '#06b6d4',
}

CATEGORY_NAMES = {
    'energy': 'Energy',
    'precious_metals': 'Precious Metals',
    'industrial': 'Industrial',
    'grains': 'Grains',
    'softs': 'Softs',
    'livestock': 'Livestock',
}

# Strength labels (used when prices are hidden)
STRENGTH_LABELS = {
    'very_strong': 'Very Strong',
    'strong': 'Strong',
    'neutral': 'Neutral',
    'weak': 'Weak',
    'very_weak': 'Very Weak',
}

MOMENTUM_LABELS = {
    'accelerating': 'Accelerating',
    'steady': 'Steady',
    'fading': 'Fading',
}
