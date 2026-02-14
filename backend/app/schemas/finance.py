from pydantic import BaseModel
from typing import List


class PortfolioDataPoint(BaseModel):
    """Single data point in portfolio history"""
    date: str  # YYYY-MM-DD
    total_value: float
    percentage_change: float  # from first data point


class PortfolioHistoryResponse(BaseModel):
    """Response schema for portfolio history endpoints"""
    data_points: List[PortfolioDataPoint]
    start_date: str
    end_date: str
    current_value: float
    starting_value: float
    total_gain_loss_pct: float
    display_mode: str  # "daily" or "weekly"
