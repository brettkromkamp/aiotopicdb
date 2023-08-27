from pydantic import BaseModel


class MapModel(BaseModel):
    identifier: int
    name: str
    description: str
    image_path: str
    published: bool
    promoted: bool

    class Config:
        from_attributes = True
