from fastapi import APIRouter,  Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate

from app.models.api import HackerNewsItemResponse, DataQueryParams

from app.services.data_service import data_service
from app.core.config.logging import get_logger
from app.core.config import get_rate_limit
from app.core.config.database import get_db_session

logger = get_logger("data")

router = APIRouter()


@router.get(
    "/data",
    response_model=Page[HackerNewsItemResponse],
    summary="Retrieve stored data",
    description="Get Hacker News data with filtering and pagination",
    dependencies=[Depends(get_rate_limit("data"))],
)
async def get_data(params: DataQueryParams = Depends(), pagination: Params = Depends(), db=Depends(get_db_session)):
    """
    Get Hacker News data with filtering and pagination.
    
    Query Parameters:
    - **item_id**: Get specific item by ID
    - **min_score**: Filter by minimum score (>= 0)
    - **keyword**: Filter by keyword in title
    - **order_by**: Order by field (score, time, id)
    - **order_direction**: Order direction (asc, desc)
    
    Pagination Parameters:
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 10, max: 100)
    
    Returns paginated list of Hacker News items.
    """
    logger.info(f"Data request: {params.model_dump()}")
    
    query = data_service.get_items_query(
        db=db,
        item_id=params.item_id,
        min_score=params.min_score,
        keyword=params.keyword,
        order_by=params.order_by,
        order_direction=params.order_direction,
    )

    return sqlalchemy_paginate(query, pagination)
