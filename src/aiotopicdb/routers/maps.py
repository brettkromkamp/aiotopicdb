from fastapi import APIRouter, HTTPException

from ..dependencies import get_store
from ..models.map_model import MapModel

store = get_store()

router = APIRouter(
    prefix="/maps", tags=["maps"], responses={404: {"description": "Not found"}}
)


@router.get("/published")
async def get_published_maps():
    result = []
    topic_maps = await store.get_published_maps()
    if not topic_maps:
        raise HTTPException(status_code=404, detail="Published topic maps not found")
    for topic_map in topic_maps:
        result.append(MapModel.model_validate(topic_map))
    return result


@router.get("/promoted")
async def get_promoted_maps():
    result = []
    topic_maps = await store.get_promoted_maps()
    if not topic_maps:
        raise HTTPException(status_code=404, detail="Promoted topic maps not found")
    for topic_map in topic_maps:
        result.append(MapModel.model_validate(topic_map))
    return result


@router.get("/{map_id}")
async def get_map(map_id: int):
    topic_map = await store.get_map(map_id)
    if not topic_map:
        raise HTTPException(status_code=404, detail="Topic map not found")
    result = MapModel.model_validate(topic_map)
    return result


# @router.get("/{map_id}/topic-names")
# async def get_topic_names(map_id: int, offset: int = 0, limit: int = 100):
#     topic_names = await store.get_topic_names(map_id, offset=offset, limit=limit)
#     if not topic_names:
#         raise HTTPException(status_code=404, detail="Topic names not found")
#     return topic_names
