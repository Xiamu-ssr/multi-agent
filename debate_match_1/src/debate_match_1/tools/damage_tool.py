from crewai.tools import BaseTool
from random import randint
from typing import Type
from pydantic import BaseModel, Field

# @deprecated
class DamageInput(BaseModel):
    """输入模式：辩题与发言"""
    topic: str = Field(..., description="辩题")
    speech: str = Field(..., description="辞手发言")

class DamageCalculator(BaseTool):
    name: str = "damage_calculator"
    description: str = "根据辩手发言判定 5-20 点伤害"
    args_schema: Type[BaseModel] = DamageInput

    def _run(self, topic: str, speech: str) -> str:
        damage = randint(5, 20)
        return f"造成 {damage} 点伤害。评判理由：基于发言内容和辩题相关性的随机模拟评判。"