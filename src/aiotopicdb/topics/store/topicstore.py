"""
TopicStore class. Part of the Contextualise (https://contextualise.dev) project.

September 1, 2022
Brett Alistair Kromkamp (brettkromkamp@gmail.com)
"""

# region Module and Class Imports
from __future__ import annotations

from collections import namedtuple
from typing import List, Optional

import aiosqlite
from typedtree.tree import Tree  # type: ignore

from aiotopicdb.retrievalmode import RetrievalMode
from aiotopicdb.topics.models.association import Association
from aiotopicdb.topics.models.attribute import Attribute
from aiotopicdb.topics.models.basename import BaseName
from aiotopicdb.topics.models.datatype import DataType
from aiotopicdb.topics.models.doublekeydict import DoubleKeyDict
from aiotopicdb.topics.models.language import Language
from aiotopicdb.topics.models.map import Map
from aiotopicdb.topics.models.member import Member
from aiotopicdb.topics.models.occurrence import Occurrence
from aiotopicdb.topics.models.topic import Topic
from aiotopicdb.topics.topicdberror import TopicDbError

# endregion
# region Constants
TopicRefs = namedtuple("TopicRefs", ["instance_of", "role_spec", "topic_ref"])

_UNIVERSAL_SCOPE = "*"
_DATABASE_PATH = "contextualise.sqlite"

# endregion


