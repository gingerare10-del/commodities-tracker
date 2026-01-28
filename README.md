# Commodities Momentum Compass

A real-time commodities tracking dashboard using Relative Rotation Graph (RRG) methodology.

![Screenshot placeholder](screenshot.png)

## What It Does

Tracks 20 major commodities and plots them on a Momentum Compass showing:
- **Leading** (green): Strong trend + positive momentum — outperforming
- **Weakening** (yellow): Strong trend + fading momentum — may be rolling over
- **Lagging** (red): Weak trend + negative momentum — underperforming
- **Improving** (blue): Weak trend + building momentum — may be turning around

## Commodities Tracked

**Energy:** WTI Crude, Brent Crude, Natural Gas, Heating Oil  
**Precious Metals:** Gold, Silver, Platinum, Palladium  
**Industrial:** Copper  
**Grains:** Corn, Wheat, Soybeans, Soybean Oil, Soybean Meal  
**Softs:** Coffee, Sugar, Cocoa, Cotton  
**Livestock:** Live Cattle, Lean Hogs

## Tech Stack

- **Data:** Yahoo Finance (prices), EIA API (energy context), FRED (economic)
- **Calculation:** Python with pandas
- **Frontend:** Vanilla HTML/CSS/JS with Chart.js
- **Hosting:** Vercel (free tier)
- **Automation:** GitHub Actions (every 15 minutes during market hours)

## Local Development

### Prerequisites
- Python 3.9+
- pip

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/commodities-tracker.git
cd commodities-tracker

# Install dependencies
pip install -r requirements.txt

# Run the update script to generate data
python scripts/update.py

# Open the frontend
open public/index.html
```

## Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/commodities-tracker.git
git push -u origin main
```

### 2. Add EIA API Key as Secret

1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `EIA_API_KEY`
4. Value: Your EIA API key

### 3. Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Set these settings:
   - Framework Preset: Other
   - Root Directory: `public`
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
5. Click Deploy

### 4. Enable GitHub Actions

The workflow runs automatically. To test manually:
1. Go to Actions tab
2. Click "Update Commodities Data"
3. Click "Run workflow"

## Methodology

Uses the Relative Rotation Graph (RRG) methodology developed by Julius de Kempenaer:

1. **Normalize prices** — All commodities start at 100
2. **Create benchmark** — Equal-weight geometric average of all commodities
3. **Calculate RS-Ratio** — Smoothed relative strength (100-period)
4. **Calculate RS-Momentum** — Rate of change of RS-Ratio (35-period)
5. **Plot on compass** — x=RS-Ratio, y=RS-Momentum, center at (100, 100)

Commodities rotate clockwise through quadrants: Improving → Leading → Weakening → Lagging → Improving

## Disclaimer

Data delayed 15+ minutes. For informational and educational purposes only. Not investment advice. Past performance does not guarantee future results.

## License

MIT
