import yaml
from crewai import Agent, Crew, Task, Process
from typing import Dict, List, Any, Optional
from game_state import Role, GameState, Player, PlayerStatus, Team, ItemManager
from game_task import GameTask
import logging
logger = logging.getLogger(__name__)


# 游戏房间
class GameRoom:
    config: Dict[str, Any] = {}
    game_state: GameState = GameState([])
    werewolf_crew: Crew | None = None # 狼人讨论群组
    discussion_crew: Crew | None = None # 公开讨论群组

    def __init__(self, config_file: str = "config/werewolf_config.yaml"):
        self.config = self._load_config(config_file)


    # 初始化游戏房间
    def init_room(self) -> None:
        """根据配置初始化游戏"""
        player_infos = self.config['game_settings']['player_info']
        
        for player_info in player_infos:
            player = self._create_player(player_info)
            self.game_state.players.append(player)

        self.werewolf_crew = self._create_werewolf_crew()
        self.discussion_crew = self._create_discussion_crew()

    # 狼人群组讨论投票
    def werewolf_vote(self) -> str:
        return self._werewolf_vote()

    # 单个agent执行动作（比如预言家，女巫，守卫）
    def single_agent_action(self, agent: Agent, task: Task) -> str:
        new_crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        result = new_crew.kickoff()
        return result.raw

    # 检查游戏是否结束
    def check_game_end(self) -> bool:
        """检查游戏是否结束"""
        werewolves = self.game_state.alive_werewolves
        good_players = self.game_state.alive_villagers
        
        if not werewolves:
            print("好人阵营胜利！")
            return True
        elif len(good_players) <= len(werewolves):
            print("狼人阵营胜利！")
            return True
        
        return False


    ## ----------- 辅助小函数 -----------
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """从YAML文件加载游戏配置"""
        with open(config_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def _create_player(self, player_info: Dict[str, Any]) -> Player:
        """
        动态创建玩家agent
        
        Args:
            player_info: 玩家信息字典，包含player_id, player_role, llm
        
        Returns:
            Player: 创建的玩家
        """
        player_id = player_info['player_id']
        role = Role(player_info['player_role'])
        llm_model = player_info['llm']
        
        role_config = self.config['roles'][role]
        
        agent = Agent(
            role=f"狼人杀玩家-{player_id}号",
            goal=role_config['goal'],
            backstory=Player.get_player_status_description(player_id, role) + role_config['backstory'],
            llm=llm_model,
            verbose=True,
            memory=True,  # Agent级别的记忆
            allow_delegation=False,
            max_iter=10
        )
        # 添加额外信息
        agent.metadata["player_id"] = player_id
        
        return Player(
            id=player_id,
            agent=agent,
            role=role
        )

    # 创建狼人讨论群组
    def _create_werewolf_crew(self) -> Crew:
        """获取狼人讨论群组"""
        werewolves = self.game_state.alive_werewolves
        if not werewolves:
            logger.warning("没有存活的狼人,游戏应该结束了")
            raise ValueError("没有存活的狼人,游戏应该结束了")

        return Crew(
            agents=[player.agent for player in werewolves],
            tasks=[],
            process=Process.sequential,
            memory=True,  # 启用crew级别的共享记忆
            verbose=True,
            max_rpm=100  # 控制请求频率
        )
    
    # 创建公开讨论群组
    def _create_discussion_crew(self) -> Crew:
        """创建公开讨论crew实例（只创建一次）"""
        return Crew(
            agents=[player.agent for player in self.game_state.alive_players],
            tasks=[],
            process=Process.sequential,
            memory=True,  # 启用crew级别的共享记忆
            verbose=True,
            max_rpm=100  # 控制请求频率
        )

    # 保留crew中存活的agent
    def _update_crew_agent(self, crew: Crew):
        for agent in crew.agents:
            if agent.metadata.get("player_id") not in [player.id for player in self.game_state.alive_players]:
                crew.agents.remove(agent) # 删除死亡的agent
    
    # 狼人投票
    def _werewolf_vote(self) -> str:
        self._update_crew_agent(self.werewolf_crew)
        
        # 更新任务描述，包含当前游戏状态
        current_context = self.game_state.get_game_state_description
        
        # 创建新的任务但使用相同的crew
        vote_task = GameTask.get_werewolf_vote_task(self.game_state)
        
        # 更新crew的任务
        self.werewolf_crew.tasks = [vote_task]
        
        result = self.werewolf_crew.kickoff()
        return result.raw
    
    def day_discussion(self) -> str:
        """白天讨论（使用持久化crew）"""
        if not self.discussion_crew:
            return "没有存活的玩家"
        
        current_context = f"第{self.game_state['day_count']}天白天，存活玩家：{[p.player_id for p in self.get_alive_players()]}"
        
        discussion_task = Task(
            description=f"白天阶段，所有玩家依次发言，分析昨晚的情况，寻找狼人线索。{current_context}",
            expected_output="发言内容和怀疑对象",
            agent=self.discussion_crew.agents[0]
        )
        
        self.discussion_crew.tasks = [discussion_task]
        
        result = self.discussion_crew.kickoff()
        return result.raw