from pydantic import BaseModel


class MapModel(BaseModel):
    name: str
    description: str
    image_path: str
    published: bool
    promoted: bool

    class Config:
        orm_mode = True
