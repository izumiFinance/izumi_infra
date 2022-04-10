# -*- coding: utf-8 -*-
import networkx as nx

class SwapPriceFacade():

    def __init__(self):
        super().__init__()
        self.token_swap_graph = nx.Graph()

    def set_or_update_pool_price(self, tokenX_addr: str, tokenY_addr: str, price: float):
        """
        price = tokenX / tokenY
        TODO 不同 fee 隔离？
        """
        tokenX, tokenY = tokenX_addr.lower(), tokenY_addr.lower()
        self._init_pool_price_from_db_if_need()
        if self.token_swap_graph.has_edge(tokenX, tokenY):
            self.token_swap_graph[tokenY][tokenY]['price'] = price
        else:
            self.token_swap_graph.add_edge(tokenX, tokenY, price=price)

    def get_token_usd_price(self, token_addr, usd_token_addr) -> float:
        # TODO 路径不存在
        try:
            sp = nx.shortest_path(self.token_swap_graph, token_addr.lower(), usd_token_addr.lower())
        except nx.NodeNotFound:
            return 0

        price = 1
        for i in range(len(sp)-1):
            source, target = sp[i], sp[i+1]
            edge = self.token_swap_graph[source][target]
            toggle_edge_price = source > target
            price = price * (1 / edge['price'] if toggle_edge_price else edge['price'])

        return price
