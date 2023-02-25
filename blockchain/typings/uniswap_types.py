# -*- coding: utf-8 -*-
from typing import TypedDict, List

class PositionsReturnDict(TypedDict):
    nonce: int
    operator: str
    token0: str
    token1: str
    fee: int
    tickLower: int
    tickUpper: int
    liquidity: int
    feeGrowthInside0LastX128: int
    feeGrowthInside1LastX128: int
    tokensOwed0: int
    tokensOwed1: int
