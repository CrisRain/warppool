# controller-app/health_checker.py
import requests
import time
import logging

class HealthChecker:
    def __init__(self, config: dict):
        """
        Initializes the HealthChecker with configuration.
        :param config: A dictionary containing 'timeout_seconds' and 'check_urls'.
        """
        self.timeout = config.get('timeout_seconds', 10)
        self.urls = config.get('check_urls', ["https://www.cloudflare.com/cdn-cgi/trace"])
        if not self.urls:
            # 确保至少有一个默认 URL
            self.urls = ["https://www.cloudflare.com/cdn-cgi/trace"]
        logging.info(f"HealthChecker initialized with timeout={self.timeout}s and {len(self.urls)} check URLs.")

    def check_proxy(self, proxy_address: str) -> dict:
        """
        Checks a SOCKS5 proxy by trying a list of URLs.
        Returns a dict with 'ok', 'latency', 'ip', etc.
        """
        proxies = {'http': proxy_address, 'https': proxy_address}
        errors = []

        for url in self.urls:
            result = {"ok": False, "latency": -1, "ip": None, "error": None}
            try:
                start_time = time.time()
                response = requests.get(url, proxies=proxies, timeout=self.timeout)
                latency = time.time() - start_time

                if response.status_code == 200:
                    result["ok"] = True
                    result["latency"] = round(latency * 1000)  # ms
                    # 解析IP
                    for line in response.text.split('\\n'):
                        if line.startswith('ip='):
                            result['ip'] = line[3:]
                            break
                    # 只要有一个成功，就立即返回
                    return result
                else:
                    error_message = f"URL {url} returned status code: {response.status_code}"
                    errors.append(error_message)

            except Exception as e:
                error_message = f"URL {url} failed with exception: {e}"
                errors.append(error_message)
        
        # 如果所有 URL 都失败了
        logging.debug(f"All health check URLs failed for proxy {proxy_address}. Errors: {errors}")
        final_error = "; ".join(errors)
        return {"ok": False, "latency": -1, "ip": None, "error": final_error}