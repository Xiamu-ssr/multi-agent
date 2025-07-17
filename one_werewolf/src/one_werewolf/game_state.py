# 核心类和函数设计
# 1. game_state.py - 游戏状态管理
from __future__ import annotations
from crewai import Agent
from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from enum import Enum
import logging
logger = logging.getLogger(__name__)

class GamePhase(Enum):
    NIGHT = {"name": "night", "description": "夜晚"}
    DAY = {"name": "day", "description": "白天"}
    DISCUSSION = {"name": "discussion", "description": "讨论"}
    VOTING = {"name": "voting", "description": "投票"}
    GAME_OVER = {"name": "game_over", "description": "游戏结束"}

class PlayerStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"

# 角色
class Role(Enum):
    WEREWOLF = "werewolf" # 狼人
    PROPHET = "prophet" # 预言家
    WITCH = "witch" # 女巫
    GUARD = "guard" # 守卫
    VILLAGER = "villager" # 村民

# 阵营
class Team(Enum):
    WEREWOLF = "werewolf" # 狼人阵营
    GOOD = "good" # 好人阵营

    @staticmethod
    def get_team(role: Role) -> Team:
        if role == Role.WEREWOLF:
            return Team.WEREWOLF
        else:
            return Team.GOOD

# 物品
class Item(Enum):
    POISON = "poison"
    ANTIDOTE = "antidote"

class Player(BaseModel):
    id: str
    agent: Agent
    status: PlayerStatus
    role: Role
    team: Team
    items: Dict[Item, int] = {}

    def __init__(self, id: str, agent: Agent, role: Role):
        self.id = id
        self.agent = agent
        self.status = PlayerStatus.ALIVE
        self.role = role
        self.team = Team.get_team(role)
        self.items = ItemManager.get_role_items(role)

    def use_item(self, item: Item):
        if item not in self.items:
            logger.warning(f"Player {self.id} does not have {item} item")
            return False
        if self.items[item] == 0:
            logger.warning(f"Player {self.id} has 0 count of {item} item")
            return False
        self.items[item] -= 1
        return True

    @staticmethod
    def get_player_status_description(id: str, role: Role) -> str:
        return f"你的玩家id是{id}，角色是{role}，阵营是{Team.get_team(role)}"

    # 获取物品剩余数量描述
    @staticmethod
    def get_item_description(role: Role) -> str:
        items = ItemManager.get_role_items(role)
        if items:
            item_str = "，".join([f"{item.value}（{count}个）" for item, count in items.items()])
            return f"你拥有以下物品：{item_str}"
        else:
            return "你没有任何物品"

# 当天夜间行动数据
class NightAction(BaseModel):
    werewolf_target: Optional[str] = None # 狼人击杀目标
    witch_poison_target: Optional[str] = None # 女巫毒杀目标
    witch_save_target: Optional[str] = None # 女巫救助目标
    guard_protect_target: Optional[str] = None # 守卫守护目标

    night_result: Optional[str] = None # 夜间行动结果

# 历史夜间行动记录
class NightRecord(BaseModel):
    night_action: Dict[int, NightAction] = {} # day -> night_action 
    
    def add_night_action_record(self, day: int, night_action: NightAction):
        self.night_action[day] = night_action

# 投票数据
class Vote(BaseModel):
    voter_id: str # 投票人
    target_id: str # 投票目标
    reason: str # 投票理由

    # 获取表述
    def get_description(self):
        return f"{self.voter_id} 投票给 {self.target_id}"

# 当天白天投票数据
class DayVote(BaseModel):
    vote: Dict[str, Vote] = {} # voter_id -> vote
    
    def add_vote_record(self, voter_id: str, vote: Vote):
        self.vote[voter_id] = vote

    # 获取表述
    def get_description(self):
        description = ""
        for voter_id, vote in self.vote.items():
            description += f"{voter_id} 投票给 {vote.target_id}\n"
        return description

# 历史投票记录
class DayVoteRecord(BaseModel):
    day_vote: Dict[int, DayVote] = {} # day -> day_vote
    
    def add_day_vote_record(self, day: int, day_vote: DayVote):
        self.day_vote[day] = day_vote

# 物品管理器
class ItemManager():

    @staticmethod
    def get_role_items(role: Role):
        if role == Role.WITCH:
            return {
                Item.POISON: 1,
                Item.ANTIDOTE: 1
            }
        else:
            return {}

# 游戏状态
class GameState(BaseModel):
    # 基础游戏信息
    day_count: int = 1
    current_phase: GamePhase = GamePhase.NIGHT
    game_over: bool = False
    winner: Optional[Team] = None
    
    # 玩家
    players: List[Player] = []
    
    # 当天夜间行动数据
    night_action: NightAction = NightAction()
    night_record: NightRecord = NightRecord()
    
    # 白天投票数据
    day_vote: DayVote = DayVote()
    day_vote_record: DayVoteRecord = DayVoteRecord()
    
    def __init__(self, players: List[Player]):
        self.players = players
    
    # 存活玩家列表
    @property
    def alive_players(self) -> List[Player]:
        return [player for player in self.players if player.status == PlayerStatus.ALIVE]
    
    @property
    def alive_werewolves(self) -> List[Player]:
        return [player for player in self.alive_players 
                if player.role == Role.WEREWOLF]
    
    @property
    def alive_villagers(self) -> List[Player]:
        return [player for player in self.alive_players 
                if player.role != Role.WEREWOLF]

    # 获取当前游戏状态描述
    @property
    def get_game_state_description(self) -> str:
        return f"""
            第{self.day_count}天{self.current_phase == GamePhase.NIGHT and "夜晚" or "白天"}
            当前游戏状态：{self.current_phase.value["description"]}
            存活玩家：{[player.agent.role for player in self.alive_players]}
        """