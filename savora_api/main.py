from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import quota, reservations

# Création automatique des tables au démarrage
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Savora API",
    description="API REST pour la gestion des réservations du restaurant Savora.",
    version="1.0.0",
)

# CORS : autorise le site SvelteKit (dev + prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # SvelteKit dev
        "http://localhost:4173",   # SvelteKit preview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reservations.router)
app.include_router(quota.router)


@app.get("/", tags=["Santé"])
def health_check():
    return {"status": "ok", "service": "Savora API"}
