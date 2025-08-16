import numpy as np
import hashlib
import json
from datasketch import MinHash, MinHashLSH
from typing import List, Dict, Tuple


class LSHService:
    def __init__(self, num_perm=128, threshold=0.6):  # 降低阈值到0.6
        self.num_perm = num_perm
        self.threshold = threshold
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        # 使用固定种子确保结果可重复
        self.random_seed = 42

    def vectorize_transfer_data(self, transfer_data: List[Dict], data_type: str) -> List[float]:
        """将转会数据向量化"""
        vector = []
        for transfer in transfer_data:
            if data_type == 'income':
                # 卖方收入数据
                vector.append(float(transfer.get('transfer_fee', 0)))
                vector.append(float(transfer.get('player_market_value', 0)))
                # 添加更多特征以提高区分度
                vector.append(
                    float(transfer.get('transfer_fee', 0)) / max(float(transfer.get('player_market_value', 1)), 1))
            elif data_type == 'expense':
                # 买方支出数据
                vector.append(float(transfer.get('transfer_fee', 0)))
                vector.append(float(transfer.get('additional_costs', 0)))
                # 添加总成本
                vector.append(float(transfer.get('transfer_fee', 0)) + float(transfer.get('additional_costs', 0)))

        # 如果向量为空，返回默认值
        if not vector:
            vector = [0.0, 0.0, 0.0]

        return vector

    def create_income_index(self, club_id: str, transfer_records: List[Dict]) -> str:
        """创建俱乐部转会收入索引 (对应论文中的步骤1)"""
        # 构建收入向量 TIVA
        income_vector = self.vectorize_transfer_data(transfer_records, 'income')

        # 使用俱乐部ID作为种子确保同一俱乐部的结果一致
        seed_value = hash(club_id + "income") % (2 ** 32)
        np.random.seed(seed_value)

        # 重复y次生成索引
        y = 10  # 索引维度
        hash_values = []

        for i in range(y):
            # 为每个维度使用不同但确定的种子
            np.random.seed(seed_value + i)
            random_vec = np.random.uniform(-1, 1, len(income_vector))

            # 计算投影
            if len(income_vector) > 0:
                proj = np.dot(income_vector, random_vec)
            else:
                proj = 0

            # 二值化
            hash_values.append(1 if proj >= 0 else 0)

        # 生成最终的LSH索引
        index_string = ''.join(map(str, hash_values))
        return index_string

    def create_expense_index(self, club_id: str, transfer_records: List[Dict]) -> str:
        """创建俱乐部转会支出索引 (对应论文中的步骤2)"""
        # 构建支出向量 TEVA
        expense_vector = self.vectorize_transfer_data(transfer_records, 'expense')

        # 使用俱乐部ID作为种子确保同一俱乐部的结果一致
        seed_value = hash(club_id + "expense") % (2 ** 32)

        # 重复y次生成索引
        y = 10  # 索引维度
        hash_values = []

        for i in range(y):
            # 为每个维度使用不同但确定的种子
            np.random.seed(seed_value + i)
            random_vec = np.random.uniform(-1, 1, len(expense_vector))

            # 计算投影
            if len(expense_vector) > 0:
                proj = np.dot(expense_vector, random_vec)
            else:
                proj = 0

            # 二值化
            hash_values.append(1 if proj >= 0 else 0)

        # 生成最终的LSH索引
        index_string = ''.join(map(str, hash_values))
        return index_string

    def detect_money_laundering(self, income_index: str, expense_index: str) -> Tuple[bool, float, str]:
        """洗钱检测判断 (对应论文中的步骤3)"""
        # 计算汉明距离相似度
        if len(income_index) != len(expense_index):
            return False, 0.0, "索引长度不匹配"

        # 计算相似度
        matching_bits = sum(1 for a, b in zip(income_index, expense_index) if a == b)
        similarity = matching_bits / len(income_index)

        # 调整判断逻辑：相似度太高或太低都可疑
        # 正常转会应该有中等相似度
        is_legitimate = 0.3 <= similarity <= 0.8

        details = {
            'similarity_score': similarity,
            'threshold_range': [0.3, 0.8],
            'income_index': income_index,
            'expense_index': expense_index,
            'is_legitimate': is_legitimate,
            'reasoning': self._get_reasoning(similarity)
        }

        detail_string = json.dumps(details, indent=2)

        return is_legitimate, similarity, detail_string

    def _get_reasoning(self, similarity: float) -> str:
        """根据相似度提供判断理由"""
        if similarity < 0.3:
            return "相似度过低，可能存在数据操纵"
        elif similarity > 0.9:
            return "相似度过高，可能存在洗钱行为"
        else:
            return "相似度正常，转会合法"

    def validate_transfer(self, selling_club_transfers: List[Dict],
                          buying_club_transfers: List[Dict]) -> Dict:
        """完整的转会验证流程"""
        # 步骤1: 创建卖方收入索引
        income_index = self.create_income_index("seller", selling_club_transfers)

        # 步骤2: 创建买方支出索引
        expense_index = self.create_expense_index("buyer", buying_club_transfers)

        # 步骤3: 洗钱检测
        is_legitimate, similarity, details = self.detect_money_laundering(income_index, expense_index)

        return {
            'income_index': income_index,
            'expense_index': expense_index,
            'is_legitimate': is_legitimate,
            'similarity_score': similarity,
            'validation_details': details
        }