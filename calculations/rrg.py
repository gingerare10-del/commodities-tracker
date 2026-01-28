"""
RRG Calculator with Percentile Rank Normalization
==================================================
Computes Momentum Compass using distribution-free percentile ranks.
This handles fat-tailed commodity returns without assuming normality.

Statistical Method:
- RS (Relative Strength) = Asset price / Benchmark price
- RS-Ratio = Percentile rank of smoothed RS (0-100 scale, 50 = median)
- RS-Momentum = Percentile rank of RS-Ratio rate of change

Display:
- Rescaled to center at 100 (so 100 = average, >100 = above average)
- Human-readable labels derived from percentile position

User-Facing Labels:
- Strength: "Very Strong", "Strong", "Neutral", "Weak", "Very Weak"
- Momentum: "Accelerating", "Steady", "Fading"
"""

import pandas as pd
import numpy as np
from scipy import stats
from config import (
    COMMODITIES, 
    RS_RATIO_PERIOD, 
    RS_MOMENTUM_PERIOD,
    STRENGTH_LABELS,
    MOMENTUM_LABELS,
)


def calculate_compass(prices_df: pd.DataFrame, tail_length: int = 5) -> dict:
    """
    Calculate Momentum Compass coordinates for all commodities.
    
    Uses percentile rank normalization — distribution-free, handles fat tails.
    
    Args:
        prices_df: DataFrame with dates as index, symbols as columns
        tail_length: Number of historical points for the "tail" trail
    
    Returns:
        Dict with compass data ready for JSON export
    """
    
    min_days = RS_RATIO_PERIOD + RS_MOMENTUM_PERIOD + tail_length
    if len(prices_df) < min_days:
        raise ValueError(f"Need at least {min_days} days of data, got {len(prices_df)}")
    
    # =========================================================================
    # STEP 1: Normalize all prices to starting point = 100
    # =========================================================================
    normalized = prices_df / prices_df.iloc[0] * 100
    
    # =========================================================================
    # STEP 2: Create equal-weight benchmark (geometric mean)
    # =========================================================================
    log_prices = np.log(normalized)
    benchmark_log = log_prices.mean(axis=1)
    benchmark = np.exp(benchmark_log) * 100 / np.exp(benchmark_log.iloc[0])
    
    # =========================================================================
    # STEP 3: Calculate Relative Strength (RS) for each asset
    # =========================================================================
    rs = normalized.div(benchmark, axis=0)
    
    # =========================================================================
    # STEP 4: Calculate RS-Ratio using percentile ranks
    # =========================================================================
    # Smooth the RS first
    rs_smoothed = rs.rolling(RS_RATIO_PERIOD).mean()
    
    # Calculate percentile rank over available history for each asset
    # This gives us "what % of historical values are below current value"
    def rolling_percentile_rank(series, window=None):
        """Calculate rolling percentile rank (0-100)
        
        If window is None, use all available history (expanding window).
        """
        result = pd.Series(index=series.index, dtype=float)
        min_periods = 50  # Minimum data points needed for meaningful percentile
        
        for i in range(min_periods, len(series)):
            if window is None:
                # Expanding window - use all history up to this point
                window_data = series.iloc[:i]
            else:
                # Fixed rolling window
                start = max(0, i - window)
                window_data = series.iloc[start:i]
            
            current = series.iloc[i]
            # Percentile rank: % of values below current
            rank = (window_data < current).sum() / len(window_data) * 100
            result.iloc[i] = rank
        return result
    
    # Apply percentile ranking to smoothed RS (use expanding window)
    rs_ratio_pct = pd.DataFrame(index=rs_smoothed.index, columns=rs_smoothed.columns)
    for col in rs_smoothed.columns:
        rs_ratio_pct[col] = rolling_percentile_rank(rs_smoothed[col], window=None)
    
    # Rescale: 50th percentile -> 100, so range is roughly 50-150
    rs_ratio_display = rs_ratio_pct + 50  # Now 0th pct = 50, 50th pct = 100, 100th pct = 150
    
    # =========================================================================
    # STEP 5: Calculate RS-Momentum using percentile ranks
    # =========================================================================
    # Rate of change of the smoothed RS
    rs_roc = rs_smoothed.pct_change(periods=RS_MOMENTUM_PERIOD) * 100
    
    # Percentile rank the rate of change (use expanding window)
    rs_momentum_pct = pd.DataFrame(index=rs_roc.index, columns=rs_roc.columns)
    for col in rs_roc.columns:
        rs_momentum_pct[col] = rolling_percentile_rank(rs_roc[col], window=None)
    
    # Rescale to center at 100
    rs_momentum_display = rs_momentum_pct + 50
    
    # =========================================================================
    # STEP 6: Build output structure
    # =========================================================================
    commodities_data = []
    
    for symbol in prices_df.columns:
        if symbol not in COMMODITIES:
            continue
            
        info = COMMODITIES[symbol]
        
        # Get current percentile ranks (0-100 scale)
        current_ratio_pct = rs_ratio_pct[symbol].iloc[-1]
        current_momentum_pct = rs_momentum_pct[symbol].iloc[-1]
        
        # Get display values (for chart, centered at 100)
        current_ratio_display = rs_ratio_display[symbol].iloc[-1]
        current_momentum_display = rs_momentum_display[symbol].iloc[-1]
        
        # Skip if NaN
        if pd.isna(current_ratio_pct) or pd.isna(current_momentum_pct):
            continue
        
        # Determine quadrant (based on 50th percentile = neutral)
        # >50th percentile = above average
        if current_ratio_pct >= 50 and current_momentum_pct >= 50:
            quadrant = 'leading'
        elif current_ratio_pct >= 50 and current_momentum_pct < 50:
            quadrant = 'weakening'
        elif current_ratio_pct < 50 and current_momentum_pct < 50:
            quadrant = 'lagging'
        else:
            quadrant = 'improving'
        
        # Convert percentiles to human-readable labels
        strength_label = _percentile_to_strength_label(current_ratio_pct)
        momentum_label = _percentile_to_momentum_label(current_momentum_pct)
        
        # Get tail (historical trail for chart)
        tail = []
        for i in range(tail_length, 0, -1):
            idx = -i
            if abs(idx) <= len(rs_ratio_display):
                ratio = rs_ratio_display[symbol].iloc[idx]
                momentum = rs_momentum_display[symbol].iloc[idx]
                if not pd.isna(ratio) and not pd.isna(momentum):
                    tail.append({
                        'x': round(float(ratio), 1),
                        'y': round(float(momentum), 1)
                    })
        
        # Get price info
        current_price = prices_df[symbol].iloc[-1]
        prev_price = prices_df[symbol].iloc[-2]
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100
        
        commodities_data.append({
            'symbol': symbol,
            'name': info['name'],
            'short': info.get('short', info['name']),
            'category': info['category'],
            'quadrant': quadrant,
            
            # Chart coordinates (display values centered at 100)
            'x': round(float(current_ratio_display), 1),
            'y': round(float(current_momentum_display), 1),
            'tail': tail,
            
            # Percentile values (0-100, 50 = median)
            'pct_ratio': round(float(current_ratio_pct), 1),
            'pct_momentum': round(float(current_momentum_pct), 1),
            
            # Human-readable labels
            'strength_label': strength_label,
            'momentum_label': momentum_label,
            
            # Price data (can be hidden by frontend based on settings)
            'price': round(float(current_price), 2),
            'price_change': round(float(price_change), 2),
            'price_change_pct': round(float(price_change_pct), 2),
        })
    
    # Sort by quadrant then by strength
    quadrant_order = {'leading': 0, 'weakening': 1, 'lagging': 2, 'improving': 3}
    commodities_data.sort(key=lambda x: (quadrant_order[x['quadrant']], -x['pct_ratio']))
    
    # Summary stats
    quadrant_counts = {
        'leading': len([c for c in commodities_data if c['quadrant'] == 'leading']),
        'weakening': len([c for c in commodities_data if c['quadrant'] == 'weakening']),
        'lagging': len([c for c in commodities_data if c['quadrant'] == 'lagging']),
        'improving': len([c for c in commodities_data if c['quadrant'] == 'improving']),
    }
    
    return {
        'generated_at': pd.Timestamp.now().isoformat(),
        'data_start': prices_df.index[0].isoformat(),
        'data_end': prices_df.index[-1].isoformat(),
        'trading_days': len(prices_df),
        'parameters': {
            'rs_ratio_period': RS_RATIO_PERIOD,
            'rs_momentum_period': RS_MOMENTUM_PERIOD,
            'tail_length': tail_length,
            'normalization': 'percentile_rank',
        },
        'summary': quadrant_counts,
        'commodities': commodities_data,
    }


