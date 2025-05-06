import httpx
from typing import List, Optional
from models.compound import Compound

BASE_URL = "https://msbi.ipb-halle.de/MassBank-api/records"

async def search_massbank(name: Optional[str], formula: Optional[str], weight: Optional[float]) -> List[Compound]:
    params = {}

    if name:
        params["compound_name"] = name
    if formula:
        params["formula"] = formula
    if weight:
        params["exact_mass"] = f"{weight:.4f}"
        params["mass_tolerance"] = 0.1  # Puedes hacer esto dinámico si lo deseas

    search_url = f"{BASE_URL}/search"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(search_url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error solicitando a MassBank: {e}")
            print(f"Respuesta cruda: {resp.text[:300]}")
            return []

        results = []
        for record in data.get("data", []):  # ✅ Cambiamos "results" por "data"
            record_id = record.get("accession")
            if not record_id:
                continue

            # ✅ Ahora hacemos otra solicitud para obtener detalles del compuesto
            try:
                detail_url = f"{BASE_URL}/{record_id}"
                detail_resp = await client.get(detail_url)
                detail_resp.raise_for_status()
                detail_data = detail_resp.json()
            except Exception as e:
                print(f"Error obteniendo detalles para {record_id}: {e}")
                continue

            compound_info = detail_data.get("compound", {})
            compound = Compound(
                name=compound_info.get("names", ["Desconocido"])[0],
                formula=compound_info.get("formula", "N/A"),
                weight=compound_info.get("mass", 0.0),
                url=f"https://massbank.eu/MassBank/RecordDisplay?id={record_id}"
            )
            results.append(compound)

    return results
