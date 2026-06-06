from pydantic import BaseModel, Field


class JobDescriptionRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


class JobDescriptionResponse(BaseModel):
    title: str
    description: str
    skills: list[str]
    requirements: list[str]
