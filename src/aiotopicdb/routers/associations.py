from fastapi import APIRouter, HTTPException

from ..retrievalmode import RetrievalMode
from ..dependencies import get_store
from ..models.association_model import AssociationModel
from ..models.language import Language

store = get_store()

router = APIRouter(
    prefix="/maps/{map_id}/associations",
    tags=["associations"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{association_id}")
async def get_association(
    map_id: int,
    association_id: str,
    scope: str = None,
    language: Language = None,
    inline_resource_data: RetrievalMode = None,
    resolve_attributes: RetrievalMode = None,
):
    association = await store.get_association(
        map_id,
        association_id,
        scope,
        language,
        inline_resource_data,
        resolve_attributes,
    )
    if not association:
        raise HTTPException(status_code=404, detail="Association not found")
    result = AssociationModel.model_validate(association)
    return result
