import yaml
from crewai import Agent, Crew, Task
from typing import Dict, List, Any, Optional
from game_state import Role, GameState

class WerewolfGameManager:
    def __init__(self, config_file: str = "config/werewolf_config.yaml"):
        """
        初始化狼人杀游戏管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self.load_config(config_file)
        self.players: List[Agent] = []
        self.game_state = {
            "alive_players": [],
            "dead_players": [],
            "day_count": 0,
            "phase": "night"
        }
        
        # 持久化的crew实例，保持memory连续性
        self.werewolf_crew: Optional[Crew] = None
        self.discussion_crew: Optional[Crew] = None
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """从YAML文件加载游戏配置"""
        with open(config_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def create_player_agent(self, player_info: Dict[str, Any]) -> Agent:
        """
        动态创建玩家agent
        
        Args:
            player_info: 玩家信息字典，包含player_id, player_role, llm
        
        Returns:
            Agent: 创建的玩家agent
        """
        player_id = player_info['player_id']
        role = player_info['player_role']
        llm_model = player_info['llm']
        
        role_config = self.config['roles'][role]
        
        agent = Agent(
            role=f"{role}_{player_id}",
            goal=role_config['goal'],
            backstory=role_config['backstory'],
            llm=llm_model,
            verbose=True,
            memory=True,  # Agent级别的记忆
            allow_delegation=False,
            max_iter=10
        )
        
        # 为agent添加自定义属性
        agent.player_id = player_id
        agent.role_type = role
        agent.is_alive = True
        agent.items = role_config.get('items', []).copy()  # 复制一份，避免共享引用
        
        return agent
    
    def initialize_game(self) -> None:
        """根据配置初始化游戏"""
        player_infos = self.config['game_settings']['player_info']
        
        for player_info in player_infos:
            player_agent = self.create_player_agent(player_info)
            self.players.append(player_agent)
            self.game_state["alive_players"].append(player_agent)
        
        # 初始化持久化的crew
        self._initialize_persistent_crews()
    
    def _initialize_persistent_crews(self):
        """初始化持久化的crew实例"""
        # 初始化狼人crew
        werewolves = self.get_alive_players_by_role(Role.WEREWOLF.value)
        if werewolves:
            self.werewolf_crew = self._create_werewolf_crew_instance(werewolves)
        
        # 初始化讨论crew
        alive_players = self.get_alive_players()
        if alive_players:
            self.discussion_crew = self._create_discussion_crew_instance(alive_players)
    
    def _create_werewolf_crew_instance(self, werewolves: List[Agent]) -> Crew:
        """创建狼人crew实例（只创建一次）"""
        vote_task = Task(
            description="作为狼人，你需要和其他狼人协商决定今晚击杀的目标。讨论并投票选择一个目标。",
            expected_output="选择的击杀目标玩家ID",
            agent=werewolves[0]
        )
        
        return Crew(
            agents=werewolves,
            tasks=[vote_task],
            memory=True,  # Crew级别的记忆现在有用了
            verbose=True
        )
    
    def _create_discussion_crew_instance(self, alive_players: List[Agent]) -> Crew:
        """创建讨论crew实例（只创建一次）"""
        discussion_task = Task(
            description="白天阶段，所有玩家依次发言，分析昨晚的情况，寻找狼人线索。",
            expected_output="发言内容和怀疑对象",
            agent=alive_players[0]
        )
        
        return Crew(
            agents=alive_players,
            tasks=[discussion_task],
            memory=True,
            verbose=True
        )
    
    def update_crews_after_death(self, dead_player: Agent):
        """玩家死亡后更新crew成员"""
        # 从crew中移除死亡玩家
        if self.werewolf_crew and dead_player.role_type == Role.WEREWOLF.value:
            # 重新创建狼人crew（如果还有狼人存活）
            remaining_werewolves = self.get_alive_players_by_role(Role.WEREWOLF.value)
            if remaining_werewolves:
                self.werewolf_crew = self._create_werewolf_crew_instance(remaining_werewolves)
            else:
                self.werewolf_crew = None
        
        # 重新创建讨论crew
        alive_players = self.get_alive_players()
        if alive_players:
            self.discussion_crew = self._create_discussion_crew_instance(alive_players)
        else:
            self.discussion_crew = None
    
    def get_alive_players_by_role(self, role: str) -> List[Agent]:
        """获取指定角色的存活玩家"""
        return [player for player in self.game_state["alive_players"] 
                if player.role_type == role]
    
    def get_alive_players(self) -> List[Agent]:
        """获取所有存活玩家"""
        return self.game_state["alive_players"]
    
    def werewolf_vote(self) -> str:
        """狼人投票（使用持久化crew）"""
        if not self.werewolf_crew:
            return "没有存活的狼人"
        
        # 更新任务描述，包含当前游戏状态
        current_context = f"第{self.game_state['day_count']}天夜晚，存活玩家：{[p.player_id for p in self.get_alive_players()]}"
        
        # 创建新的任务但使用相同的crew
        vote_task = Task(
            description=f"作为狼人，你需要和其他狼人协商决定今晚击杀的目标。{current_context}",
            expected_output="选择的击杀目标玩家ID和理由",
            agent=self.werewolf_crew.agents[0]
        )
        
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
    
    def single_agent_action(self, agent: Agent, action_type: str, context: str = "") -> str:
        """单个agent执行动作"""
        current_context = f"第{self.game_state['day_count']}天，{context}"
        
        task = Task(
            description=f"{action_type}: {current_context}",
            expected_output="你的决定和理由",
            agent=agent
        )
        
        temp_crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        result = temp_crew.kickoff()
        return result.raw
    
    def night_phase(self):
        """夜晚阶段执行"""
        print(f"=== 第{self.game_state['day_count']}天夜晚 ===")
        
        # 1. 狼人投票
        werewolf_result = self.werewolf_vote()
        print(f"狼人投票结果: {werewolf_result}")
        
        # 2. 预言家查验
        prophets = self.get_alive_players_by_role(Role.PROPHET.value)
        if prophets:
            prophet_result = self.single_agent_action(
                prophets[0], 
                "预言家查验", 
                "选择一个玩家查验其身份"
            )
            print(f"预言家查验: {prophet_result}")
        
        # 3. 女巫行动
        witches = self.get_alive_players_by_role(Role.WITCH.value)
        if witches:
            witch_result = self.single_agent_action(
                witches[0], 
                "女巫行动", 
                "决定是否使用解药或毒药"
            )
            print(f"女巫行动: {witch_result}")
        
        # 4. 守卫守护
        guards = self.get_alive_players_by_role(Role.GUARD.value)
        if guards:
            guard_result = self.single_agent_action(
                guards[0], 
                "守卫守护", 
                "选择一个玩家进行守护"
            )
            print(f"守卫守护: {guard_result}")
    
    def day_phase(self):
        """白天阶段执行"""
        print(f"=== 第{self.game_state['day_count']}天白天 ===")
        
        # 1. 宣布夜晚结果
        self.announce_night_results()
        
        # 2. 讨论阶段
        discussion_result = self.day_discussion()
        print(f"讨论结果: {discussion_result}")
        
        # 3. 投票阶段
        self.voting_phase()
    
    def voting_phase(self):
        """投票阶段"""
        print("=== 投票阶段 ===")
        
        alive_players = self.get_alive_players()
        votes = {}
        
        for player in alive_players:
            vote_result = self.single_agent_action(
                player,
                "投票",
                "根据讨论内容，投票选择你认为是狼人的玩家"
            )
            print(f"玩家{player.player_id}投票: {vote_result}")
    
    def announce_night_results(self):
        """宣布夜晚结果"""
        # 根据夜晚各角色的行动结果，更新游戏状态
        pass
    
    def check_game_end(self) -> bool:
        """检查游戏是否结束"""
        werewolves = self.get_alive_players_by_role(Role.WEREWOLF.value)
        good_players = [p for p in self.get_alive_players() if p.role_type != Role.WEREWOLF.value]
        
        if not werewolves:
            print("好人阵营胜利！")
            return True
        elif len(good_players) <= len(werewolves):
            print("狼人阵营胜利！")
            return True
        
        return False
    
    def run_game(self):
        """运行游戏主循环"""
        while not self.check_game_end():
            self.game_state["day_count"] += 1
            self.night_phase()
            if self.check_game_end():
                break
            self.day_phase()