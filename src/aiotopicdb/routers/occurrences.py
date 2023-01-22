from fastapi import APIRouter, HTTPException

from ..retrievalmode import RetrievalMode
from ..dependencies import get_store
from ..models.occurrence_model import OccurrenceModel

store = get_store()

router = APIRouter(prefix="/maps/{map_id}/occurrences", tags=["occurrences"],
                   responses={404: {"description": "Not found"}})


@router.get("/{occurrence_id}")
async def get_occurrence(map_id: int, occurrence_id: str,
                         inline_resource_data: RetrievalMode = None,
                         resolve_attributes: RetrievalMode = None):
    occurrence = await store.get_occurrence(map_id, occurrence_id, inline_resource_data, resolve_attributes)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    result = OccurrenceModel.from_orm(occurrence)

    return result
