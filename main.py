from fastapi import FastAPI, Query
from typing import Optional, List
from models.compound import Compound
from services import pubchem, massbank, hmdb
import time
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API de Búsqueda en MassBank")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes (cualquier frontend)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Permitir todos los encabezados
)

@app.get("/buscar", response_model=List[Compound])
async def buscar_compuestos(
    nombre: Optional[str] = Query(None),
    formula: Optional[str] = Query(None),
    peso: Optional[float] = Query(None)
):
    start_time = time.perf_counter()  # ⏱️ Inicia el contador

    resultados = []

    pubchem_result = await pubchem.search_pubchem(nombre, formula, peso)
    print(f"🔍 Resultados de PubChem ({len(pubchem_result)})")

    massbank_result = await massbank.search_massbank(nombre, formula, peso)
    print(f"🔍 Resultados de MassBank ({len(massbank_result)})")

    # hmdb_result = await hmdb.search_hmdb(nombre, formula, peso)
    # print(f"🔍 Resultados de HMDB ({len(hmdb_result)}): {hmdb_result}")

    resultados.extend(pubchem_result)
    resultados.extend(massbank_result)
    #resultados.extend(hmdb_result)

    end_time = time.perf_counter()  # ⏱️ Finaliza el contador
    total_time = end_time - start_time
    print(f"⏳ Tiempo total de ejecución: {total_time:.2f} segundos")

    return resultados

@app.get("/buscar_massbank_picos", response_model=List[Compound])
async def buscar_por_picos(
    peak_list: str = Query(..., description="Formato: m/z;intensidad separados por coma"),
    threshold: float = Query(0.01, description="Umbral de coincidencia para comparación de espectros")
):
    """
    Búsqueda de compuestos en MassBank usando una lista de picos.
    Ejemplo: 56.04;10,69.04;42,83.06;51,...
    """
    resultados = await massbank.search_massbank_by_peaks(peak_list, threshold)
    print(f"🔍 Resultados de MassBank por picos: {len(resultados)} encontrados")
    return resultados