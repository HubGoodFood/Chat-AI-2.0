"""
数据处理模块 - 处理产品数据和政策数据
"""
import pandas as pd
import json
import jieba
from fuzzywuzzy import fuzz
from typing import List, Dict, Any, Optional


class DataProcessor:
    def __init__(self):
        self.products_df = None
        self.policy_data = None
        self.product_keywords = {}
        self.policy_keywords = {}
        
    def load_data(self):
        """加载产品和政策数据"""
        try:
            # 加载产品数据
            self.products_df = pd.read_csv('data/products.csv')
            # 清理列名中的空格
            self.products_df.columns = self.products_df.columns.str.strip()

            # 加载政策数据
            with open('data/policy.json', 'r', encoding='utf-8') as f:
                self.policy_data = json.load(f)
            
            # 建立关键词索引
            self._build_product_keywords()
            self._build_policy_keywords()
            
            print("数据加载成功！")
            print(f"产品数量: {len(self.products_df)}")
            print(f"政策板块: {len(self.policy_data['sections'])}")
            
        except Exception as e:
            print(f"数据加载失败: {e}")
            
    def _build_product_keywords(self):
        """建立产品关键词索引"""
        for idx, row in self.products_df.iterrows():
            keywords = []
            
            # 产品名称分词
            product_name = str(row['ProductName']).strip()
            keywords.extend(jieba.lcut(product_name))
            
            # 类别关键词
            category = str(row['Category']).strip()
            keywords.extend(jieba.lcut(category))
            
            # 显式关键词
            if pd.notna(row['Keywords']) and str(row['Keywords']).strip():
                explicit_keywords = str(row['Keywords']).split(';')
                keywords.extend([kw.strip() for kw in explicit_keywords])
            
            # 产地关键词
            origin = str(row['Origin']).strip()
            if origin and origin != 'nan':
                keywords.extend(jieba.lcut(origin))
            
            # 去重并过滤
            keywords = list(set([kw for kw in keywords if len(kw) > 1]))
            self.product_keywords[idx] = keywords
            
    def _build_policy_keywords(self):
        """建立政策关键词索引"""
        policy_mapping = {
            'mission': ['使命', '理念', '介绍', '关于我们', '拼台'],
            'group_rules': ['群规', '规则', '禁止', '违规', '管理'],
            'product_quality': ['质量', '品质', '退款', '换货', '问题', '保证'],
            'delivery': ['配送', '送货', '运费', '起送', '免费配送', '外围'],
            'payment': ['付款', '支付', 'venmo', '现金', '备注', '手续费'],
            'pickup': ['取货', '自取', 'malden', 'chinatown', '取货点'],
            'after_sale': ['售后', '退款', '更换', '质量问题', '反馈'],
            'community': ['社区', '拼友', '互助', '感恩', '建议']
        }
        
        for section, keywords in policy_mapping.items():
            self.policy_keywords[section] = keywords
            
    def search_products(self, query: str, limit: int = 5) -> List[Dict]:
        """搜索产品"""
        if self.products_df is None:
            return []
            
        query_keywords = jieba.lcut(query.lower())
        results = []
        
        for idx, row in self.products_df.iterrows():
            score = 0
            
            # 产品名称匹配
            product_name = str(row['ProductName']).lower()
            for qk in query_keywords:
                if qk in product_name:
                    score += 10
                else:
                    # 模糊匹配
                    fuzzy_score = fuzz.partial_ratio(qk, product_name)
                    if fuzzy_score > 70:
                        score += fuzzy_score / 10
            
            # 关键词匹配
            product_keywords = self.product_keywords.get(idx, [])
            for qk in query_keywords:
                for pk in product_keywords:
                    if qk == pk.lower():
                        score += 8
                    elif fuzz.ratio(qk, pk.lower()) > 80:
                        score += 5
            
            # 类别匹配
            category = str(row['Category']).lower()
            for qk in query_keywords:
                if qk in category:
                    score += 6
                    
            if score > 0:
                product_info = {
                    'name': row['ProductName'],
                    'specification': row['Specification'],
                    'price': row['Price'],
                    'unit': row['Unit'],
                    'category': row['Category'],
                    'keywords': row['Keywords'] if pd.notna(row['Keywords']) else '',
                    'taste': row['Taste'] if pd.notna(row['Taste']) else '',
                    'origin': row['Origin'] if pd.notna(row['Origin']) else '',
                    'benefits': row['Benefits'] if pd.notna(row['Benefits']) else '',
                    'suitable_for': row['SuitableFor'] if pd.notna(row['SuitableFor']) else '',
                    'score': score
                }
                results.append(product_info)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def search_policies(self, query: str) -> List[Dict]:
        """搜索政策信息"""
        if self.policy_data is None:
            return []
            
        query_keywords = jieba.lcut(query.lower())
        results = []
        
        for section_name, keywords in self.policy_keywords.items():
            score = 0
            
            # 关键词匹配
            for qk in query_keywords:
                for pk in keywords:
                    if qk == pk or qk in pk or pk in qk:
                        score += 10
                    elif fuzz.ratio(qk, pk) > 70:
                        score += 5
            
            if score > 0:
                section_content = self.policy_data['sections'][section_name]
                policy_info = {
                    'section': section_name,
                    'content': section_content,
                    'score': score
                }
                results.append(policy_info)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """根据产品名称获取详细信息"""
        if self.products_df is None:
            return None
            
        # 精确匹配
        exact_match = self.products_df[self.products_df['ProductName'].str.contains(name, na=False)]
        if not exact_match.empty:
            row = exact_match.iloc[0]
            return {
                'name': row['ProductName'],
                'specification': row['Specification'],
                'price': row['Price'],
                'unit': row['Unit'],
                'category': row['Category'],
                'keywords': row['Keywords'] if pd.notna(row['Keywords']) else '',
                'taste': row['Taste'] if pd.notna(row['Taste']) else '',
                'origin': row['Origin'] if pd.notna(row['Origin']) else '',
                'benefits': row['Benefits'] if pd.notna(row['Benefits']) else '',
                'suitable_for': row['SuitableFor'] if pd.notna(row['SuitableFor']) else ''
            }
        return None
    
    def get_all_categories(self) -> List[str]:
        """获取所有产品类别"""
        if self.products_df is None:
            return []
        return self.products_df['Category'].unique().tolist()
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """根据类别获取产品列表"""
        if self.products_df is None:
            return []
            
        category_products = self.products_df[self.products_df['Category'] == category]
        results = []
        
        for _, row in category_products.iterrows():
            product_info = {
                'name': row['ProductName'],
                'price': row['Price'],
                'unit': row['Unit'],
                'taste': row['Taste'] if pd.notna(row['Taste']) else '',
                'origin': row['Origin'] if pd.notna(row['Origin']) else ''
            }
            results.append(product_info)
            
        return results


# 测试代码
if __name__ == "__main__":
    processor = DataProcessor()
    processor.load_data()
    
    # 测试产品搜索
    print("\n=== 产品搜索测试 ===")
    results = processor.search_products("苹果")
    for result in results:
        print(f"产品: {result['name']}, 价格: ${result['price']}, 分数: {result['score']}")
    
    # 测试政策搜索
    print("\n=== 政策搜索测试 ===")
    policy_results = processor.search_policies("配送")
    for result in policy_results:
        print(f"政策板块: {result['section']}, 分数: {result['score']}")
