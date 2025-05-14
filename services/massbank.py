import httpx
from typing import List, Optional
from urllib.parse import quote
import asyncio
from models.compound import Compound

BASE_URL = "https://msbi.ipb-halle.de/MassBank-api/records"

# Límite de concurrencia (ajusta según pruebas, p. ej. 5–10)
MAX_CONCURRENT_REQUESTS = 10

async def search_massbank(name: Optional[str], formula: Optional[str], weight: Optional[float]) -> List[Compound]:
    params = {}

    if name:
        params["compound_name"] = name
    if formula:
        params["formula"] = formula
    if weight:
        params["exact_mass"] = f"{weight:.4f}"
        params["mass_tolerance"] = 0.01  # Puedes hacer esto dinámico si lo deseas

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

async def search_massbank_by_peaks(peak_list: str, threshold: float = 0.01) -> List[Compound]:
    peak_list = peak_list.replace(" ", "")
    encoded_peak_list = quote(peak_list, safe=",")
    full_url = f"{BASE_URL}/search?peak_list={encoded_peak_list}&peak_list_threshold={threshold}"
    timeout = httpx.Timeout(120.0)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(full_url)
            resp.raise_for_status()
            data = resp.json()

            accessions = [
                r.get("accession")
                for r in data.get("data", [])
                if r.get("accession")
            ]

            if not accessions:
                return []

            tasks = [
                _fetch_massbank_detail(client, acc, semaphore)
                for acc in accessions
            ]
            results = await asyncio.gather(*tasks)
            return [c for c in results if c]

        except httpx.RequestError as e:
            print(f"❌ Error consultando MassBank: {e}")
            return []

async def _fetch_massbank_detail(client: httpx.AsyncClient, acc: str, semaphore: asyncio.Semaphore) -> Compound:
    async with semaphore:
        try:
            detail_url = f"{BASE_URL}/{acc}"
            resp = await client.get(detail_url)
            resp.raise_for_status()
            info = resp.json().get("compound", {})
            return Compound(
                name=info.get("names", ["Desconocido"])[0],
                formula=info.get("formula", "N/A"),
                weight=info.get("mass", 0.0),
                url=f"https://massbank.eu/MassBank/RecordDisplay?id={acc}"
            )
        except Exception as e:
            print(f"⚠️ Error detalle {acc}: {e}")
            return None

