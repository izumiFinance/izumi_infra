# -*- coding: utf-8 -*-

def addr_identity(chainId: int, addr: str) -> str:
    return f"{chainId}-{addr.lower()}"
