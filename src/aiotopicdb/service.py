from fastapi import FastAPI

from .routers import attributes, occurrences, topics, associations, maps
from .version import __version__

app = FastAPI()

app.include_router(attributes.router)
app.include_router(occurrences.router)
app.include_router(topics.router)
app.include_router(associations.router)
app.include_router(maps.router)


@app.get("/")
async def root():
    return {"message": f"TopicDB API Service, version {__version__}"}