def _percentile_to_strength_label(pct: float) -> str:
    """Convert percentile rank (0-100) to strength label."""
    if pct >= 80:
        return 'very_strong'
    elif pct >= 60:
        return 'strong'
    elif pct >= 40:
        return 'neutral'
    elif pct >= 20:
        return 'weak'
    else:
        return 'very_weak'


def _percentile_to_momentum_label(pct: float) -> str:
    """Convert percentile rank (0-100) to momentum label."""
    if pct >= 60:
        return 'accelerating'
    elif pct >= 40:
        return 'steady'
    else:
        return 'fading'


def get_strength_description(label: str) -> str:
    """Get human-readable description for strength label."""
    descriptions = {
        'very_strong': 'Significantly outperforming (top 10%)',
        'strong': 'Outperforming the average',
        'neutral': 'Performing around average',
        'weak': 'Underperforming the average',
        'very_weak': 'Significantly underperforming (bottom 10%)',
    }
    return descriptions.get(label, '')


def get_momentum_description(label: str) -> str:
    """Get human-readable description for momentum label."""
    descriptions = {
        'accelerating': 'Relative performance improving',
        'steady': 'Relative performance stable',
        'fading': 'Relative performance declining',
    }
    return descriptions.get(label, '')


if __name__ == '__main__':
    # Test with real data
    import sys
    sys.path.insert(0, '..')
    from data_sources.fetcher import fetch_all_prices
    
    print("=" * 60)
    print("Testing RRG Calculator with Z-Scores")
    print("=" * 60)
    
    prices = fetch_all_prices('1y')
    compass = calculate_compass(prices)
    
    print(f"\nGenerated at: {compass['generated_at']}")
    print(f"Data range: {compass['data_start'][:10]} to {compass['data_end'][:10]}")
    print(f"Trading days: {compass['trading_days']}")
    print(f"Normalization: {compass['parameters']['normalization']}")
    
    print(f"\nQuadrant summary:")
    for q, count in compass['summary'].items():
        print(f"  {q.capitalize():12}: {count}")
    
    print(f"\nCommodities (with Z-scores and labels):")
    print("-" * 80)
    print(f"{'Name':<18} {'Quadrant':<12} {'Z-Ratio':>8} {'Z-Mom':>8} {'Strength':<12} {'Momentum':<12}")
    print("-" * 80)
    
    for c in compass['commodities']:
        print(f"{c['name']:<18} {c['quadrant']:<12} {c['z_ratio']:>8.2f} {c['z_momentum']:>8.2f} {c['strength_label']:<12} {c['momentum_label']:<12}")
