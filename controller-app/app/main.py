import asyncio
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine
from .pool_manager import pool_manager
from .dynamic_proxy import start_proxy_server

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="WARP Pool Controller")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    # Load instances from DB at startup
    pool_manager.load_instances_from_db()
    # Start health checks in the background
    asyncio.create_task(pool_manager.run_health_checks())
    # Start the unified SOCKS5 proxy server
    asyncio.create_task(start_proxy_server())

@app.get("/api/instances", response_model=List[schemas.WarpInstance])
def read_instances(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    instances = crud.get_instances(db, skip=skip, limit=limit)
    return instances

@app.post("/api/instances", response_model=schemas.WarpInstance)
def create_instance(instance: schemas.WarpInstanceCreate, db: Session = Depends(get_db)):
    db_instance_by_name = crud.get_instance_by_name(db, name=instance.name)
    if db_instance_by_name:
        raise HTTPException(status_code=400, detail=f"Instance with name '{instance.name}' already registered")
    # You might want to check for port conflicts as well
    new_instance = crud.create_instance(db=db, instance=instance)
    pool_manager.load_instances_from_db() # Reload to include the new one
    return new_instance

@app.get("/api/instances/status")
async def get_instances_status():
    status = await pool_manager.get_status()
    return status

@app.get("/api/instances/{instance_id}", response_model=schemas.WarpInstance)
def read_instance(instance_id: int, db: Session = Depends(get_db)):
    db_instance = crud.get_instance(db, instance_id=instance_id)
    if db_instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    return db_instance

@app.put("/api/instances/{instance_id}", response_model=schemas.WarpInstance)
def update_instance(instance_id: int, instance_in: schemas.WarpInstanceUpdate, db: Session = Depends(get_db)):
    db_instance = crud.get_instance(db, instance_id=instance_id)
    if db_instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    updated_instance = crud.update_instance(db=db, db_instance=db_instance, instance_in=instance_in)
    pool_manager.load_instances_from_db() # Reload to reflect changes
    return updated_instance

@app.delete("/api/instances/{instance_id}", response_model=schemas.WarpInstance)
def delete_instance(instance_id: int, db: Session = Depends(get_db)):
    db_instance = crud.get_instance(db, instance_id=instance_id)
    if db_instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Stop and remove container before deleting from DB
    controller = pool_manager.get_instance(instance_id)
    if controller:
        controller.stop_and_remove_container()

    deleted_instance = crud.delete_instance(db=db, instance_id=instance_id)
    pool_manager.load_instances_from_db() # Reload to remove it
    return deleted_instance

@app.post("/api/instances/{instance_id}/reconnect")
async def reconnect_instance(instance_id: int):
    controller = pool_manager.get_instance(instance_id)
    if not controller:
        raise HTTPException(status_code=404, detail="Instance not found in active pool")
    
    asyncio.create_task(controller.reconnect())
    return {"message": f"Reconnection process for instance {instance_id} started."}

@app.post("/api/instances/{instance_id}/check")
async def check_instance(instance_id: int):
    controller = pool_manager.get_instance(instance_id)
    if not controller:
        raise HTTPException(status_code=404, detail="Instance not found in active pool")
    
    asyncio.create_task(pool_manager.health_checker.check_instance(controller))
    await asyncio.sleep(1) # Give it a moment to update
    return controller.get_status()

@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await pool_manager.connection_manager.connect(websocket)
    try:
        # Send initial status
        initial_status = await pool_manager.get_status()
        await websocket.send_json({"type": "initial_status", "data": initial_status})
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        pool_manager.connection_manager.disconnect(websocket)
        print(f"Client disconnected from WebSocket.")