# region Class
class TopicStore:
    # region Initialisation
    def __init__(self, database_path=_DATABASE_PATH) -> None:
        self.database_path = database_path

        self.base_topics = {
            _UNIVERSAL_SCOPE: "Universal",
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
        }

    # endregion

    # region Association
    @staticmethod
    def _resolve_topic_refs(association: Association) -> List[TopicRefs]:
        result: List[TopicRefs] = [
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
        scope: str = None,
        language: Language = None,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
        resolve_occurrences: RetrievalMode = RetrievalMode.DONT_RESOLVE_OCCURRENCES,
    ) -> Optional[Association]:
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
                        result.clear_base_names()
                        if scope:
                            if language:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier = ? AND
                                                    topic_identifier = ? AND
                                                    scope = ? AND
                                                    language = ?"""
                                bind_variables = (
                                    map_identifier,
                                    identifier,
                                    scope,
                                    language.name.lower(),
                                )
                            else:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier =? AND
                                                    topic_identifier = ? AND
                                                    scope = ?"""
                                bind_variables = (map_identifier, identifier, scope)
                        else:
                            if language:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier = ? AND
                                                    topic_identifier = ? AND
                                                    language = ?"""
                                bind_variables = (
                                    map_identifier,
                                    identifier,
                                    language.name.lower(),
                                )
                            else:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier = ? AND
                                                    topic_identifier = ?"""
                                bind_variables = (map_identifier, identifier)
                        # Base name records
                        async with db.execute(sql, bind_variables) as base_name_cursor:
                            async for base_name_record in base_name_cursor:
                                result.add_base_name(
                                    BaseName(
                                        base_name_record["name"],
                                        base_name_record["scope"],
                                        Language[
                                            base_name_record["language"].upper()
                                        ].value,
                                        base_name_record["identifier"],
                                    )
                                )
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
                        if (
                            resolve_attributes
                            and resolve_attributes is RetrievalMode.RESOLVE_ATTRIBUTES
                        ):
                            result.add_attributes(
                                await self.get_attributes(map_identifier, identifier)
                            )
                        if (
                            resolve_occurrences
                            and resolve_occurrences is RetrievalMode.RESOLVE_OCCURRENCES
                        ):
                            result.add_occurrences(
                                await self.get_topic_occurrences(
                                    map_identifier, identifier
                                )
                            )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving association: {error}")

        return result

    async def get_association_groups(
        self,
        map_identifier: int,
        identifier: str = "",
        associations: Optional[List[Association]] = None,
        instance_ofs: Optional[List[str]] = None,
        scope: str = None,
    ) -> DoubleKeyDict:
        if identifier == "" and associations is None:
            raise TopicDbError(
                "At least one of following parameters is required: 'identifier' or 'associations'"
            )

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

    # region Attribute
    async def get_attribute(
        self, map_identifier: int, identifier: str
    ) -> Optional[Attribute]:
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
                            DataType[record["data_type"].upper()].value,
                            record["scope"],
                            Language[record["language"].upper()].value,
                        )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving attribute: {error}")
        return result

    async def get_attributes(
        self,
        map_identifier: int,
        entity_identifier: str,
        scope: str = None,
        language: Language = None,
    ) -> List[Attribute]:
        result = []
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
                bind_variables = (map_identifier, entity_identifier, scope)
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
                )
            else:
                sql = """SELECT * FROM attribute
                    WHERE map_identifier = ? AND
                    entity_identifier = ?"""
                bind_variables = (map_identifier, entity_identifier)

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
                            DataType[record["data_type"].upper()].value,
                            record["scope"],
                            Language[record["language"].upper()].value,
                        )
                        result.append(attribute)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving attributes: {error}")
        return result

    # endregion

    # region Occurrence
    async def get_occurrence(
        self,
        map_identifier: int,
        identifier: str,
        inline_resource_data: RetrievalMode = RetrievalMode.DONT_INLINE_RESOURCE_DATA,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
    ) -> Optional[Occurrence]:
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
                            and inline_resource_data.value
                            is RetrievalMode.INLINE_RESOURCE_DATA.value
                        ):
                            resource_data = await self.get_occurrence_data(
                                map_identifier, identifier
                            )
                        result = Occurrence(
                            record["identifier"],
                            record["instance_of"],
                            record["topic_identifier"],
                            record["scope"],
                            record["resource_ref"],
                            resource_data,  # Type: bytes
                            Language[record["language"].upper()].value,
                        )
                        if (
                            resolve_attributes
                            and resolve_attributes.value
                            is RetrievalMode.RESOLVE_ATTRIBUTES.value
                        ):
                            result.add_attributes(
                                await self.get_attributes(map_identifier, identifier)
                            )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving occurrence: {error}")
        return result

    async def get_occurrence_data(
        self, map_identifier: int, identifier: str
    ) -> Optional[bytes]:
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
            raise TopicDbError(f"Error retrieving occurrence data: {error}")
        return result

    # endregion

    # region Tag
    async def get_tags(
        self, map_identifier: int, identifier: str
    ) -> List[Optional[str]]:
        result = []

        associations = await self.get_topic_associations(map_identifier, identifier)
        if associations:
            groups = await self.get_association_groups(
                map_identifier, associations=associations
            )
            for instance_of in groups.dict:
                for role in groups.dict[instance_of]:
                    for topic_ref in groups[instance_of, role]:
                        if topic_ref == identifier:
                            continue
                        if instance_of == "categorization":
                            result.append(topic_ref)
        return result

    # endregion

    # region Topic
    @staticmethod
    def _normalize_topic_name(topic_identifier):
        return " ".join([word.capitalize() for word in topic_identifier.split("-")])

    async def get_related_topics(
        self,
        map_identifier: int,
        identifier: str,
        instance_ofs: Optional[List[str]] = None,
        scope: str = None,
    ) -> List[Optional[Topic]]:
        result = []

        associations = await self.get_topic_associations(
            map_identifier, identifier, instance_ofs=instance_ofs, scope=scope
        )
        if associations:
            groups = await self.get_association_groups(
                map_identifier, associations=associations
            )
            for instance_of in groups.dict:
                for role in groups.dict[instance_of]:
                    for topic_ref in groups[instance_of, role]:
                        if topic_ref == identifier:
                            continue
                        result.append(await self.get_topic(map_identifier, topic_ref))
        return result

    async def get_topic(
        self,
        map_identifier: int,
        identifier: str,
        scope: str = None,
        language: Language = None,
        resolve_attributes: RetrievalMode = RetrievalMode.RESOLVE_ATTRIBUTES,
        resolve_occurrences: RetrievalMode = RetrievalMode.RESOLVE_OCCURRENCES,
    ) -> Optional[Topic]:
        result = None
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT identifier, instance_of FROM topic WHERE map_identifier = ? AND identifier = ?",
                    (map_identifier, identifier),
                ) as topic_cursor:
                    async for topic_record in topic_cursor:
                        result = Topic(
                            topic_record["identifier"], topic_record["instance_of"]
                        )
                        result.clear_base_names()
                        if scope:
                            if language:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier = ? AND
                                                    topic_identifier = ? AND
                                                    scope = ? AND
                                                    language = ?"""
                                bind_variables = (
                                    map_identifier,
                                    identifier,
                                    scope,
                                    language.name.lower(),
                                )
                            else:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier = ? AND
                                                    topic_identifier = ? AND
                                                    scope = ?"""
                                bind_variables = (map_identifier, identifier, scope)
                        else:
                            if language:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier = ? AND
                                                    topic_identifier = ? AND
                                                    language = ?"""
                                bind_variables = (
                                    map_identifier,
                                    identifier,
                                    language.name.lower(),
                                )
                            else:
                                sql = """SELECT name, scope, language, identifier
                                                    FROM basename
                                                    WHERE map_identifier = ? AND
                                                    topic_identifier = ?"""
                                bind_variables = (map_identifier, identifier)
                        async with db.execute(sql, bind_variables) as base_name_cursor:
                            async for base_name_record in base_name_cursor:
                                result.add_base_name(
                                    BaseName(
                                        base_name_record["name"],
                                        base_name_record["scope"],
                                        Language[
                                            base_name_record["language"].upper()
                                        ].value,
                                        base_name_record["identifier"],
                                    )
                                )
                        if (
                            resolve_attributes
                            and resolve_attributes is RetrievalMode.RESOLVE_ATTRIBUTES
                        ):
                            result.add_attributes(
                                await self.get_attributes(map_identifier, identifier)
                            )
                        if (
                            resolve_occurrences
                            and resolve_occurrences is RetrievalMode.RESOLVE_OCCURRENCES
                        ):
                            result.add_occurrences(
                                await self.get_topic_occurrences(
                                    map_identifier, identifier
                                )
                            )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving topic: {error}")
        return result

    async def get_topic_occurrences(
        self,
        map_identifier: int,
        identifier: str,
        instance_of: str = None,
        scope: str = None,
        language: Language = None,
        inline_resource_data: RetrievalMode = RetrievalMode.DONT_INLINE_RESOURCE_DATA,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
    ) -> List[Occurrence]:
        result = []

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
                    bind_variables = (map_identifier, identifier, instance_of, scope)
            else:
                if language:
                    query_filter = " AND instance_of = ? AND language = ?"
                    bind_variables = (
                        map_identifier,
                        identifier,
                        instance_of,
                        language.name.lower(),
                    )
                else:
                    query_filter = " AND instance_of = ?"
                    bind_variables = (map_identifier, identifier, instance_of)
        else:
            if scope:
                if language:
                    query_filter = " AND scope = ? AND language = ?"
                    bind_variables = (
                        map_identifier,
                        identifier,
                        scope,
                        language.name.lower(),
                    )
                else:
                    query_filter = " AND scope = ?"
                    bind_variables = (map_identifier, identifier, scope)
            else:
                if language:
                    query_filter = " AND language = ?"
                    bind_variables = (map_identifier, identifier, language.name.lower())
                else:
                    query_filter = ""
                    bind_variables = (map_identifier, identifier)
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    sql.format(query_filter), bind_variables
                ) as cursor:
                    async for record in cursor:
                        resource_data = None
                        if (
                            inline_resource_data
                            and inline_resource_data
                            is RetrievalMode.INLINE_RESOURCE_DATA
                        ):
                            resource_data = await self.get_occurrence_data(
                                map_identifier, identifier
                            )
                        occurrence = Occurrence(
                            record["identifier"],
                            record["instance_of"],
                            record["topic_identifier"],
                            record["scope"],
                            record["resource_ref"],
                            resource_data,  # Type: bytes
                            Language[record["language"].upper()].value,
                        )
                        if (
                            resolve_attributes
                            and resolve_attributes is RetrievalMode.RESOLVE_ATTRIBUTES
                        ):
                            occurrence.add_attributes(
                                await self.get_attributes(map_identifier, identifier)
                            )
                        result.append(occurrence)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving occurrences: {error}")
        return result

    async def get_topic_associations(
        self,
        map_identifier: int,
        identifier: str,
        instance_ofs: Optional[List[str]] = None,
        scope: str = None,
        language: Language = None,
        resolve_attributes: RetrievalMode = RetrievalMode.DONT_RESOLVE_ATTRIBUTES,
        resolve_occurrences: RetrievalMode = RetrievalMode.DONT_RESOLVE_OCCURRENCES,
    ) -> List[Association]:
        result = []

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
                    (map_identifier,)
                    + tuple(instance_ofs)
                    + (scope, map_identifier, identifier, identifier)
                )
            else:
                query_filter = instance_of_in_condition
                bind_variables = (
                    (map_identifier,)
                    + tuple(instance_ofs)
                    + (map_identifier, identifier, identifier)
                )
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
                async with db.execute(
                    sql.format(query_filter), bind_variables
                ) as cursor:
                    async for record in cursor:
                        association = await self.get_association(
                            map_identifier,
                            record["identifier"],
                            language=language,
                            resolve_attributes=resolve_attributes,
                            resolve_occurrences=resolve_occurrences,
                        )
                        result.append(association)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving associations: {error}")

        return result

    # endregion

    # region Topic Map
    async def get_map(self, map_identifier: int) -> Optional[Map]:
        result = None
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM map WHERE identifier = ? AND published = 1",
                    (map_identifier,),
                ) as cursor:
                    async for record in cursor:
                        result = Map(
                            record["identifier"],
                            record["name"],
                            description=record["description"],
                            image_path=record["image_path"],
                            published=record["published"],
                            promoted=record["promoted"],
                        )
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving map: {error}")
        return result

    async def get_published_maps(self) -> List[Map]:
        result = []
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM map WHERE published = 1 ORDER BY identifier"
                ) as cursor:
                    async for record in cursor:
                        topic_map = Map(
                            record["identifier"],
                            record["name"],
                            description=record["description"],
                            image_path=record["image_path"],
                            published=record["published"],
                            promoted=record["promoted"],
                        )
                        result.append(topic_map)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving published maps: {error}")
        return result

    async def get_promoted_maps(self) -> List[Map]:
        result = []
        try:
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM map WHERE promoted = 1 AND published = 1 ORDER BY identifier"
                ) as cursor:
                    async for record in cursor:
                        topic_map = Map(
                            record["identifier"],
                            record["name"],
                            description=record["description"],
                            image_path=record["image_path"],
                            published=record["published"],
                            promoted=record["promoted"],
                        )
                        result.append(topic_map)
        except aiosqlite.Error as error:
            raise TopicDbError(f"Error retrieving promoted maps: {error}")
        return result

    # endregion


# endregion
