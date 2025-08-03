# controller-app/pool_manager.py
import threading
import random
import logging
import yaml
import copy
from typing import List, Dict
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from . import warp_controller, health_checker

# --- 新增常量 ---
RECOVERY_MAX_RETRIES = 3
RECOVERY_COOLDOWN_SECONDS = 300  # 5 分钟
# ----------------

class ProxyPoolManager:
    def __init__(self, config_path='config.yaml'):
        config = self._load_config(config_path)
        self.instances = config.get('warp_instances', [])
        health_checker_config = config.get('health_checker', {})
        
        self.health_checker = health_checker.HealthChecker(health_checker_config)

        self.pool_status = {
            inst['name']: {
                "status": "initializing",
                "recovery_attempts": 0,
                "last_recovery_attempt_time": None
            } for inst in self.instances
        }
        self.lock = threading.Lock()
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.check_all_proxies, 'interval', seconds=60, id='health_check_job')

    def _load_config(self, config_path: str) -> Dict:
        logging.info(f"Loading configuration from {config_path}...")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            instances = []
            for inst in config.get('warp_instances', []):
                instance_name = inst['name']
                socks5_port = inst['socks5_port']
                # http_proxy_port = inst['http_proxy_port'] # 如果需要，也可以加载
                
                # 注意：这里的地址现在是相对于 Docker Compose 网络内部的
                proxy_address = f"socks5://{instance_name}:{socks5_port}"
                
                instances.append({
                    'name': instance_name,
                    'proxy_address': proxy_address
                })
            
            logging.info(f"Loaded {len(instances)} WARP instances.")
            config['warp_instances'] = instances
            return config
        except FileNotFoundError:
            logging.error(f"Configuration file not found at {config_path}. Please ensure it exists.")
            return {}
        except Exception as e:
            logging.error(f"Error loading or parsing configuration file: {e}")
            return {}

    def start(self):
        logging.info("Starting Proxy Pool Manager...")
        # 首次立即检查
        self.check_all_proxies()
        self.scheduler.start()

    def get_healthy_proxies(self) -> List[Dict]:
        with self.lock:
            healthy_proxies = [
                inst['proxy_address'] for inst in self.instances
                if self.pool_status[inst['name']]['status'] == 'healthy'
            ]
            return healthy_proxies

    def get_proxy(self) -> str | None:
        with self.lock:
            healthy_proxies = [
                inst['proxy_address'] for inst in self.instances
                if self.pool_status[inst['name']]['status'] == 'healthy'
            ]
            if not healthy_proxies:
                return None
            return random.choice(healthy_proxies)

    def get_full_status(self) -> Dict:
        with self.lock:
            return copy.deepcopy(self.pool_status)

    def check_all_proxies(self):
        logging.info("Running scheduled health check for all proxies...")
        for instance in self.instances:
            self.check_and_recover(instance)

    def check_and_recover(self, instance: Dict):
        container_name = instance['name']
        proxy_address = instance['proxy_address']
        
        health = self.health_checker.check_proxy(proxy_address)
        
        with self.lock:
            status = self.pool_status[container_name]

            if health['ok']:
                if status['status'] != 'healthy':
                    logging.info(f"Proxy {container_name} is now healthy. IP: {health['ip']}, Latency: {health['latency']}ms")
                    status.update({
                        "status": "healthy",
                        "ip": health['ip'],
                        "latency": health['latency'],
                        "proxy_address": proxy_address,
                    })
                    # 如果实例恢复健康，重置恢复尝试计数
                    status['recovery_attempts'] = 0
                    status['last_recovery_attempt_time'] = None
            else:
                logging.warning(f"Proxy {container_name} is unhealthy. Reason: {health['error']}.")

                # 检查是否达到最大重试次数
                if status['recovery_attempts'] >= RECOVERY_MAX_RETRIES:
                    if status['status'] != 'PERMANENTLY_FAILED':
                        logging.error(f"Proxy {container_name} has failed recovery {RECOVERY_MAX_RETRIES} times. Marking as PERMANENTLY_FAILED.")
                        status['status'] = 'PERMANENTLY_FAILED'
                    return

                # 检查是否处于冷却期
                if status['last_recovery_attempt_time']:
                    cooldown_period = timedelta(seconds=RECOVERY_COOLDOWN_SECONDS)
                    if datetime.now() - status['last_recovery_attempt_time'] < cooldown_period:
                        logging.info(f"Proxy {container_name} is in recovery cooldown. Skipping recovery attempt.")
                        return
                
                logging.info(f"Attempting recovery for {container_name} (Attempt {status['recovery_attempts'] + 1})...")
                
                # 更新恢复尝试状态
                status['recovery_attempts'] += 1
                status['last_recovery_attempt_time'] = datetime.now()
                status['status'] = 'recovering'
                status['error'] = health['error']

                # 恢复逻辑
                warp_controller.disconnect(container_name)
                if warp_controller.connect(container_name):
                    logging.info(f"Successfully reconnected {container_name}.")
                    # 恢复后，我们不会立即将其标记为“healthy”，而是等待下一次健康检查来确认。
                    # 但我们会重置计数器，因为我们已经成功执行了一次恢复操作。
                    status['recovery_attempts'] = 0
                    status['last_recovery_attempt_time'] = None # 清除时间戳以允许立即进行下一次检查
                    # 状态将保持为 'recovering' 直到下一次健康检查
                else:
                    logging.error(f"Failed to reconnect {container_name}.")
                    status['status'] = 'failed' # 标记为 'failed'，但不是 'PERMANENTLY_FAILED'

# The pool_manager is now initialized with the path to the config file.
# The actual path inside the container will be determined by the docker-compose.yml volume mount.
pool_manager = ProxyPoolManager(config_path='/app/config.yaml')