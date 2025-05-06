from pydantic import BaseModel

class Compound(BaseModel):
    name: str
    formula: str
    weight: float
    url: str
