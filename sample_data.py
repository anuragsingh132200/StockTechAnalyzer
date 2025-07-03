"""
Sample data generator for demonstration purposes
This file creates a sample parquet file if the original is not available
"""

import polars as pl
import random
import numpy as np
from datetime import date, timedelta
import os

def create_sample_parquet_data():
    """Create sample OHLC data and save as parquet"""
    
    # Stock symbols
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "JPM", "JNJ", "V"]
    
    # Date range (3 years)
    start_date = date.today() - timedelta(days=1095)
    dates = []
    
    # Generate weekday dates only
    for i in range(1095):
        current_date = start_date + timedelta(days=i)
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            dates.append(current_date)
    
    # Generate data
    data_rows = []
    
    for symbol in symbols:
        # Starting price for each symbol
        base_prices = {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
            "MSFT": 330.0,
            "TSLA": 200.0,
            "AMZN": 3300.0,
            "META": 350.0,
            "NVDA": 250.0,
            "JPM": 140.0,
            "JNJ": 160.0,
            "V": 220.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        for i, date_val in enumerate(dates):
            # Generate realistic price movements
            if i == 0:
                open_price = base_price
            else:
                # Get previous close
                prev_close = data_rows[-1]['close'] if data_rows and data_rows[-1]['symbol'] == symbol else base_price
                
                # Add some trend and volatility
                trend = random.uniform(-0.002, 0.003)  # Slight upward bias
                volatility = random.uniform(-0.05, 0.05)  # Daily volatility
                
                price_change = prev_close * (trend + volatility)
                open_price = max(prev_close + price_change, 1.0)
            
            # Generate OHLC
            daily_volatility = random.uniform(0.01, 0.04)
            high_multiplier = 1 + random.uniform(0, daily_volatility)
            low_multiplier = 1 - random.uniform(0, daily_volatility)
            
            close_change = random.uniform(-daily_volatility/2, daily_volatility/2)
            close_price = max(open_price * (1 + close_change), 1.0)
            
            high_price = max(open_price, close_price) * high_multiplier
            low_price = min(open_price, close_price) * low_multiplier
            
            # Generate volume
            base_volume = random.randint(500000, 5000000)
            volume_multiplier = random.uniform(0.5, 2.0)
            volume = int(base_volume * volume_multiplier)
            
            data_rows.append({
                'date': date_val,
                'symbol': symbol,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
    
    # Create DataFrame and save
    df = pl.DataFrame(data_rows)
    
    # Ensure directory exists
    os.makedirs("attached_assets", exist_ok=True)
    
    # Save as parquet
    output_path = "attached_assets/stocks_ohlc_data_1751553774887.parquet"
    df.write_parquet(output_path)
    
    print(f"Sample data created with {len(data_rows)} records for {len(symbols)} symbols")
    print(f"Data saved to: {output_path}")
    print(f"Date range: {min(dates)} to {max(dates)}")
    
    return output_path

if __name__ == "__main__":
    create_sample_parquet_data()
