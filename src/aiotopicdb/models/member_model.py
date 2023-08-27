from pydantic import BaseModel


class MemberModel(BaseModel):
    src_topic_ref: str
    src_role_spec: str
    dest_topic_ref: str
    dest_role_spec: str

    class Config:
        from_attributes = True
