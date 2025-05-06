from pydantic import BaseModel
from typing import List, Optional

class Compound(BaseModel):
    nombre: str
    formula: str
    masa_exacta: str
    imagen: str
    url: str

class SearchResult(BaseModel):
    compuestos: List[Compound]
    execution_time: float
