# -*- coding: utf-8 -*-
from decimal import Decimal

def convert_amount(from_amount: str, from_decimals: int, to_decimal: int):
    """
    from_amount: Integer number not float, eg: 1.1*10^18(1.1 ETH)
    to_amount Integer number not float, eg: 1.1*10^18(1.1 ETH)
    """
    to_amount = Decimal(from_amount) * (10 ** to_decimal)  / (10 ** from_decimals)
    return int(to_amount)

def sort_addr(addr0: str, addr1: str):
    if addr0.lower() > addr1.lower():
        return addr1, addr0
    return addr0, addr1
