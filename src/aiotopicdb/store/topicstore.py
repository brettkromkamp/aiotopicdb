"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

# region Module and Class Imports
from __future__ import annotations

from collections import namedtuple
from typing import Dict, Tuple

import aiosqlite

from aiotopicdb.constants import DATABASE_PATH, UNIVERSAL_SCOPE
from aiotopicdb.models.association import Association
from aiotopicdb.models.attribute import Attribute
from aiotopicdb.models.basename import BaseName
from aiotopicdb.models.collaborationmode import CollaborationMode
from aiotopicdb.models.datatype import DataType
from aiotopicdb.models.doublekeydict import DoubleKeyDict
from aiotopicdb.models.language import Language
from aiotopicdb.models.map import Map
from aiotopicdb.models.member import Member
from aiotopicdb.models.occurrence import Occurrence
from aiotopicdb.models.topic import Topic
from aiotopicdb.topicdberror import TopicDbError

from .retrievalmode import RetrievalMode

# endregion

# region Setup
TopicRefs = namedtuple("TopicRefs", ["instance_of", "role_spec", "topic_ref"])
# endregion


# region Class
class TopicStore:
    # region Initialisation
    def __init__(self, database_path: str = DATABASE_PATH) -> None:
        self.database_path = database_path

        self.base_topics = {
            UNIVERSAL_SCOPE: "Universal",
            "home": "Home",
            "entity": "Entity",
            "topic": "Topic",
            "base-topic": "Base Topic",
            "association": "Association",
            "occurrence": "Occurrence",
            "navigation": "Navigation",
            "member": "Member",
            "category": "Category",
            "categorization": "Categorization",
            "tag": "Tag",
            "tags": "Tags",
            "note": "Note",
            "notes": "Notes",
            "broader": "Broader",
            "narrower": "Narrower",
            "related": "Related",
            "parent": "Parent",
            "child": "Child",
            "previous": "Previous",
            "next": "Next",
            "up": "Up",
            "down": "Down",
            "image": "Image",
            "video": "Video",
            "audio": "Audio",
            "file": "File",
            "url": "URL",
            "text": "Text",
            "3d-scene": "3D Scene",
            "string": "String",
            "number": "Number",
            "timestamp": "Timestamp",
            "boolean": "Boolean",
            "eng": "English Language",
            "spa": "Spanish Language",
            "nld": "Dutch Language",
            "inclusion": "Inclusion",  # https://brettkromkamp.com/posts/semantically-meaningful-relationships/
            "characteristic": "Characteristic",
            "action": "Action",
            "process": "Process",
            "temporal": "Temporal",
        }

    # endregion

    # region Topic
    @staticmethod
    def _normalize_topic_name(topic_identifier: str) -> str:
        return " ".join([word.capitalize() for word in topic_identifier.split("-")])

    async def get_topic(
        self,
        map_identifier: int,
        identifier: str,
        scope: str | None = None,
        language: Language | None = None,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
        resolve_occurrences: RetrievalMode = RetrievalMode.DONT_RESOLVE_OCCURRENCES,
    ) -> Topic | None:
        result = None
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT identifier, instance_of FROM topic WHERE map_identifier = ? AND identifier = ?",
                    (map_identifier, identifier),
                ) as topic_cursor:
                    async for topic_record in topic_cursor:
                        result = Topic(topic_record["identifier"], topic_record["instance_of"])
                        # Base names
                        result.clear_base_names()
                        # TODO: Add base names
                        # Attributes
                        if resolve_attributes and resolve_attributes is RetrievalMode.RESOLVE_ATTRIBUTES:
                            result.add_attributes(await self.get_attributes(map_identifier, identifier, scope=scope))
                        # Occurrences
                        if resolve_occurrences and resolve_occurrences is RetrievalMode.RESOLVE_OCCURRENCES:
                            result.add_occurrences(
                                await self.get_topic_occurrences(map_identifier, identifier, scope=scope)
                            )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching topic: {error}")
        return result

    async def get_related_topics(
        self,
        map_identifier: int,
        identifier: str,
        instance_ofs: list[str] | None = None,
        scope: str | None = None,
    ) -> list[Topic]:
        result: list[Topic] = []

        associations = await self.get_topic_associations(
            map_identifier, identifier, instance_ofs=instance_ofs, scope=scope
        )
        if associations:
            groups = await self.get_association_groups(map_identifier, identifier, associations=associations)
            for instance_of in groups.dict:
                for role in groups.dict[instance_of]:
                    for topic_ref in groups[instance_of, role]:
                        if topic_ref == identifier:
                            continue
                        topic = await self.get_topic(map_identifier, topic_ref)
                        if topic:
                            result.append(topic)
        return result

    async def get_topic_associations(
        self,
        map_identifier: int,
        identifier: str,
        instance_ofs: list[str] | None = None,
        scope: str | None = None,
        language: Language | None = None,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
        resolve_occurrences: RetrievalMode = RetrievalMode.DONT_RESOLVE_OCCURRENCES,
    ) -> list[Association]:
        result: list[Association] = []

        sql = """SELECT identifier FROM topic WHERE map_identifier = ? {0} AND
                identifier IN
                    (SELECT association_identifier FROM member
                     WHERE map_identifier = ? AND (src_topic_ref = ? OR dest_topic_ref = ?))"""
        if instance_ofs:
            instance_of_in_condition = " AND instance_of IN ("
            for index, value in enumerate(instance_ofs):
                if (index + 1) != len(instance_ofs):
                    instance_of_in_condition += "?, "
                else:
                    instance_of_in_condition += "?) "
            if scope:
                query_filter = instance_of_in_condition + " AND scope = ? "
                bind_variables = (
                    (map_identifier,) + tuple(instance_ofs) + (scope, map_identifier, identifier, identifier)
                )
            else:
                query_filter = instance_of_in_condition
                bind_variables = (map_identifier,) + tuple(instance_ofs) + (map_identifier, identifier, identifier)
        else:
            if scope:
                query_filter = " AND scope = ?"
                bind_variables = (
                    map_identifier,
                    scope,
                    map_identifier,
                    identifier,
                    identifier,
                )
            else:
                query_filter = ""
                bind_variables = (
                    map_identifier,
                    map_identifier,
                    identifier,
                    identifier,
                )
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql.format(query_filter), bind_variables) as cursor:
                    async for record in cursor:
                        association = await self.get_association(
                            map_identifier,
                            record["identifier"],
                            language=language,
                            resolve_attributes=resolve_attributes,
                            resolve_occurrences=resolve_occurrences,
                        )
                        if association:
                            result.append(association)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching associations: {error}")

        return result

    async def get_topic_occurrences(
        self,
        map_identifier: int,
        identifier: str,
        instance_of: str | None = None,
        scope: str | None = None,
        language: Language | None = None,
        inline_resource_data: RetrievalMode = RetrievalMode.DONT_INLINE_RESOURCE_DATA,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
    ) -> list[Occurrence]:
        result: list[Occurrence] = []

        sql = """SELECT identifier, instance_of, scope, resource_ref, topic_identifier, language
            FROM occurrence
            WHERE map_identifier = ? AND
            topic_identifier = ?
            {0}
            ORDER BY instance_of, scope, language"""
        if instance_of:
            if scope:
                if language:
                    query_filter = " AND instance_of = ? AND scope = ? AND language = ?"
                    bind_variables = (
                        map_identifier,
                        identifier,
                        instance_of,
                        scope,
                        language.name.lower(),
                    )
                else:
                    query_filter = " AND instance_of = ? AND scope = ?"
                    bind_variables = (map_identifier, identifier, instance_of, scope)  # type: ignore
            else:
                if language:
                    query_filter = " AND instance_of = ? AND language = ?"
                    bind_variables = (
                        map_identifier,
                        identifier,
                        instance_of,
                        language.name.lower(),
                    )  # type: ignore
                else:
                    query_filter = " AND instance_of = ?"
                    bind_variables = (map_identifier, identifier, instance_of)  # type: ignore
        else:
            if scope:
                if language:
                    query_filter = " AND scope = ? AND language = ?"
                    bind_variables = (
                        map_identifier,
                        identifier,
                        scope,
                        language.name.lower(),
                    )  # type: ignore
                else:
                    query_filter = " AND scope = ?"
                    bind_variables = (map_identifier, identifier, scope)  # type: ignore
            else:
                if language:
                    query_filter = " AND language = ?"
                    bind_variables = (map_identifier, identifier, language.name.lower())  # type: ignore
                else:
                    query_filter = ""
                    bind_variables = (map_identifier, identifier)  # type: ignore
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql.format(query_filter), bind_variables) as cursor:
                    async for record in cursor:
                        resource_data = None
                        if inline_resource_data and inline_resource_data is RetrievalMode.INLINE_RESOURCE_DATA:
                            resource_data = await self.get_occurrence_data(map_identifier, record["identifier"])
                        occurrence = Occurrence(
                            record["identifier"],
                            record["instance_of"],
                            record["topic_identifier"],
                            record["scope"],
                            record["resource_ref"],
                            resource_data,  # Type: bytes
                            Language[record["language"].upper()],
                        )
                        if resolve_attributes and resolve_attributes is RetrievalMode.RESOLVE_ATTRIBUTES:
                            occurrence.add_attributes(await self.get_attributes(map_identifier, occurrence.identifier))
                        result.append(occurrence)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching occurrences: {error}")
        return result

    # endregion

    # region BaseName
    async def get_topic_base_names(self, map_identifier: int, identifier: str) -> list[BaseName]:
        result: list[BaseName] = []
        # TODO: Implement
        return result
    # endregion

    # region Association
    @staticmethod
    def _resolve_topic_refs(association: Association) -> list[TopicRefs]:
        result: list[TopicRefs] = [
            TopicRefs(
                association.instance_of,
                association.member.src_role_spec,
                association.member.src_topic_ref,
            ),
            TopicRefs(
                association.instance_of,
                association.member.dest_role_spec,
                association.member.dest_topic_ref,
            ),
        ]

        return result

    async def get_association(
        self,
        map_identifier: int,
        identifier: str,
        scope: str | None = None,
        language: Language | None = None,
        resolve_attributes: RetrievalMode | None = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
        resolve_occurrences: RetrievalMode | None = RetrievalMode.DONT_RESOLVE_OCCURRENCES,
    ) -> Association | None:
        result = None
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row

                # Association record
                async with db.execute(
                    "SELECT identifier, instance_of, scope FROM topic WHERE map_identifier = ? AND identifier = ? AND scope IS NOT NULL",
                    (map_identifier, identifier),
                ) as association_cursor:
                    async for association_record in association_cursor:
                        result = Association(
                            identifier=association_record["identifier"],
                            instance_of=association_record["instance_of"],
                            scope=association_record["scope"],
                        )
                        # Base names
                        result.clear_base_names()
                        # TODO: Add base names
                        # Member record
                        async with db.execute(
                            "SELECT * FROM member WHERE map_identifier = ? AND association_identifier = ?",
                            (map_identifier, identifier),
                        ) as member_cursor:
                            async for member_record in member_cursor:
                                member = Member(
                                    src_topic_ref=member_record["src_topic_ref"],
                                    src_role_spec=member_record["src_role_spec"],
                                    dest_topic_ref=member_record["dest_topic_ref"],
                                    dest_role_spec=member_record["dest_role_spec"],
                                    identifier=member_record["identifier"],
                                )
                                result.member = member
                        if resolve_attributes and resolve_attributes is RetrievalMode.RESOLVE_ATTRIBUTES:
                            result.add_attributes(await self.get_attributes(map_identifier, identifier))
                        if resolve_occurrences and resolve_occurrences is RetrievalMode.RESOLVE_OCCURRENCES:
                            result.add_occurrences(await self.get_topic_occurrences(map_identifier, identifier))
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching association: {error}")

        return result

    async def get_association_groups(
        self,
        map_identifier: int,
        identifier: str,
        associations: list[Association] | None = None,
        instance_ofs: list[str] | None = None,
        scope: str | None = None,
    ) -> DoubleKeyDict:
        if identifier == "" and associations is None:
            raise TopicDbError("At least one of following parameters is required: 'identifier' or 'associations'")

        result = DoubleKeyDict()
        if not associations:
            associations = await self.get_topic_associations(
                map_identifier, identifier, instance_ofs=instance_ofs, scope=scope
            )
        for association in associations:
            resolved_topic_refs = self._resolve_topic_refs(association)
            for resolved_topic_ref in resolved_topic_refs:
                instance_of = resolved_topic_ref.instance_of
                role_spec = resolved_topic_ref.role_spec
                topic_ref = resolved_topic_ref.topic_ref
                if topic_ref != identifier:
                    if [instance_of, role_spec] in result:
                        topic_refs = result[instance_of, role_spec]
                        if topic_ref not in topic_refs:
                            topic_refs.append(topic_ref)
                        result[instance_of, role_spec] = topic_refs
                    else:
                        result[instance_of, role_spec] = [topic_ref]
        return result

    # endregion

    # region Occurrence
    async def get_occurrence(
        self,
        map_identifier: int,
        identifier: str,
        inline_resource_data: RetrievalMode = RetrievalMode.DONT_INLINE_RESOURCE_DATA,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
    ) -> Occurrence | None:
        result = None
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT identifier, instance_of, scope, resource_ref, topic_identifier, language FROM occurrence WHERE map_identifier = ? AND identifier = ?",
                    (map_identifier, identifier),
                ) as cursor:
                    async for record in cursor:
                        resource_data = None
                        if (
                            inline_resource_data
                            and inline_resource_data.value is RetrievalMode.INLINE_RESOURCE_DATA.value
                        ):
                            resource_data = await self.get_occurrence_data(map_identifier, identifier)
                        result = Occurrence(
                            record["identifier"],
                            record["instance_of"],
                            record["topic_identifier"],
                            record["scope"],
                            record["resource_ref"],
                            resource_data,  # Type: bytes
                            Language[record["language"].upper()],
                        )
                        if resolve_attributes and resolve_attributes.value is RetrievalMode.RESOLVE_ATTRIBUTES.value:
                            result.add_attributes(await self.get_attributes(map_identifier, identifier))
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching occurrence: {error}")
        return result

    async def get_occurrence_data(self, map_identifier: int, identifier: str) -> bytes | None:
        result = None
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT resource_data FROM occurrence WHERE map_identifier = ? AND identifier = ?",
                    (map_identifier, identifier),
                ) as cursor:
                    async for record in cursor:
                        if record["resource_data"] is not None:
                            result = record["resource_data"]  # Type: bytes
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching occurrence data: {error}")
        return result

    # endregion

    # region Attribute
    async def get_attribute(self, map_identifier: int, identifier: str) -> Attribute | None:
        result = None
        try:
            # Context managers automatically close the connection and the cursor
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM attribute WHERE map_identifier = ? AND identifier = ?",
                    (map_identifier, identifier),
                ) as cursor:
                    async for record in cursor:
                        result = Attribute(
                            record["name"],
                            record["value"],
                            record["entity_identifier"],
                            record["identifier"],
                            DataType[record["data_type"].upper()],
                            record["scope"],
                            Language[record["language"].upper()],
                        )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching attribute: {error}")
        return result

    async def get_attributes(
        self,
        map_identifier: int,
        entity_identifier: str,
        scope: str | None = None,
        language: Language | None = None,
    ) -> list[Attribute]:
        result: list[Attribute] = []
        if scope:
            if language:
                sql = """SELECT * FROM attribute
                    WHERE map_identifier = ? AND
                    entity_identifier = ? AND
                    scope = ? AND
                    language = ?"""
                bind_variables = (
                    map_identifier,
                    entity_identifier,
                    scope,
                    language.name.lower(),
                )
            else:
                sql = """SELECT * FROM attribute
                    WHERE map_identifier = ? AND
                    entity_identifier = ? AND
                    scope = ?"""
                bind_variables = (map_identifier, entity_identifier, scope)  # type: ignore
        else:
            if language:
                sql = """SELECT * FROM attribute
                    WHERE map_identifier = ? AND
                    entity_identifier = ? AND
                    language = ?"""
                bind_variables = (
                    map_identifier,
                    entity_identifier,
                    language.name.lower(),
                )  # type: ignore
            else:
                sql = """SELECT * FROM attribute
                    WHERE map_identifier = ? AND
                    entity_identifier = ?"""
                bind_variables = (map_identifier, entity_identifier)  # type: ignore

        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql, bind_variables) as cursor:
                    async for record in cursor:
                        attribute = Attribute(
                            record["name"],
                            record["value"],
                            record["entity_identifier"],
                            record["identifier"],
                            DataType[record["data_type"].upper()],
                            record["scope"],
                            Language[record["language"].upper()],
                        )
                        result.append(attribute)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching attributes: {error}")
        return result

    # endregion

    # region Tag
    async def get_tags(self, map_identifier: int, identifier: str) -> list[str]:
        result: list[str] = []

        associations = await self.get_topic_associations(map_identifier, identifier)
        if associations:
            groups = await self.get_association_groups(map_identifier, identifier, associations=associations)
            for instance_of in groups.dict:
                for role in groups.dict[instance_of]:
                    for topic_ref in groups[instance_of, role]:
                        if topic_ref == identifier:
                            continue
                        if instance_of == "categorization":
                            result.append(topic_ref)
        return result

    # endregion

    # region Topic Map
    async def get_map(self, map_identifier: int, user_identifier: int | None = None) -> Map | None:
        result = None
        if user_identifier:
            sql = """SELECT
                map.identifier AS map_identifier,
                map.name AS name,
                map.description AS description,
                map.image_path AS image_path,
                map.initialised AS initialised,
                map.published AS published,
                map.promoted AS promoted,
                user_map.user_identifier AS user_identifier,
                user_map.owner AS owner,
                user_map.collaboration_mode AS collaboration_mode
                FROM map
                INNER JOIN user_map ON map.identifier = user_map.map_identifier
                WHERE user_map.user_identifier = ?
                AND map.identifier = ?
                ORDER BY map_identifier"""
            bind_variables = (user_identifier, map_identifier)
        else:
            sql = "SELECT * FROM map WHERE identifier = ?"
            bind_variables = (map_identifier,)  # type: ignore
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql, bind_variables) as cursor:
                    async for record in cursor:
                        result = Map(
                            record["map_identifier"] if user_identifier else record["identifier"],
                            record["name"],
                            user_identifier=record["user_identifier"] if user_identifier else None,
                            description=record["description"],
                            image_path=record["image_path"],
                            initialised=record["initialised"],
                            published=record["published"],
                            promoted=record["promoted"],
                            owner=record["owner"] if user_identifier else None,
                            collaboration_mode=(
                                CollaborationMode[record["collaboration_mode"].upper()] if user_identifier else None
                            ),
                        )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching map: {error}")
        return result

    async def get_maps(
        self,
        user_identifier: int,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Map]:
        result: list[Map] = []

        sql = """SELECT
            map.identifier AS map_identifier,
            map.name AS name,
            map.description AS description,
            map.image_path AS image_path,
            map.initialised AS initialised,
            map.published AS published,
            map.promoted AS promoted,
            user_map.user_identifier AS user_identifier,
            user_map.owner AS owner,
            user_map.collaboration_mode AS collaboration_mode
            FROM map
            INNER JOIN user_map ON map.identifier = user_map.map_identifier
            WHERE user_map.user_identifier = ?
            ORDER BY map_identifier"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    sql,
                    (user_identifier,),
                ) as cursor:
                    async for record in cursor:
                        map = Map(
                            record["map_identifier"],
                            record["name"],
                            user_identifier=record["user_identifier"],
                            description=record["description"],
                            image_path=record["image_path"],
                            initialised=record["initialised"],
                            published=record["published"],
                            promoted=record["promoted"],
                            owner=record["owner"],
                            collaboration_mode=CollaborationMode[record["collaboration_mode"].upper()],
                        )
                        result.append(map)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching map: {error}")
        return result

    async def is_map_owner(self, map_identifier: int, user_identifier: int) -> bool:
        result = False
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_map WHERE user_identifier = ? AND map_identifier = ? AND owner = 1",
                    (user_identifier, map_identifier),
                ) as cursor:  # 1 = True
                    async for record in cursor:
                        result = True
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching map: {error}")
        return result

    # endregion

    # region Collaboration
    async def get_collaboration_mode(self, map_identifier: int, user_identifier: int) -> CollaborationMode | None:
        result = None
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT collaboration_mode FROM user_map WHERE user_identifier = ? AND map_identifier = ?",
                    (user_identifier, map_identifier),
                ) as cursor:
                    async for record in cursor:
                        result = CollaborationMode[record["collaboration_mode"].upper()]
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error fetching collaboration mode: {error}")
        return result

    async def get_collaborators(self, map_identifier: int) -> None:
        pass

    async def get_collaborator(self, map_identifier: int) -> None:
        pass

    # endregion
    # region Statistics
    async def get_topic_occurrences_statistics(
        self, map_identifier: int, identifier: str, scope: str | None = None
    ) -> Dict:
        result = {
            "image": 0,
            "3d-scene": 0,
            "video": 0,
            "audio": 0,
            "note": 0,
            "file": 0,
            "url": 0,
            "text": 0,
        }
        if scope:
            sql = "SELECT instance_of, COUNT(identifier) AS count FROM occurrence GROUP BY map_identifier, topic_identifier, instance_of, scope HAVING map_identifier = ? AND topic_identifier = ? AND scope = ?"
            bind_variables = (map_identifier, identifier, scope)
        else:
            sql = "SELECT instance_of, COUNT(identifier) AS count FROM occurrence GROUP BY map_identifier, topic_identifier, instance_of HAVING map_identifier = ? AND topic_identifier = ?"
            bind_variables = (map_identifier, identifier)  # type: ignore
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql, bind_variables) as cursor:
                    async for record in cursor:
                        result[record["instance_of"]] = record["count"]
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error compiling statistics: {error}")
        return result

    # endregion


# endregion
