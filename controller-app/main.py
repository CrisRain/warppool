from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from .pool_manager import pool_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时运行
    pool_manager.start()
    yield
    # 在应用关闭时运行 (可选)
    pool_manager.scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "WARP Proxy Pool is running!"}

@app.get("/get_proxy")
def get_proxy():
    proxy = pool_manager.get_proxy()
    if not proxy:
        raise HTTPException(status_code=503, detail="No healthy proxies available.")
    return {"proxy": proxy}

@app.get("/status")
def get_status():
    return pool_manager.get_full_status()