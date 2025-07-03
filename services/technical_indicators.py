import numpy as np
import polars as pl
from typing import List, Dict, Any, Optional
from datetime import date
import logging

from schemas.indicator_schemas import (
    IndicatorType, IndicatorDataPoint, MACDDataPoint, 
    BollingerBandsDataPoint, IndicatorResponse
)

class TechnicalIndicatorService:
    """Service for calculating technical indicators"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_sma(self, df: pl.DataFrame, period: int) -> pl.DataFrame:
        """Calculate Simple Moving Average"""
        try:
            return df.with_columns([
                pl.col("close").rolling_mean(window_size=period).alias("sma")
            ])
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {e}")
            raise

    def calculate_ema(self, df: pl.DataFrame, period: int) -> pl.DataFrame:
        """Calculate Exponential Moving Average"""
        try:
            alpha = 2.0 / (period + 1.0)
            return df.with_columns([
                pl.col("close").ewm_mean(alpha=alpha).alias("ema")
            ])
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            raise

    def calculate_rsi(self, df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
        """Calculate Relative Strength Index"""
        try:
            # Calculate price changes
            df_with_changes = df.with_columns([
                (pl.col("close") - pl.col("close").shift(1)).alias("price_change")
            ])
            
            # Separate gains and losses
            df_with_gains_losses = df_with_changes.with_columns([
                pl.when(pl.col("price_change") > 0)
                .then(pl.col("price_change"))
                .otherwise(0.0)
                .alias("gain"),
                
                pl.when(pl.col("price_change") < 0)
                .then(-pl.col("price_change"))
                .otherwise(0.0)
                .alias("loss")
            ])
            
            # Calculate average gains and losses
            df_with_averages = df_with_gains_losses.with_columns([
                pl.col("gain").rolling_mean(window_size=period).alias("avg_gain"),
                pl.col("loss").rolling_mean(window_size=period).alias("avg_loss")
            ])
            
            # Calculate RSI
            df_with_rsi = df_with_averages.with_columns([
                pl.when(pl.col("avg_loss") == 0)
                .then(100.0)
                .otherwise(
                    100.0 - (100.0 / (1.0 + (pl.col("avg_gain") / pl.col("avg_loss"))))
                )
                .alias("rsi")
            ])
            
            return df_with_rsi
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            raise

    def calculate_macd(self, df: pl.DataFrame, fast_period: int = 12, 
                      slow_period: int = 26, signal_period: int = 9) -> pl.DataFrame:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            # Calculate fast and slow EMAs
            fast_alpha = 2.0 / (fast_period + 1.0)
            slow_alpha = 2.0 / (slow_period + 1.0)
            signal_alpha = 2.0 / (signal_period + 1.0)
            
            df_with_emas = df.with_columns([
                pl.col("close").ewm_mean(alpha=fast_alpha).alias("ema_fast"),
                pl.col("close").ewm_mean(alpha=slow_alpha).alias("ema_slow")
            ])
            
            # Calculate MACD line
            df_with_macd = df_with_emas.with_columns([
                (pl.col("ema_fast") - pl.col("ema_slow")).alias("macd")
            ])
            
            # Calculate signal line
            df_with_signal = df_with_macd.with_columns([
                pl.col("macd").ewm_mean(alpha=signal_alpha).alias("signal")
            ])
            
            # Calculate histogram
            df_final = df_with_signal.with_columns([
                (pl.col("macd") - pl.col("signal")).alias("histogram")
            ])
            
            return df_final
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            raise

    def calculate_bollinger_bands(self, df: pl.DataFrame, period: int = 20, 
                                 std_dev: float = 2.0) -> pl.DataFrame:
        """Calculate Bollinger Bands"""
        try:
            df_with_sma = df.with_columns([
                pl.col("close").rolling_mean(window_size=period).alias("middle_band")
            ])
            
            df_with_std = df_with_sma.with_columns([
                pl.col("close").rolling_std(window_size=period).alias("std_dev")
            ])
            
            df_with_bands = df_with_std.with_columns([
                (pl.col("middle_band") + (pl.col("std_dev") * std_dev)).alias("upper_band"),
                (pl.col("middle_band") - (pl.col("std_dev") * std_dev)).alias("lower_band")
            ])
            
            return df_with_bands
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            raise

    def process_indicator_request(self, df: pl.DataFrame, 
                                indicator_type: IndicatorType,
                                parameters: Dict[str, Any]) -> List[Any]:
        """Process indicator request and return formatted data"""
        try:
            if indicator_type == IndicatorType.SMA:
                period = parameters.get('period', parameters.get('window', 14))
                result_df = self.calculate_sma(df, period)
                return [
                    IndicatorDataPoint(
                        date=row['date'],
                        value=row['sma'] if row['sma'] is not None else None
                    )
                    for row in result_df.to_dicts()
                ]
                
            elif indicator_type == IndicatorType.EMA:
                period = parameters.get('period', parameters.get('window', 14))
                result_df = self.calculate_ema(df, period)
                return [
                    IndicatorDataPoint(
                        date=row['date'],
                        value=row['ema'] if row['ema'] is not None else None
                    )
                    for row in result_df.to_dicts()
                ]
                
            elif indicator_type == IndicatorType.RSI:
                period = parameters.get('period', 14)
                result_df = self.calculate_rsi(df, period)
                return [
                    IndicatorDataPoint(
                        date=row['date'],
                        value=row['rsi'] if row['rsi'] is not None else None
                    )
                    for row in result_df.to_dicts()
                ]
                
            elif indicator_type == IndicatorType.MACD:
                fast_period = parameters.get('fast_period', 12)
                slow_period = parameters.get('slow_period', 26)
                signal_period = parameters.get('signal_period', 9)
                result_df = self.calculate_macd(df, fast_period, slow_period, signal_period)
                return [
                    MACDDataPoint(
                        date=row['date'],
                        macd=row['macd'] if row['macd'] is not None else None,
                        signal=row['signal'] if row['signal'] is not None else None,
                        histogram=row['histogram'] if row['histogram'] is not None else None
                    )
                    for row in result_df.to_dicts()
                ]
                
            elif indicator_type == IndicatorType.BOLLINGER_BANDS:
                period = parameters.get('period', 20)
                std_dev = parameters.get('std_dev', 2.0)
                result_df = self.calculate_bollinger_bands(df, period, std_dev)
                return [
                    BollingerBandsDataPoint(
                        date=row['date'],
                        upper_band=row['upper_band'] if row['upper_band'] is not None else None,
                        middle_band=row['middle_band'] if row['middle_band'] is not None else None,
                        lower_band=row['lower_band'] if row['lower_band'] is not None else None
                    )
                    for row in result_df.to_dicts()
                ]
                
            else:
                raise ValueError(f"Unsupported indicator type: {indicator_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing indicator request: {e}")
            raise
