
import uvicorn

from fastapi import FastAPI

from aiotopicdb.routers import attributes, occurrences, topics, associations, maps
from aiotopicdb.version import __version__

app = FastAPI()

app.include_router(attributes.router)
app.include_router(occurrences.router)
app.include_router(topics.router)
app.include_router(associations.router)
app.include_router(maps.router)


@app.get("/")
async def root():
    return {"message": f"TopicDB API Service, version {__version__}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)