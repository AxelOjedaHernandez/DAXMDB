import httpx
import os
from typing import List, Optional
from models.compound import Compound

HMDB_API_KEY = "nMq6GYDb.mXo7lyPkIew7lN6jS5RvT2OdrrCoeOzz"
BASE_URL = "https://hmdb.ca/unearth/q"

async def search_hmdb(name: Optional[str], formula: Optional[str], weight: Optional[float]) -> List[Compound]:
    query_parts = []
    if name:
        query_parts.append(name)
    if formula:
        query_parts.append(formula)
    if weight:
        query_parts.append(str(weight))

    query = " ".join(query_parts)

    if not query:
        return []

    params = {
        "query": query,
        "searcher": "metabolites"
    }

    headers = {
        "Authorization": f"Bearer {HMDB_API_KEY}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(BASE_URL, params=params, headers=headers)

        if resp.status_code != 200:
            print(f"HMDB error: {resp.status_code} - {resp.text}")
            return []
        
        print(f"HMDB status code: {resp.status_code}")
        print(f"HMDB headers sent: {headers}")
        print(f"HMDB params sent: {params}")
        print(f"HMDB raw response:\n{resp.text}")

        try:
            data = resp.json()
        except Exception as e:
            print(f"Error parsing HMDB response: {e}")
            return []

        results = []
        for item in data.get("metabolites", []):
            compound = Compound(
                name=item.get("name", "Desconocido"),
                formula=item.get("chemical_formula", "N/A"),
                weight=float(item.get("monisotopic_molecular_weight", 0.0)),
                url=f"https://hmdb.ca/metabolites/{item.get('accession')}"
            )
            results.append(compound)
        return results

