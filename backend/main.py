"""
FastAPI backend for Financial Heatmap Dashboard.
Provides endpoints for index listing and heatmap data generation.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from models.schemas import IndicesResponse, HeatmapResponse
from utils.csv_loader import CSVLoader
from services.heatmap_service import HeatmapService


# Initialize FastAPI app
app = FastAPI(
    title="Financial Heatmap API",
    description="API for generating financial index heatmaps with MoM returns",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CSV loader (CSV should be in project root)
CSV_PATH = Path(__file__).parent.parent / "Latest_Indices_rawdata_14112025.csv"
csv_loader = CSVLoader(str(CSV_PATH))

# Global cached service instance
cached_service = None


@app.on_event("startup")
async def startup_event():
    """
    Load CSV data on startup to validate file existence and cache it.
    """
    global cached_service
    try:
        data = csv_loader.load_data()
        print(f"✓ CSV data loaded successfully ({len(data)} rows)")
        # Pre-initialize service with cached data
        cached_service = HeatmapService(data)
        print("✓ Heatmap service initialized")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print(f"  Expected CSV at: {CSV_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        sys.exit(1)


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Financial Heatmap API",
        "version": "1.0.0",
        "endpoints": {
            "/indices": "Get list of all available indices",
            "/heatmap/{index_name}": "Get heatmap data for a specific index"
        }
    }


@app.get("/indices", response_model=IndicesResponse)
async def get_indices():
    """
    Get list of all available index columns.
    
    Returns:
        IndicesResponse: List of index names
    """
    try:
        indices = csv_loader.get_index_columns()
        return IndicesResponse(indices=indices)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching indices: {str(e)}")


@app.get("/heatmap/{index_name}", response_model=HeatmapResponse)
async def get_heatmap(index_name: str, forward_period: str = None):
    """
    Get heatmap data for a specific index.
    Calculates monthly averages and month-over-month returns or forward returns.
    
    Args:
        index_name: Name of the index (must match column name in CSV)
        forward_period: Optional forward period ('1M', '3M', '6M', '1Y', '2Y', '3Y', '4Y')
                       If provided, shows forward returns instead of MoM returns
        
    Returns:
        HeatmapResponse: Heatmap matrix with year -> month -> return value
    """
    try:
        # Validate index exists
        if index_name not in csv_loader.get_index_columns():
            raise HTTPException(
                status_code=404,
                detail=f"Index '{index_name}' not found. Use /indices to see available indices."
            )
        
        # Use cached service instead of creating new one
        service = cached_service
        
        # If forward_period is specified, use forward returns; otherwise use MoM returns
        if forward_period:
            heatmap_data = service.calculate_forward_returns(index_name, forward_period)
        else:
            heatmap_data = service.generate_heatmap_matrix(index_name)
        
        monthly_price = service.generate_monthly_price_matrix(index_name)
        monthly_profits = service.generate_heatmap_matrix(index_name)  # Always MoM returns for this metric
        avg_monthly_profits_3y = service.calculate_avg_monthly_profits_3y(index_name)
        rank_percentile_4y = service.calculate_rank_percentile_4y(index_name)
        inverse_rank_percentile = service.calculate_inverse_rank_percentile(index_name)
        monthly_rank_percentile = service.calculate_monthly_rank_position(index_name)
        
        return HeatmapResponse(
            index=index_name,
            heatmap=heatmap_data,
            monthly_price=monthly_price,
            monthly_profits=monthly_profits,
            avg_monthly_profits_3y=avg_monthly_profits_3y,
            rank_percentile_4y=rank_percentile_4y,
            inverse_rank_percentile=inverse_rank_percentile,
            monthly_rank_percentile=monthly_rank_percentile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating heatmap: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
