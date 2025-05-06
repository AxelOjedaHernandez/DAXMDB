import httpx
import asyncio
import re
from typing import List, Optional
from models.compound import Compound

BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def normalize_formula(formula: str) -> str:
    """Elimina espacios y normaliza la fórmula molecular."""
    return re.sub(r"\s+", "", formula.strip())

async def resolve_listkey(client: httpx.AsyncClient, listkey_url: str, delay: int = 2, max_retries: int = 5):
    """Resuelve una URL con ListKey de PubChem esperando los resultados."""
    for _ in range(max_retries):
        try:
            response = await client.get(listkey_url)
            response.raise_for_status()
            data = response.json()

            if "IdentifierList" in data:
                return data

            await asyncio.sleep(delay)

        except Exception:
            pass

    return {"IdentifierList": {"CID": []}}

async def fetch_pubchem_details(client: httpx.AsyncClient, cid: str) -> Optional[Compound]:
    """Obtiene detalles de un compuesto desde PubChem por su CID."""
    url = f"{BASE_URL}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
        return Compound(
            name=props.get("IUPACName", "No disponible"),
            formula=props.get("MolecularFormula", "Desconocida"),
            weight=props.get("MolecularWeight", 0.0),
            url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        )
    except Exception:
        return None

async def search_pubchem(name: Optional[str] = None, formula: Optional[str] = None, weight: Optional[float] = None) -> List[Compound]:
    urls = []

    print("🔍 Buscando en PubChem con:")
    print(f"   Nombre: {name}")
    print(f"   Fórmula: {formula}")
    print(f"   Peso: {weight}")

    if name:
        urls.append(f"{BASE_URL}/compound/name/{name}/cids/JSON")
    if formula:
        formula = normalize_formula(formula)
        urls.append(f"{BASE_URL}/compound/formula/{formula}/cids/JSON")
    if weight:
        urls.append(f"{BASE_URL}/compound/molecular_weight/equals/{weight}/cids/JSON")

    if not urls:
        return []

    async with httpx.AsyncClient() as client:
        search_results = await asyncio.gather(*(client.get(url) for url in urls))
        cid_sets = []

        for resp in search_results:
            cids = []
            if resp.status_code == 200 or 202:
                data = resp.json()
                if "Waiting" in data and "ListKey" in data["Waiting"]:
                    listkey = data["Waiting"]["ListKey"]
                    listkey_url = f"{BASE_URL}/compound/listkey/{listkey}/cids/JSON"
                    data = await resolve_listkey(client, listkey_url)
                cids = data.get("IdentifierList", {}).get("CID", [])
            cid_sets.append(set(cids))

        print(f"🔎 CIDs encontrados por criterio: {[len(s) for s in cid_sets]}")

        # Elimina sets vacíos
        cid_sets = [s for s in cid_sets if s]
        if not cid_sets:
            return []

        common_cids = set.intersection(*cid_sets) if len(cid_sets) > 1 else cid_sets[0]
        if not common_cids:
            return []

        details_tasks = [fetch_pubchem_details(client, str(cid)) for cid in common_cids]
        details = await asyncio.gather(*details_tasks)

    return [c for c in details if c]

