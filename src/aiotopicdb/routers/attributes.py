from fastapi import APIRouter, HTTPException

from ..dependencies import get_store
from ..models.attribute_model import AttributeModel
from ..models.language import Language

store = get_store()

router = APIRouter(
    prefix="/maps/{map_id}/attributes",
    tags=["attributes"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{attribute_id}")
async def get_attribute(map_id: int, attribute_id: str):
    attribute = await store.get_attribute(map_id, attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    result = AttributeModel.model_validate(attribute)

    return result


@router.get("/{entity_id}/entity-attributes")
async def get_attributes(
    map_id: int, entity_id: str, scope: str = None, language: Language = None
):
    result = []
    attributes = await store.get_attributes(map_id, entity_id, scope, language)
    if not attributes:
        raise HTTPException(status_code=404, detail="Attributes not found")
    for attribute in attributes:
        result.append(AttributeModel.model_validate(attribute))
    return result
