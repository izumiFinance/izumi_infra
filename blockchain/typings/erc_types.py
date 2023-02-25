# -*- coding: utf-8 -*-
from typing import TypedDict

ERC721Transfer = TypedDict('ERC721Transfer', {'from': str, 'to': str, 'tokenId': int})
