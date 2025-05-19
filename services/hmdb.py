# services/hmdb.py

import httpx
from typing import List, Optional
from models.compound import Compound

HMDB_API_KEY    = "nMq6GYDb.mXo7lyPkIew7lN6jS5RvT2OdrrCoeOzz"
HMDB_SEARCH_URL = "http://35.184.189.38/api/hmdb/metabolites/search/"

async def search_hmdb(name: Optional[str] = None, formula: Optional[str] = None) -> List[Compound]:
    """
    Busca metabolitos en HMDB usando cualquier combinación de:
    - nombre
    - fórmula
    - ambos
    Devuelve solo name, formula, mass y url.
    """
    if not (name or formula):
        return []

    payload = {}
    if name:
        payload["name"] = name
    if formula:
        payload["formula"] = formula

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {HMDB_API_KEY}"
    }
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        try:
            print("ℹ️ HMDB payload:", payload)
            resp = await client.post(HMDB_SEARCH_URL, json=payload)
            print("ℹ️ HMDB status:", resp.status_code)

            if resp.status_code != 200:
                print("⚠️ HMDB error:", resp.text[:200])
                return []

            raw = resp.json()
            entries = raw.get("data", raw) if isinstance(raw, dict) else raw
            results: List[Compound] = []

            for entry in entries:
                name_    = entry.get("name")
                formula_ = entry.get("moldb_formula") or entry.get("formula")
                mass_ = (
                    float(entry["moldb_mono_mass"])
                    if entry.get("moldb_mono_mass")
                    else float(entry.get("moldb_average_mass", 0.0))
                )
                hmdb_id = entry.get("hmdb_id", "")
                url     = f"https://hmdb.ca/metabolites/{hmdb_id}" if hmdb_id else ""

                results.append(Compound(
                    name=name_,
                    formula=formula_,
                    weight=mass_,
                    url=url
                ))

            return results

        except Exception as e:
            print("❌ HMDB error:", e)
            return []