from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew
from crewai.tools import BaseTool
from random import randint
from typing import Type, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
# from deprecated import deprecated

# @deprecated
class DamageInput(BaseModel):
    """输入模式：辩题与发言"""
    topic: str = Field(..., description="辩题")
    speech: str = Field(..., description="辞手发言")

# @deprecated
class DamageCalculator(BaseTool):
    name: str = "damage_calculator"
    description: str = "根据辞手发言判定 5-20 点伤害"
    args_schema: Type[BaseModel] = DamageInput

    def _run(self, topic: str, speech: str) -> str:
        damage = randint(5, 20)
        return f"造成 {damage} 点伤害。评判理由：基于发言内容和辩题相关性的随机模拟评判。"

@CrewBase
class DebateCrew:
    """辩论赛 Crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, max_rounds: int = 5):
        self.max_rounds = max_rounds
        self.current_round = 1
        self.hp_A = 100
        self.hp_B = 100

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'],
            verbose=True
        )

    @agent
    def player_a(self) -> Agent:
        return Agent(
            config=self.agents_config['player_a'],
            verbose=True
        )

    @agent
    def player_b(self) -> Agent:
        return Agent(
            config=self.agents_config['player_b'],
            verbose=True
        )

    @crew
    def crew(self) -> Crew:
        """创建一个简单的 crew，主要用于满足 CrewBase 的要求"""
        # 创建一个简单的任务来满足 CrewBase 的要求
        simple_task = Task(
            description="这是一个占位任务",
            expected_output="占位输出",
            agent=self.judge()
        )
        
        return Crew(
            agents=[self.judge(), self.player_a(), self.player_b()],
            tasks=[simple_task],
            process=Process.sequential,
            verbose=True
        )

    def run_debate(self, topic: str):
        """运行辩论流程"""
        print(f"=== 辩论开始：{topic} ===")
        print(f"正方(A)血量: {self.hp_A}, 反方(B)血量: {self.hp_B}")
        
        while self.current_round <= self.max_rounds and self.hp_A > 0 and self.hp_B > 0:
            print(f"\n--- 第 {self.current_round} 轮 ---")
            
            # 正方发言
            speech_a = self._get_speech(self.player_a(), topic, "正方", self.hp_A, self.hp_B)
            print(f"正方发言: {speech_a}")
            
            # 裁判评判正方发言
            summary_a = self._judge_speech(topic, speech_a)
            self.hp_B -= summary_a.damage
            print(
                f"正方造成 {summary_a.damage} 点伤害，反方剩余血量: {self.hp_B}；评判理由：{summary_a.rationale}"
            )
            
            # 反方发言
            speech_b = self._get_speech(self.player_b(), topic, "反方", self.hp_B, self.hp_A)
            print(f"反方发言: {speech_b}")
            
            # 裁判评判反方发言
            summary_b = self._judge_speech(topic, speech_b)
            self.hp_A -= summary_b.damage
            print(
                f"反方造成 {summary_b.damage} 点伤害，正方剩余血量: {self.hp_A}；评判理由：{summary_b.rationale}"
            )
            
            if self.hp_A <= 0 and self.hp_A < self.hp_B:
                print("反方获胜！")
                break

            if self.hp_B <= 0 and self.hp_B < self.hp_A:
                print("正方获胜！")
                break
            
            self.current_round += 1
        
        return self._determine_winner()

    def _get_speech(self, agent: Agent, topic: str, side: str, own_hp: int, opponent_hp: int) -> str:
        """获取辞手发言"""
        task = Task(
            description=f"作为{side}，针对辩题'{topic}'进行发言。当前血量：{own_hp}，对方血量：{opponent_hp}。请提出有力的论据。",
            expected_output=f"一段有力的{side}辩论发言",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )
        
        result = crew.kickoff()
        return result.raw

    def _judge_speech(self, topic: str, speech: str) -> "DebateCrew.JudgeSummary":
        """裁判评判发言，返回裁判评判摘要"""
        task = Task(
            description=f"评价以下辩论发言，并打出伤害值。辩题：{topic}，发言：{speech}",
            expected_output="伤害评判结果，包含具体的伤害数值和评判理由，伤害值范围为10-30，输出格式为一段json:，比如{'damage': 10, 'rationale': '评判理由'}",
            agent=self.judge()
        )
        
        crew = Crew(
            agents=[self.judge()],
            tasks=[task],
            verbose=False
        )
        
        result = crew.kickoff()
        return self._parse_judge_summary(result.raw)

    def _parse_judge_summary(self, summary_text: str) -> "DebateCrew.JudgeSummary":
        """解析裁判输出，提取伤害值与评判理由"""
        import json, re

        damage: Optional[int] = None
        rationale: str = ""

        # 尝试解析 JSON 片段
        try:
            json_match = re.search(r"\{.*?\}", summary_text, re.S)
            if json_match:
                data = json.loads(json_match.group(0))
                damage = int(data.get("damage", 0)) or None
                rationale = data.get("rationale", "警告，无理由")
        except Exception:
            # 如果 JSON 解析失败则忽略
            pass

        # 兜底：正则提取数字
        if damage is None:
            nums = re.findall(r"\d+", summary_text)
            if nums:
                damage = int(nums[0])

        # 最终兜底随机
        if damage is None:
            damage = randint(10, 30)

        # 伤害范围修正
        damage = max(10, min(damage, 30))

        # 如果理由为空，直接使用裁判原始文本作为理由
        rationale = rationale or summary_text.strip()

        return self.JudgeSummary(damage=damage, rationale=rationale)

    def _determine_winner(self):
        """确定获胜者"""
        if self.current_round > self.max_rounds:
            if self.hp_A > self.hp_B:
                winner = "正方获胜！"
            elif self.hp_B > self.hp_A:
                winner = "反方获胜！"
            else:
                winner = "平局！"
            print(winner)
        
        return {
            "winner": "A" if self.hp_A > self.hp_B else "B" if self.hp_B > self.hp_A else "平局",
            "final_hp_A": self.hp_A,
            "final_hp_B": self.hp_B,
            "rounds": self.current_round - 1
        }

    # ================= 内部数据结构 =================
    @dataclass
    class JudgeSummary:
        """裁判评判摘要"""
        damage: int
        rationale: str