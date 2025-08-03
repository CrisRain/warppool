import asyncio
import docker
from sqlalchemy.orm import Session
from typing import List, Dict

from . import crud, schemas
from .health_checker import HealthChecker
from .warp_controller import WarpController
from .database import SessionLocal
from starlette.websockets import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

class PoolManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.instances: Dict[int, WarpController] = {}
        self.health_checker = HealthChecker()
        self.connection_manager = ConnectionManager()
        self.lock = asyncio.Lock()
        self.round_robin_index = 0

    def load_instances_from_db(self):
        db: Session = SessionLocal()
        try:
            db_instances = crud.get_instances(db)
            print(f"Loading {len(db_instances)} instances from database...")
            for instance_model in db_instances:
                if instance_model.id not in self.instances:
                    controller = WarpController(
                        docker_client=self.docker_client,
                        instance_id=instance_model.id,
                        name=instance_model.name,
                        socks5_port=instance_model.socks5_port,
                    )
                    self.instances[instance_model.id] = controller
            # Clean up instances that are no longer in the DB
            for instance_id in list(self.instances.keys()):
                if not any(db_inst.id == instance_id for db_inst in db_instances):
                     del self.instances[instance_id]

        finally:
            db.close()

    async def get_status(self):
        status_list = []
        for controller in self.instances.values():
            status = controller.get_status()
            status_list.append(status)
        return status_list

    async def run_health_checks(self):
        while True:
            self.load_instances_from_db()
            if not self.instances:
                print("No instances to check. Waiting...")
                await asyncio.sleep(30)
                continue

            tasks = [
                self.health_checker.check_instance(instance)
                for instance in self.instances.values()
            ]
            await asyncio.gather(*tasks)
            status = await self.get_status()
            await self.connection_manager.broadcast({"type": "status_update", "data": status})
            await asyncio.sleep(60) # Check every 60 seconds

    def get_instance(self, instance_id: int):
        return self.instances.get(instance_id)

    def get_healthy_instance(self):
        healthy_instances = [
            inst for inst in self.instances.values() if inst.get_status().get("is_healthy")
        ]
        if not healthy_instances:
            return None

        # Simple round-robin
        async def get_next():
            async with self.lock:
                if self.round_robin_index >= len(healthy_instances):
                    self.round_robin_index = 0
                instance = healthy_instances[self.round_robin_index]
                self.round_robin_index += 1
                return instance
        
        # This is a bit of a workaround to call an async def from a sync def
        # In a real-world, more complex scenario, you might rethink the structure
        # but for this purpose, it's acceptable.
        return asyncio.run(get_next())

pool_manager = PoolManager()