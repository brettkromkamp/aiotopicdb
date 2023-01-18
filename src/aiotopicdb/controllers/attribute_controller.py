from starlite import Controller
from starlite.handlers import get, post, patch, delete

from aiotopicdb.models.attribute_model import AttributeModel


class AttributeController(Controller):
    path = "/attribute"

    @get(path="/{map_id: str, attribute_id:str}")
    async def get_attribute(self, map_id: int, attribute_id: str) -> AttributeModel:
        pass
