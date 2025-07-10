# -*- coding: utf-8 -*-
from time import time
import logging

logger = logging.getLogger(__name__)


class RenewalManager:
    def __init__(self, redis_instance, key: str, initial_ttl: int, min_renewal_interval: int = 60):
        self.redis = redis_instance
        self.key = key
        self.initial_ttl = initial_ttl
        self.min_renewal_interval = min_renewal_interval
        self.last_renewal_time = time()

    def renew(self, force: bool = False) -> bool:
        current_time = time()
        if not force and not self.should_renew(): return False

        try:
            self.redis.expire(self.key, self.initial_ttl)
            self.last_renewal_time = current_time
            logger.info(f"Renewed key {self.key} with TTL {self.initial_ttl} seconds")
            return True
        except Exception as e:
            logger.error(f"Failed to renew key {self.key}: {str(e)}")
            return False

    def should_renew(self) -> bool:
        current_time = time()
        since_last_renewal_interval = current_time - self.last_renewal_time
        if since_last_renewal_interval < self.min_renewal_interval:
            return False

        return True

class DefaultRenewalManager(RenewalManager):
    def __init__(self):
        super().__init__(None, None, 0, 0)

    def renew(self, force: bool = False) -> bool:
        logger.debug(f"Should not call me to renew, please check running environment")
        return False

FAIL_BACK_RENEWAL_MANAGER = DefaultRenewalManager()
