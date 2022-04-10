# -*- coding: utf-8 -*-

def tick2PriceSqrt(tick):
    return (1.0001 ** tick) ** 0.5;

def tick2Price(tick: int) -> float:
    return 1.0001 ** tick;

def liquidity2TokenAmount(liquidity, lowerTick, upperTick, currentTick):
    tokenAAmount = 0;
    tokenBAmount = 0;

    # only tokenA
    if currentTick < lowerTick:
        tokenAAmount = liquidity * (1 / tick2PriceSqrt(lowerTick) - 1 / tick2PriceSqrt(upperTick));
    elif currentTick > upperTick :
        tokenBAmount = liquidity * (tick2PriceSqrt(upperTick) - tick2PriceSqrt(lowerTick));
    else:
        tokenAAmount = liquidity * (1 / tick2PriceSqrt(currentTick) - 1 / tick2PriceSqrt(upperTick));
        tokenBAmount = liquidity * (tick2PriceSqrt(currentTick) - tick2PriceSqrt(lowerTick));

    return [tokenAAmount, tokenBAmount];
