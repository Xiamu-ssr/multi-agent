# 核心类和函数设计
# 1. game_state.py - 游戏状态管理
from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from enum import Enum

class PlayerStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"

class GamePhase(Enum):
    NIGHT = "night"
    DAY = "day"
    DISCUSSION = "discussion"
    VOTING = "voting"
    GAME_OVER = "game_over"

class Role(Enum):
    WEREWOLF = "werewolf"
    PROPHET = "prophet"
    WITCH = "witch"
    GUARD = "guard"
    VILLAGER = "villager"

class GameState(BaseModel):
    # 基础游戏信息
    day_count: int = 1
    current_phase: GamePhase = GamePhase.NIGHT
    game_over: bool = False
    winner: Optional[str] = None
    
    # 玩家状态
    player_status: Dict[str, PlayerStatus] = {}  # agent_id -> status
    player_roles: Dict[str, Role] = {}           # agent_id -> role
    
    # 夜间行动数据
    werewolf_target: Optional[str] = None        # 狼人击杀目标
    witch_poison_target: Optional[str] = None    # 女巫毒杀目标
    witch_save_target: Optional[str] = None      # 女巫救助目标
    guard_protect_target: Optional[str] = None   # 守卫守护目标
    
    # 白天投票数据
    votes: Dict[str, str] = {}                   # voter_id -> target_id
    eliminated_player: Optional[str] = None      # 被投票淘汰的玩家
    
    # 私有数据
    prophet_checked_players: Dict[str, Role] = {}  # 预言家已验证的玩家
    witch_potions: Dict[str, int] = {             # 女巫药水数量
        "antidote": 1,
        "poison": 1
    }
    
    # 历史记录
    night_results: List[Dict] = []               # 每夜结果记录
    discussion_history: List[Dict] = []          # 讨论历史
    voting_history: List[Dict] = []              # 投票历史
    
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