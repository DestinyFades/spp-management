from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
import asyncio

class DistributionService:
    @staticmethod
    async def distribute(selected_ids: List[int], total_sum: float, tree: Dict) -> Dict:
        total = Decimal(str(total_sum))
        
        # 1. Найти выбранные узлы в дереве
        selected_nodes = []
        
        def find_selected_nodes(node: Dict):
            if node.get("id") in selected_ids:
                selected_nodes.append(node)
            for child in node.get("children", []):
                find_selected_nodes(child)
        
        find_selected_nodes(tree)
        
        if not selected_nodes:
            return tree
        
        # 2. Распределить сумму между выбранными узлами
        share = total / len(selected_nodes)
        for node in selected_nodes:
            await DistributionService._distribute_recursive(node, share)
        
        # 3. Агрегировать суммы (пересчитать суммы родителей)
        await DistributionService._aggregate(tree)
        return tree

    @staticmethod
    async def _distribute_recursive(node: Dict, amount: Decimal):
        children = node.get("children", [])
        
        if not children:
            # Листовой узел: присваиваем сумму
            node["allocated"] = float(amount.quantize(Decimal('0.01')))
            return
        
        # Распределяем сумму между дочерними узлами
        share = amount / len(children)
        tasks = [DistributionService._distribute_recursive(child, share) for child in children]
        await asyncio.gather(*tasks)

    @staticmethod
    async def _aggregate(node: Dict):
        children = node.get("children", [])
        if children:
            for child in children:
                await DistributionService._aggregate(child)
            # Суммируем все выделенные суммы детей
            total = sum(child.get("allocated", 0) for child in children)
            node["allocated"] = total
