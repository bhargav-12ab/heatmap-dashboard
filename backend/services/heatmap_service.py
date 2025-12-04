"""
Service layer for heatmap calculations and data processing.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from functools import lru_cache


class HeatmapService:
    """
    Handles all heatmap-related calculations including:
    - Monthly averaging
    - Month-over-month return calculations
    - Heatmap matrix generation
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize the service with loaded data.
        
        Args:
            data: DataFrame containing DATE and index columns
        """
        self.data = data
        # Cache for computed results
        self._cache = {}
    
    def _get_cache_key(self, index_name: str, operation: str, *args) -> str:
        """Generate cache key for memoization."""
        return f"{index_name}:{operation}:{':'.join(map(str, args))}"
    
    def calculate_monthly_average(self, index_name: str) -> pd.Series:
        """
        Calculate monthly average prices for a given index.
        
        Args:
            index_name: Name of the index column
            
        Returns:
            Series with monthly average values, indexed by (year, month)
        """
        # Check cache
        cache_key = self._get_cache_key(index_name, 'monthly_avg')
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Create a copy with only DATE and the selected index
        df = self.data[['DATE', index_name]].copy()
        
        # Extract year and month
        df['Year'] = df['DATE'].dt.year
        df['Month'] = df['DATE'].dt.month
        
        # Calculate monthly average
        monthly_avg = df.groupby(['Year', 'Month'])[index_name].mean()
        
        # Cache result
        self._cache[cache_key] = monthly_avg
        
        return monthly_avg
    
    def calculate_mom_returns(self, monthly_avg: pd.Series) -> pd.Series:
        """
        Calculate month-over-month return percentage.
        Formula: (avg_current_month / avg_previous_month) - 1
        
        Args:
            monthly_avg: Series of monthly average values
            
        Returns:
            Series of MoM returns
        """
        # Calculate percentage change: (current / previous) - 1
        mom_returns = (monthly_avg / monthly_avg.shift(1)) - 1
        
        return mom_returns
    
    def generate_heatmap_matrix(self, index_name: str) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Generate heatmap matrix in the format:
        {
            "2025": { "1": 0.31, "2": 0.22, ... },
            "2024": { "1": -0.12, "2": 0.05, ... },
            ...
        }
        
        Args:
            index_name: Name of the index to generate heatmap for
            
        Returns:
            Dictionary with year -> month -> value structure
        """
        # Validate index exists
        if index_name not in self.data.columns:
            raise ValueError(f"Index '{index_name}' not found in data")
        
        # Calculate monthly averages
        monthly_avg = self.calculate_monthly_average(index_name)
        
        # Calculate MoM returns
        mom_returns = self.calculate_mom_returns(monthly_avg)
        
        # Build the heatmap dictionary
        heatmap: Dict[str, Dict[str, Optional[float]]] = {}
        
        for idx in mom_returns.index:
            year = idx[0]
            month = idx[1]
            value = mom_returns.loc[idx]
            year_str = str(year)
            month_str = str(month)
            
            # Initialize year if not exists
            if year_str not in heatmap:
                heatmap[year_str] = {}
            
            # Add value (round to 4 decimal places, handle NaN)
            if pd.isna(value):
                heatmap[year_str][month_str] = None
            else:
                heatmap[year_str][month_str] = round(float(value), 4)
        
        return heatmap
    
    def generate_monthly_price_matrix(self, index_name: str) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Generate monthly price matrix (monthly average prices).
        
        Args:
            index_name: Name of the index
            
        Returns:
            Dictionary with year -> month -> price structure
        """
        if index_name not in self.data.columns:
            raise ValueError(f"Index '{index_name}' not found in data")
        
        monthly_avg = self.calculate_monthly_average(index_name)
        price_matrix: Dict[str, Dict[str, Optional[float]]] = {}
        
        for idx in monthly_avg.index:
            year = idx[0]
            month = idx[1]
            value = monthly_avg.loc[idx]
            year_str = str(year)
            month_str = str(month)
            
            if year_str not in price_matrix:
                price_matrix[year_str] = {}
            
            if pd.isna(value):
                price_matrix[year_str][month_str] = None
            else:
                price_matrix[year_str][month_str] = round(float(value), 2)
        
        return price_matrix
    
    def calculate_avg_monthly_profits_3y(self, index_name: str) -> Optional[float]:
        """
        Calculate average of monthly profits (MoM returns) over the last 3 years.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Average monthly profit percentage over 3 years, or None if insufficient data
        """
        if index_name not in self.data.columns:
            raise ValueError(f"Index '{index_name}' not found in data")
        
        monthly_avg = self.calculate_monthly_average(index_name)
        mom_returns = self.calculate_mom_returns(monthly_avg)
        
        # Get the most recent date
        if len(mom_returns) == 0:
            return None
        
        latest_date = mom_returns.index[-1]
        latest_year = latest_date[0]
        
        # Filter for last 3 years
        three_years_ago = latest_year - 3
        recent_returns = mom_returns[
            [idx for idx in mom_returns.index if idx[0] > three_years_ago]
        ]
        
        if len(recent_returns) == 0:
            return None
        
        # Calculate average, ignoring NaN values
        avg = recent_returns.mean()
        return round(float(avg), 6) if not pd.isna(avg) else None
    
    def calculate_rank_percentile_4y(self, index_name: str) -> Optional[float]:
        """
        Calculate rank percentile over 4 years (performance metric).
        Higher percentile means better performance.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Rank percentile (0-100), or None if insufficient data
        """
        if index_name not in self.data.columns:
            raise ValueError(f"Index '{index_name}' not found in data")
        
        # Get data for last 4 years
        df = self.data[['DATE', index_name]].copy()
        df['Year'] = df['DATE'].dt.year
        
        latest_year = df['Year'].max()
        four_years_ago = latest_year - 4
        df_4y = df[df['Year'] > four_years_ago]
        
        if len(df_4y) == 0:
            return None
        
        # Calculate cumulative return over 4 years
        values = df_4y[index_name].dropna()
        if len(values) < 2:
            return None
        
        cumulative_return = (values.iloc[-1] / values.iloc[0]) - 1
        
        # Calculate percentile rank among all indices for the same period
        all_returns = []
        for col in self.data.columns:
            if col == 'DATE':
                continue
            try:
                col_df = self.data[['DATE', col]].copy()
                col_df['Year'] = col_df['DATE'].dt.year
                col_df_4y = col_df[col_df['Year'] > four_years_ago]
                col_values = col_df_4y[col].dropna()
                if len(col_values) >= 2:
                    col_return = (col_values.iloc[-1] / col_values.iloc[0]) - 1
                    all_returns.append(col_return)
            except:
                continue
        
        if len(all_returns) == 0:
            return None
        
        # Calculate percentile (percentage of indices with lower return)
        percentile = (sum(1 for r in all_returns if r < cumulative_return) / len(all_returns)) * 100
        return round(float(percentile), 2)
    
    def calculate_inverse_rank_percentile(self, index_name: str) -> Optional[float]:
        """
        Calculate inverse rank percentile (valuation metric).
        This is 100 - rank_percentile, where higher values suggest overvaluation.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Inverse rank percentile (0-100), or None if insufficient data
        """
        rank_percentile = self.calculate_rank_percentile_4y(index_name)
        if rank_percentile is None:
            return None
        return round(100 - rank_percentile, 2)
    
    def calculate_monthly_rank_position(self, index_name: str) -> Dict[str, Dict[str, Optional[int]]]:
        """
        Calculate rank position for each month by comparing the selected index's
        MoM return with all other indices for the same month.
        Returns actual rank number (1 = best performer, higher = worse).
        
        Args:
            index_name: Name of the index
            
        Returns:
            Dictionary with year -> month -> rank position (1, 2, 3, etc.)
        """
        if index_name not in self.data.columns:
            raise ValueError(f"Index '{index_name}' not found in data")
        
        # Calculate monthly averages and MoM returns for selected index
        monthly_avg = self.calculate_monthly_average(index_name)
        mom_returns = self.calculate_mom_returns(monthly_avg)
        
        # Calculate MoM returns for all indices
        all_indices_returns = {}
        for col in self.data.columns:
            if col == 'DATE':
                continue
            try:
                col_monthly_avg = self.calculate_monthly_average(col)
                col_mom_returns = self.calculate_mom_returns(col_monthly_avg)
                all_indices_returns[col] = col_mom_returns
            except:
                continue
        
        # Build the rank position dictionary
        rank_matrix: Dict[str, Dict[str, Optional[int]]] = {}
        
        for idx in mom_returns.index:
            year = idx[0]
            month = idx[1]
            value = mom_returns.loc[idx]
            year_str = str(year)
            month_str = str(month)
            
            # Initialize year if not exists
            if year_str not in rank_matrix:
                rank_matrix[year_str] = {}
            
            # Skip if no value for this month
            if pd.isna(value):
                rank_matrix[year_str][month_str] = None
                continue
            
            # Collect all indices' returns for this same month (EXCLUDING the selected index)
            same_month_returns = []
            for col, col_returns in all_indices_returns.items():
                if col == index_name:  # Skip the selected index itself
                    continue
                if idx in col_returns.index:
                    col_value = col_returns.loc[idx]
                    if not pd.isna(col_value):
                        same_month_returns.append(col_value)
            
            # Calculate rank position (1 = best, higher = worse)
            # Count how many OTHER indices have BETTER (higher) returns than this index
            if len(same_month_returns) > 0:
                rank_position = sum(1 for r in same_month_returns if r > value) + 1
                rank_matrix[year_str][month_str] = int(rank_position)
            else:
                rank_matrix[year_str][month_str] = None
        
        return rank_matrix
    
    def calculate_forward_returns(self, index_name: str, forward_period: str) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Calculate forward returns for each month.
        Forward return = return from current month to N months/years in the future.
        
        Args:
            index_name: Name of the index
            forward_period: One of '1M', '3M', '6M', '1Y', '2Y', '3Y', '4Y'
            
        Returns:
            Dictionary with year -> month -> forward return value
        """
        if index_name not in self.data.columns:
            raise ValueError(f"Index '{index_name}' not found in data")
        
        # Map forward period to number of months
        period_map = {
            '1M': 1,
            '3M': 3,
            '6M': 6,
            '1Y': 12,
            '2Y': 24,
            '3Y': 36,
            '4Y': 48
        }
        
        if forward_period not in period_map:
            raise ValueError(f"Invalid forward period: {forward_period}")
        
        months_forward = period_map[forward_period]
        
        # Calculate monthly averages
        monthly_avg = self.calculate_monthly_average(index_name)
        
        # Calculate forward returns
        forward_returns: Dict[str, Dict[str, Optional[float]]] = {}
        
        # Convert monthly_avg to list for easier indexing
        monthly_list = list(monthly_avg.items())
        
        for i, (idx, current_value) in enumerate(monthly_list):
            year = idx[0]
            month = idx[1]
            year_str = str(year)
            month_str = str(month)
            
            # Initialize year if not exists
            if year_str not in forward_returns:
                forward_returns[year_str] = {}
            
            # Check if we have data for the future period
            future_idx = i + months_forward
            if future_idx < len(monthly_list):
                future_value = monthly_list[future_idx][1]
                
                # Calculate forward return: (future_value / current_value) - 1
                if not pd.isna(current_value) and not pd.isna(future_value) and current_value != 0:
                    forward_return = (future_value / current_value) - 1
                    forward_returns[year_str][month_str] = round(float(forward_return), 4)
                else:
                    forward_returns[year_str][month_str] = None
            else:
                # No future data available
                forward_returns[year_str][month_str] = None
        
        return forward_returns
