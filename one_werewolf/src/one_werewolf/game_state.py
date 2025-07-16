# 核心类和函数设计
# 1. game_state.py - 游戏状态管理
from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from enum import Enum
import logging
logger = logging.getLogger(__name__)

class PlayerStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"

class GamePhase(Enum):
    NIGHT = "night"
    DAY = "day"
    DISCUSSION = "discussion"
    VOTING = "voting"
    GAME_OVER = "game_over"

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


# 物品
class Item(Enum):
    POISON = "poison"
    ANTIDOTE = "antidote"

# 物品管理器
class ItemManager(BaseModel):
    player_items: Dict[str, Dict[Item, int]] = {} # player_id -> item_name -> item_count

    def __init__(self, player_roles: Dict[str, Role]):
        self.player_items = {}
        for player_id, role in player_roles.items():
            if role == Role.WITCH:
                self.player_items[player_id] = {
                    Item.POISON: 1,
                    Item.ANTIDOTE: 1
                }
            else:
                # 其他角色没有特殊物品
                self.player_items[player_id] = {}
    
    def use_item(self, player_id: str, item: Item):
        if player_id not in self.player_items:
            raise ValueError(f"Player {player_id} does not have any items")
        if item not in self.player_items[player_id]:
            raise ValueError(f"Player {player_id} does not have {item} item")
        if self.player_items[player_id][item] == 0:
            logger.warning(f"Player {player_id} has 0 count of {item} item")
            return False
        self.player_items[player_id][item] -= 1
        return True

# 游戏状态
class GameState(BaseModel):
    # 基础游戏信息
    day_count: int = 1
    current_phase: GamePhase = GamePhase.NIGHT
    game_over: bool = False
    winner: Optional[Team] = None
    
    # 玩家状态
    player_status: Dict[str, PlayerStatus] = {}  # agent_id -> status
    player_roles: Dict[str, Role] = {}           # agent_id -> role
    
    # 当天夜间行动数据
    night_action: NightAction = NightAction()
    night_record: NightRecord = NightRecord()
    
    # 白天投票数据
    day_vote: DayVote = DayVote()
    day_vote_record: DayVoteRecord = DayVoteRecord()
    
    # 物品数据
    item_manager: Optional[ItemManager] = None
    
    def __init__(self, player_roles: Dict[str, Role]):
        self.item_manager = ItemManager(player_roles)
        self.player_status = {player_id: PlayerStatus.ALIVE for player_id in player_roles}
        self.player_roles = player_roles
    
    # 存活玩家列表
    @property
    def alive_players(self) -> List[str]:
        return [player_id for player_id, status in self.player_status.items() 
                if status == PlayerStatus.ALIVE]
    
    @property
    def alive_werewolves(self) -> List[str]:
        return [player_id for player_id in self.alive_players 
                if self.player_roles[player_id] == Role.WEREWOLF]
    
    @property
    def alive_villagers(self) -> List[str]:
        return [player_id for player_id in self.alive_players 
                if self.player_roles[player_id] != Role.WEREWOLF]