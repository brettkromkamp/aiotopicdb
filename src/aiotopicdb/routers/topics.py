from fastapi import APIRouter, HTTPException

from ..retrievalmode import RetrievalMode
from ..dependencies import get_store
from ..models.association_model import AssociationModel
from ..models.language import Language
from ..models.occurrence_model import OccurrenceModel
from ..models.topic_model import TopicModel
from ..models.basename_model import BaseNameModel

store = get_store()

router = APIRouter(
    prefix="/maps/{map_id}/topics",
    tags=["topics"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{topic_id}")
async def get_topic(
    map_id: int,
    topic_id: str,
    scope: str = None,
    language: Language = None,
    resolve_attributes: RetrievalMode = None,
    resolve_occurrences: RetrievalMode = None,
):
    topic = await store.get_topic(
        map_id, topic_id, scope, language, resolve_attributes, resolve_occurrences
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    result = TopicModel.model_validate(topic)
    return {"map-identifier": map_id, "topic-identifier": topic_id, "topic": result}


@router.get("/{topic_id}/occurrences")
async def get_topic_occurrences(
    map_id: int,
    topic_id: str,
    instance_of: str = None,
    scope: str = None,
    language: Language = None,
    inline_resource_data: RetrievalMode = None,
    resolve_attributes: RetrievalMode = None,
):
    result = []
    occurrences = await store.get_topic_occurrences(
        map_id,
        topic_id,
        instance_of,
        scope,
        language,
        inline_resource_data,
        resolve_attributes,
    )
    if not occurrences:
        raise HTTPException(status_code=404, detail="Occurrences not found")
    for occurrence in occurrences:
        result.append(OccurrenceModel.model_validate(occurrence))
    return {"map-identifier": map_id, "topic-identifier": topic_id, "occurrences": result}


@router.get("/{topic_id}/associations")
async def get_topic_associations(
    map_id: int,
    topic_id: str,
    instance_of: str = None,
    scope: str = None,
    language: Language = None,
    inline_resource_data: RetrievalMode = None,
    resolve_attributes: RetrievalMode = None,
):
    result = []
    associations = await store.get_topic_associations(
        map_id,
        topic_id,
        instance_of,
        scope,
        language,
        inline_resource_data,
        resolve_attributes,
    )
    if not associations:
        raise HTTPException(status_code=404, detail="Associations not found")

    for association in associations:
        result.append(AssociationModel.model_validate(association))
    return {"map-identifier": map_id, "topic-identifier": topic_id, "associations": result}


@router.get("/{topic_id}/tags")
async def get_topic_tags(map_id: int, topic_id: str):
    tags = await store.get_tags(map_id, topic_id)
    if not tags:
        raise HTTPException(status_code=404, detail="Tags not found")
    return {"map-identifier": map_id, "topic-identifier": topic_id, "tags": tags}


@router.get("/{topic_id}/association-groups")
async def get_association_groups(
    map_id: int, topic_id: str, scope_id: str = "*", scope_filtered: int = 0
):
    result = []
    if scope_filtered:
        associations = await store.get_association_groups(
            map_id, topic_id, scope=scope_id
        )
    else:
        associations = await store.get_association_groups(map_id, topic_id)
    if not associations:
        raise HTTPException(status_code=404, detail="Association groups not found")
    for instance_of, roles in associations.dict.items():
        result_roles = []
        for role, topic_refs in roles.items():
            result_topic_refs = []
            for topic_ref in topic_refs:
                topic_ref_topic = await store.get_topic(map_id, topic_ref)
                result_topic_refs.append(
                    {
                        "identifier": topic_ref,
                        "name": topic_ref_topic.first_base_name.name,
                    }
                )
            else:
                role_topic = await store.get_topic(map_id, role)
                result_roles.append(
                    {
                        "identifier": role,
                        "name": role_topic.first_base_name.name,
                        "topicRefs": result_topic_refs,
                    }
                )
        else:
            instance_of_topic = await store.get_topic(map_id, instance_of)
            result.append(
                {
                    "identifier": instance_of,
                    "name": instance_of_topic.first_base_name.name,
                    "roles": result_roles,
                }
            )
    return {"map-identifier": map_id, "topic-identifier": topic_id, "association-groups": result}


@router.get("/{topic_id}/names")
async def get_topic_names(
    map_id: int,
    topic_id: str,
    scope: str = None,
    language: Language = None,
):
    result = []
    names = await store.get_topic_names(map_id, topic_id, scope, language)
    if not names:
        raise HTTPException(status_code=404, detail="Topic names not found")
    for name in names:
        result.append(BaseNameModel.model_validate(name))
    return {"map-identifier": map_id, "topic-identifier": topic_id, "topic-names": result}
