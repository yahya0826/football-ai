"""
知识百库服务 - 世界杯知识问答与内容浏览
"""
import os
import sys
import io
import json
import faiss
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from openai import OpenAI

# Fix Windows console encoding issues with Chinese characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class KnowledgeBaseService:
    """世界杯知识库服务"""

    def __init__(self, kb_dir: str = "data/knowledge"):
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.knowledge_data: List[Dict] = []
        self.chunks: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self.team_profiles: List[Dict] = []
        self.tactical_glossary: List[Dict] = []
        self.formation_encyclopedia: List[Dict] = []
        self.formation_matchup: List[Dict] = []
        self.playing_styles: List[Dict] = []
        self.style_matchup: List[Dict] = []
        self.position_requirements: List[Dict] = []
        self.client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))) if (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")) else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self._initialize_knowledge_base()
        self._load_extended_content()

    def _initialize_knowledge_base(self):
        """初始化知识库"""
        self._load_knowledge_data()
        if self.chunks:
            self._build_index()

    def _load_knowledge_data(self):
        """加载知识数据"""
        kb_file = self.kb_dir / "worldcup_knowledge.json"

        # 如果文件不存在，创建默认知识库
        if not kb_file.exists():
            self._create_default_knowledge()
            return

        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                self.knowledge_data = json.load(f)

            # 提取文本块用于索引
            for item in self.knowledge_data:
                if 'content' in item:
                    self.chunks.append(item['content'])
                elif 'question' in item and 'answer' in item:
                    self.chunks.append(f"问题：{item['question']}\n答案：{item['answer']}")

            print(f"已加载 {len(self.chunks)} 条知识条目")
        except Exception as e:
            print(f"加载知识库失败: {e}")
            self._create_default_knowledge()

    def _create_default_knowledge(self):
        """创建默认世界杯知识库"""
        self.knowledge_data = [
            # 世界杯历史
            {
                "category": "历史",
                "question": "第一届世界杯在哪里举办？",
                "answer": "第一届世界杯于1930年在乌拉圭举办，共有13支球队参加决赛圈比赛。"
            },
            {
                "category": "历史",
                "question": "哪支球队获得世界杯冠军最多？",
                "answer": "巴西队获得世界杯冠军最多，共5次（1958、1962、1970、1994、2002）。"
            },
            {
                "category": "历史",
                "question": "世界杯每隔几年举办一次？",
                "answer": "世界杯每隔4年举办一次，自1930年首届比赛以来，除了1942年和1946年因二战停办外，每四年举办一次。"
            },

            # 2026世界杯
            {
                "category": "2026世界杯",
                "question": "2026世界杯在哪里举办？",
                "answer": "2026年世界杯将由美国、加拿大和墨西哥联合举办，这是历史上首次由三国联合举办世界杯。"
            },
            {
                "category": "2026世界杯",
                "question": "2026世界杯有多少支球队参赛？",
                "answer": "2026年世界杯将扩军至48支球队参赛，相比2022年的32支球队增加了16个名额。"
            },
            {
                "category": "2026世界杯",
                "question": "2026世界杯赛制是怎样的？",
                "answer": "48支球队将分成12个小组，每组4队，小组赛的前两名和成绩最好的8个第三名晋级32强淘汰赛。"
            },

            # 规则
            {
                "category": "规则",
                "question": "世界杯加时赛规则是什么？",
                "answer": "淘汰赛阶段，如果90分钟打平，将进行上下半场各15分钟的加时赛（共30分钟）。如果加时赛仍然打平，则进行点球大战。"
            },
            {
                "category": "规则",
                "question": "点球大战规则是什么？",
                "answer": "点球大战中，双方交替罚点球，各罚5轮。如果5轮后仍是平局，继续罚点球直到分出胜负。守门员在球门线上不能移动。"
            },
            {
                "category": "规则",
                "question": "越位规则是什么？",
                "answer": "越位是指进攻球员在接球瞬间，比球和倒数第二个防守球员（通常包括守门员）更接近对方球门线。处于越位位置并不犯规，只有实际参与进攻才构成越位犯规。"
            },
            {
                "category": "规则",
                "question": "黄牌和红牌的区别是什么？",
                "answer": "黄牌是警告，累计两张黄牌等于一张红牌。红牌是直接罚下，被红牌罚下的球员不能继续参加比赛，且下一场也要停赛。"
            },

            # 术语
            {
                "category": "术语",
                "question": "什么是xG（期望进球）？",
                "answer": "xG（Expected Goals）是一种衡量射门质量的指标，根据射门位置、角度、守门员位置等因素计算每次射门的进球概率。xG总和可以预测球队理论上应该进的球数。"
            },
            {
                "category": "术语",
                "question": "什么是帽子戏法？",
                "answer": "帽子戏法指一名球员在一场比赛中打进3个进球。这个术语源于19世纪的板球运动，当时裁判员因投手出色表现而奖励一顶帽子。"
            },
            {
                "category": "术语",
                "question": "什么是越位陷阱？",
                "answer": "越位陷阱是防守球队故意制造越位位置的战术，通过整体后撤让进攻球员处于越位位置，从而破坏对方的进攻节奏。"
            },
            {
                "category": "术语",
                "question": "什么是防守反击？",
                "answer": "防守反击是一种战术，球队在防守时重兵囤积在中后场，一旦夺回球权就迅速发动快速反击，利用对方压上后的空档。"
            },

            # 著名球员
            {
                "category": "球员",
                "question": "世界杯历史最佳射手是谁？",
                "answer": "世界杯历史最佳射手是德国传奇前锋米洛斯拉夫·克洛泽，他在4届世界杯共打进16球。"
            },
            {
                "category": "球员",
                "question": "谁是世界杯出场次数最多的球员？",
                "answer": "德国传奇中场洛塔尔·马特乌斯保持着世界杯出场纪录，共参加5届世界杯，出场25次。"
            },
            {
                "category": "球员",
                "question": "贝利赢得过几次世界杯？",
                "answer": "球王贝利职业生涯赢得3次世界杯冠军，分别是1958年（17岁）、1962年和1970年。"
            },

            # 有趣知识
            {
                "category": "趣闻",
                "question": "世界杯最快的进球是多少秒？",
                "answer": "世界杯最快进球纪录由土耳其球员哈坎·苏克保持，他在2002年对阵韩国的比赛中仅用11秒就破门得分。"
            },
            {
                "category": "趣闻",
                "question": "哪届世界杯观众人数最多？",
                "answer": "1994年美国世界杯观众人数最多，共有超过358万人次现场观战，场均观赛人数超过7万。"
            },
            {
                "category": "趣闻",
                "question": "世界杯决赛最常见的比分是什么？",
                "answer": "世界杯决赛最常见的比分是1-0，共有8次决赛以此比分结束。其次是2-1和2-0，各有5次。"
            },

            # 中国队
            {
                "category": "中国队",
                "question": "中国队参加过几次世界杯？",
                "answer": "中国国家男子足球队只参加过一次世界杯正赛，那是2002年韩日世界杯，当时在小组赛中0胜3负未能晋级。"
            },
            {
                "category": "中国队",
                "question": "2002年世界杯中国队的进球和失球数是多少？",
                "answer": "2002年世界杯，中国队小组赛三战皆负，进了0球，失了9球。分别0-2不敌哥斯达黎加、0-4不敌巴西、0-3不敌土耳其。"
            }
        ]

        # 保存到文件
        self._save_knowledge()

        # 提取文本块
        for item in self.knowledge_data:
            if 'question' in item and 'answer' in item:
                self.chunks.append(f"问题：{item['question']}\n答案：{item['answer']}")

    def _save_knowledge(self):
        """保存知识库到文件"""
        kb_file = self.kb_dir / "worldcup_knowledge.json"
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)
        print(f"知识库已保存到 {kb_file}")

    def _build_index(self):
        """构建FAISS索引"""
        if not self.chunks:
            return

        if not self.client:
            # 无API时使用简单关键词匹配
            return

        try:
            # 生成embeddings
            print("正在生成知识库向量...")
            batch_size = 20
            all_embeddings = []

            for i in range(0, len(self.chunks), batch_size):
                batch = self.chunks[i:i+batch_size]
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

            self.embeddings = np.array(all_embeddings).astype('float32')

            # 构建FAISS索引
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings)

            print(f"FAISS索引已构建，包含 {len(self.chunks)} 条知识")
        except Exception as e:
            print(f"构建索引失败: {e}")

    def _simple_search(self, query: str, top_k: int = 5) -> List[Tuple[int, float, str]]:
        """简单关键词搜索（当FAISS不可用时）"""
        query_lower = query.lower()
        results = []

        for idx, chunk in enumerate(self.chunks):
            chunk_lower = chunk.lower()

            # 计算简单的相似度分数
            score = 0
            query_words = query_lower.split()

            for word in query_words:
                if word in chunk_lower:
                    score += 1
                    # 关键词匹配加分
                    if word in ['世界杯', '世界', '冠军', '规则', '进球', '比分']:
                        score += 2

            if score > 0:
                results.append((idx, score, chunk))

        results.sort(key=lambda x: x[1], reverse=True)
        return [(idx, 1.0/score if score > 0 else 0, chunk) for idx, score, chunk in results[:top_k]]

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """搜索相关知识"""
        if not query:
            return []

        try:
            if self.index is None or self.client is None:
                # 使用简单搜索
                search_results = self._simple_search(query, top_k)
            else:
                # 使用向量搜索
                query_embedding = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=[query]
                )
                query_vector = np.array([query_embedding.data[0].embedding]).astype('float32')

                distances, indices = self.index.search(query_vector, top_k)
                search_results = [
                    (int(indices[0][i]), float(distances[0][i]), self.chunks[int(indices[0][i])])
                    for i in range(len(indices[0]))
                ]

            results = []
            for idx, distance, chunk in search_results:
                # 找到对应的知识条目
                for item in self.knowledge_data:
                    if 'question' in item and 'answer' in item:
                        if f"问题：{item['question']}" in chunk or item['question'] in chunk:
                            results.append({
                                'question': item['question'],
                                'answer': item['answer'],
                                'category': item.get('category', '其他'),
                                'relevance': 1.0 / (1.0 + distance)
                            })
                            break

            return results

        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def _load_extended_content(self):
        """加载扩展内容：球队档案、战术词汇等"""
        # 加载球队档案
        team_file = self.kb_dir / "team_profiles.json"
        if team_file.exists():
            try:
                with open(team_file, 'r', encoding='utf-8') as f:
                    self.team_profiles = json.load(f)
                print(f"已加载 {len(self.team_profiles)} 支球队档案")
            except Exception as e:
                print(f"加载球队档案失败: {e}")

        # 加载战术词汇
        glossary_file = self.kb_dir / "tactical_glossary.json"
        if glossary_file.exists():
            try:
                with open(glossary_file, 'r', encoding='utf-8') as f:
                    self.tactical_glossary = json.load(f)
                print(f"已加载 {len(self.tactical_glossary)} 条战术概念")
            except Exception as e:
                print(f"加载战术词汇失败: {e}")

        # 加载阵型百科
        self._load_json("formation_encyclopedia.json", "_formation_encyclopedia")
        # 加载阵型对位矩阵
        self._load_json("formation_matchup.json", "_formation_matchup")
        # 加载战术风格
        self._load_json("playing_styles.json", "_playing_styles")
        # 加载风格对位
        self._load_json("style_matchup.json", "_style_matchup")
        # 加载位置需求
        self._load_json("position_requirements.json", "_position_requirements")

    def _load_json(self, filename: str, attr: str):
        path = self.kb_dir / filename
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    setattr(self, attr, json.load(f))
                print(f"已加载 {len(getattr(self, attr))} 条数据 ({filename})")
            except Exception as e:
                print(f"加载 {filename} 失败: {e}")

    def get_team_profiles(self) -> List[Dict]:
        """获取所有球队档案"""
        return self.team_profiles

    def get_team_profile(self, team_name: str) -> Optional[Dict]:
        """根据队名获取球队档案"""
        team_lower = team_name.strip().lower()
        for tp in self.team_profiles:
            if tp.get("team", "").lower() == team_lower:
                return tp
        return None

    def get_tactical_glossary(self) -> List[Dict]:
        """获取所有战术词汇"""
        return self.tactical_glossary

    def search_tactical_term(self, term: str) -> Optional[Dict]:
        """搜索战术术语"""
        term_lower = term.strip().lower()
        for entry in self.tactical_glossary:
            if term_lower in entry.get("term", "").lower():
                return entry
        return None

    def search_team(self, query: str) -> List[Dict]:
        """搜索球队档案"""
        query_lower = query.strip().lower()
        results = []
        for tp in self.team_profiles:
            if (query_lower in tp.get("team", "").lower()
                or query_lower in tp.get("confederation", "").lower()
                or query_lower in tp.get("playing_style", "").lower()):
                results.append(tp)
        return results

    # ── 新增：战术数据检索 ────────────────────────────────

    def get_formation_encyclopedia(self) -> List[Dict]:
        return self.formation_encyclopedia

    def get_formation_detail(self, formation_id: str) -> Optional[Dict]:
        for f in self.formation_encyclopedia:
            if f.get("id") == formation_id:
                return f
        return None

    def get_formation_matchup(self, home_form: str, away_form: str) -> Optional[Dict]:
        for m in self.formation_matchup:
            if m.get("home_formation") == home_form and m.get("away_formation") == away_form:
                return m
        return None

    def get_playing_styles(self) -> List[Dict]:
        return self.playing_styles

    def get_playing_style(self, style_id: str) -> Optional[Dict]:
        for s in self.playing_styles:
            if s.get("id") == style_id:
                return s
        return None

    def get_style_matchup(self, style_a: str, style_b: str) -> Optional[Dict]:
        for sm in self.style_matchup:
            if sm.get("style_a") == style_a and sm.get("style_b") == style_b:
                return sm
        return None

    def get_position_requirements(self) -> List[Dict]:
        return self.position_requirements

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for item in self.knowledge_data:
            if 'category' in item:
                categories.add(item['category'])
        return sorted(list(categories))

    def get_knowledge_by_category(self, category: str) -> List[Dict]:
        """按分类获取知识"""
        return [item for item in self.knowledge_data if item.get('category') == category]

    def get_random_knowledge(self, count: int = 5) -> List[Dict]:
        """获取随机知识条目"""
        import random
        if len(self.knowledge_data) <= count:
            return self.knowledge_data
        return random.sample(self.knowledge_data, count)

    def add_knowledge(self, question: str, answer: str, category: str = "其他"):
        """添加新知识"""
        self.knowledge_data.append({
            "category": category,
            "question": question,
            "answer": answer
        })
        self.chunks.append(f"问题：{question}\n答案：{answer}")
        self._save_knowledge()

        # 更新索引
        if self.index is not None and self.client is not None:
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=[question + " " + answer]
                )
                new_embedding = np.array([response.data[0].embedding]).astype('float32')
                self.index.add(new_embedding)
            except Exception as e:
                print(f"更新索引失败: {e}")

    def answer_question(self, question: str) -> str:
        """使用RAG回答问题"""
        # 搜索相关知识
        results = self.search(question, top_k=3)

        if not results:
            return "抱歉，我在知识库中没有找到相关信息。您可以尝试换个问题，或者咨询更具体的世界杯知识。"

        # 构建上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"{i}. {result['question']}\n   {result['answer']}")

        context = "\n\n".join(context_parts)

        if self.client:
            try:
                prompt = f"""基于以下知识库内容，回答用户的问题。如果知识库中的内容不能完全回答问题，请基于已有信息给出合理的回答。

知识库：
{context}

用户问题：{question}

请给出准确、简洁的回答。
"""
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "你是一个专业、友好的世界杯知识问答助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )

                return response.choices[0].message.content

            except Exception as e:
                print(f"生成回答失败: {e}")

        # 备用：直接返回最相关的答案
        return results[0]['answer']


# 全局知识库服务实例
knowledge_service = KnowledgeBaseService()


if __name__ == "__main__":
    service = KnowledgeBaseService()

    # 测试问答
    print("\n=== 知识库测试 ===")
    answer = service.answer_question("世界杯历史最佳射手是谁？")
    print(f"Q: 世界杯历史最佳射手是谁？\nA: {answer}\n")

    print(f"分类列表: {service.get_categories()}")