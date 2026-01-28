"""
Data Fetcher - Pulls commodity prices from Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import COMMODITIES


def fetch_all_prices(period: str = '1y') -> pd.DataFrame:
    """
    Fetch historical prices for all commodities.
    
    Args:
        period: How much history to fetch ('1y', '6mo', etc.)
    
    Returns:
        DataFrame with dates as index, commodity symbols as columns
    """
    print(f"Fetching {len(COMMODITIES)} commodities...")
    
    prices = {}
    failed = []
    
    for symbol, info in COMMODITIES.items():
        yahoo_symbol = info['yahoo']
        try:
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period)
            
            if len(hist) >= 100:  # Minimum needed for RRG calculation
                prices[symbol] = hist['Close']
                print(f"  ✓ {info['name']}: {len(hist)} days")
            else:
                print(f"  ✗ {info['name']}: only {len(hist)} days (need 100+)")
                failed.append(symbol)
        except Exception as e:
            print(f"  ✗ {info['name']}: {e}")
            failed.append(symbol)
    
    if failed:
        print(f"\nWarning: {len(failed)} commodities failed: {', '.join(failed)}")
    
    # Combine into DataFrame and align dates
    df = pd.DataFrame(prices)
    df = df.dropna()  # Only keep dates where all commodities have data
    
    print(f"\nTotal: {len(df)} aligned trading days for {len(df.columns)} commodities")
    
    return df


def fetch_latest_prices() -> dict:
    """
    Fetch just the latest price for each commodity.
    
    Returns:
        Dict of {symbol: {'price': float, 'change': float, 'change_pct': float}}
    """
    results = {}
    
    for symbol, info in COMMODITIES.items():
        yahoo_symbol = info['yahoo']
        try:
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period='5d')
            
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = current - previous
                change_pct = (change / previous) * 100
                
                results[symbol] = {
                    'price': round(current, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'name': info['name'],
                    'category': info['category'],
                }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    return results


def fetch_term_structure() -> dict:
    """
    Fetch term structure (contango/backwardation) for commodities.
    
    Methodology (validated by multiple AI reviewers):
    - Compare front-month vs next-month futures prices
    - Annualize the spread for proper comparison
    - Use 2% threshold for classification
    - Flag seasonal commodities
    
    Returns:
        Dict with term structure data and summary
    """
    
    # Contract tickers: (front_month, next_month, approx_days_between)
    # Updated for 2026 contracts
    term_contracts = {
        'CL': {
            'name': 'Crude Oil',
            'front': 'CL=F',
            'next': 'CLH26.NYM',
            'third': 'CLJ26.NYM',
            'days': 30,
            'seasonal': False,
        },
        'BZ': {
            'name': 'Brent Crude',
            'front': 'BZ=F',
            'next': 'BZH26.NYM',
            'third': 'BZJ26.NYM',
            'days': 30,
            'seasonal': False,
        },
        'NG': {
            'name': 'Natural Gas',
            'front': 'NG=F',
            'next': 'NGH26.NYM',
            'third': 'NGJ26.NYM',
            'days': 30,
            'seasonal': True,  # Strong seasonality
        },
        'HO': {
            'name': 'Heating Oil',
            'front': 'HO=F',
            'next': 'HOH26.NYM',
            'third': 'HOJ26.NYM',
            'days': 30,
            'seasonal': True,  # Winter demand
        },
        'GC': {
            'name': 'Gold',
            'front': 'GC=F',
            'next': 'GCJ26.CMX',
            'third': 'GCM26.CMX',
            'days': 60,  # Gold has bi-monthly contracts
            'seasonal': False,
        },
        'SI': {
            'name': 'Silver',
            'front': 'SI=F',
            'next': 'SIH26.CMX',
            'third': 'SIK26.CMX',
            'days': 30,
            'seasonal': False,
        },
        'HG': {
            'name': 'Copper',
            'front': 'HG=F',
            'next': 'HGH26.CMX',
            'third': 'HGK26.CMX',
            'days': 30,
            'seasonal': False,
        },
        'ZC': {
            'name': 'Corn',
            'front': 'ZC=F',
            'next': 'ZCH26.CBT',
            'third': 'ZCK26.CBT',
            'days': 30,
            'seasonal': True,  # Harvest cycle
        },
        'ZW': {
            'name': 'Wheat',
            'front': 'ZW=F',
            'next': 'ZWH26.CBT',
            'third': 'ZWK26.CBT',
            'days': 30,
            'seasonal': True,  # Harvest cycle
        },
        'ZS': {
            'name': 'Soybeans',
            'front': 'ZS=F',
            'next': 'ZSH26.CBT',
            'third': 'ZSK26.CBT',
            'days': 30,
            'seasonal': True,  # Harvest cycle
        },
        'KC': {
            'name': 'Coffee',
            'front': 'KC=F',
            'next': 'KCH26.NYB',
            'third': 'KCK26.NYB',
            'days': 30,
            'seasonal': False,
        },
        'SB': {
            'name': 'Sugar',
            'front': 'SB=F',
            'next': 'SBH26.NYB',
            'third': 'SBK26.NYB',
            'days': 30,
            'seasonal': False,
        },
        'CC': {
            'name': 'Cocoa',
            'front': 'CC=F',
            'next': 'CCH26.NYB',
            'third': 'CCK26.NYB',
            'days': 30,
            'seasonal': False,
        },
    }
    
    results = {}
    summary = {'contango': 0, 'backwardation': 0, 'flat': 0}
    
    print("\nFetching term structure...")
    
    for symbol, config in term_contracts.items():
        try:
            # Fetch front and next month prices
            front_data = yf.Ticker(config['front']).history(period='5d')
            next_data = yf.Ticker(config['next']).history(period='5d')
            
            if len(front_data) == 0 or len(next_data) == 0:
                print(f"  ✗ {config['name']}: Missing data")
                continue
            
            front_price = front_data['Close'].iloc[-1]
            next_price = next_data['Close'].iloc[-1]
            days_between = config['days']
            
            # Calculate raw spread
            raw_spread = ((next_price - front_price) / front_price) * 100
            
            # Annualize the spread
            annualized_spread = ((next_price / front_price) ** (365 / days_between) - 1) * 100
            
            # Classify with 2% threshold (validated)
            if annualized_spread > 2.0:
                structure = 'contango'
            elif annualized_spread < -2.0:
                structure = 'backwardation'
            else:
                structure = 'flat'
            
            summary[structure] += 1
            
            results[symbol] = {
                'name': config['name'],
                'structure': structure,
                'spread_raw': round(raw_spread, 2),
                'spread_annualized': round(annualized_spread, 2),
                'front_price': round(front_price, 2),
                'next_price': round(next_price, 2),
                'front_contract': config['front'],
                'next_contract': config['next'],
                'seasonal': config['seasonal'],
            }
            
            # Visual indicator
            indicator = '↗' if structure == 'contango' else '↘' if structure == 'backwardation' else '→'
            seasonal_flag = ' ⚠️' if config['seasonal'] else ''
            print(f"  {indicator} {config['name']}: {structure.upper()} ({annualized_spread:+.1f}% ann.){seasonal_flag}")
            
        except Exception as e:
            print(f"  ✗ {config['name']}: Error - {str(e)[:30]}")
    
    print(f"\nTerm Structure Summary:")
    print(f"  Contango: {summary['contango']} | Backwardation: {summary['backwardation']} | Flat: {summary['flat']}")
    
    return {
        'commodities': results,
        'summary': summary,
        'methodology': {
            'comparison': 'Front month vs Next month futures',
            'threshold': '±2% annualized',
            'note': 'Seasonal commodities flagged (NG, HO, grains)',
        }
    }


if __name__ == '__main__':
    # Test the fetcher
    print("=" * 50)
    print("Testing Data Fetcher")
    print("=" * 50)
    
    df = fetch_all_prices('1y')
    print(f"\nShape: {df.shape}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"\nLast row:\n{df.iloc[-1]}")
