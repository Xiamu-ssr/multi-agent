from crewai.flow import Flow, start, listen, router
from typing import Dict, Any
import random

class WerewolfGameFlow(Flow[GameState]):
    
    @start()
    def initialize_game(self) -> Dict[str, Any]:
        """
        游戏初始化 - 不调用agent，直接设置全局变量
        """
        # 初始化玩家身份
        roles = [Role.WEREWOLF] * 3 + [Role.PROPHET, Role.WITCH, Role.GUARD] + [Role.VILLAGER] * 3
        agent_ids = [f"agent_{i}" for i in range(10)]
        random.shuffle(roles)
        
        # 设置游戏状态
        self.state.player_roles = dict(zip(agent_ids, roles))
        self.state.player_status = {agent_id: PlayerStatus.ALIVE for agent_id in agent_ids}
        self.state.current_phase = GamePhase.NIGHT
        self.state.day_count = 1
        
        # 打印初始化信息
        print("=== 狼人杀游戏开始 ===")
        print(f"玩家身份分配: {self.state.player_roles}")
        print(f"第{self.state.day_count}夜开始")
        
        return {"phase": "werewolf_night_action"}
    
    @listen(initialize_game)
    def werewolf_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-狼人投票杀人逻辑
        """
        from tasks.night_tasks import create_werewolf_kill_task
        from agents.werewolf_agent import create_werewolf_agents
        
        # 获取存活的狼人
        alive_werewolves = self.state.alive_werewolves
        if not alive_werewolves:
            return {"phase": "prophet_night_action"}
        
        # 创建狼人Crew
        werewolf_agents = create_werewolf_agents(alive_werewolves, allow_delegation=True)
        werewolf_task = create_werewolf_kill_task(self.state.alive_players, alive_werewolves)
        
        werewolf_crew = Crew(
            agents=werewolf_agents,
            tasks=[werewolf_task],
            process=Process.hierarchical,
            manager_agent=werewolf_agents[0],  # 第一个狼人作为管理者
            memory=True,
            verbose=True
        )
        
        result = werewolf_crew.kickoff()
        
        # 解析结果并更新状态
        self.state.werewolf_target = self._extract_target_from_result(result)
        print(f"狼人选择击杀: {self.state.werewolf_target}")
        
        return {"phase": "prophet_night_action"}
    
    @listen(werewolf_night_action)
    def prophet_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-预言家流程
        """
        from tasks.night_tasks import create_prophet_check_task
        from agents.prophet_agent import create_prophet_agent
        
        # 找到预言家
        prophet_id = self._find_player_by_role(Role.PROPHET)
        if not prophet_id or self.state.player_status[prophet_id] == PlayerStatus.DEAD:
            return {"phase": "witch_night_action"}
        
        # 创建预言家Crew
        prophet_agent = create_prophet_agent(prophet_id)
        prophet_task = create_prophet_check_task(
            self.state.alive_players, 
            self.state.prophet_checked_players
        )
        
        prophet_crew = Crew(
            agents=[prophet_agent],
            tasks=[prophet_task],
            process=Process.sequential,
            memory=True,
            verbose=True
        )
        
        result = prophet_crew.kickoff()
        
        # 更新预言家已验证信息
        target, role = self._extract_prophet_result(result)
        if target:
            self.state.prophet_checked_players[target] = role
            print(f"预言家验证 {target}: {role.value}")
        
        return {"phase": "witch_night_action"}
    
    @listen(prophet_night_action)
    def witch_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-女巫流程
        """
        from tasks.night_tasks import create_witch_action_task
        from agents.witch_agent import create_witch_agent
        
        # 找到女巫
        witch_id = self._find_player_by_role(Role.WITCH)
        if not witch_id or self.state.player_status[witch_id] == PlayerStatus.DEAD:
            return {"phase": "guard_night_action"}
        
        # 创建女巫Crew
        witch_agent = create_witch_agent(witch_id)
        witch_task = create_witch_action_task(
            self.state.werewolf_target,
            self.state.witch_potions,
            self.state.alive_players
        )
        
        witch_crew = Crew(
            agents=[witch_agent],
            tasks=[witch_task],
            process=Process.sequential,
            memory=True,
            verbose=True
        )
        
        result = witch_crew.kickoff()
        
        # 更新女巫行动结果
        action_result = self._extract_witch_result(result)
        if action_result.get("save_target"):
            self.state.witch_save_target = action_result["save_target"]
            self.state.witch_potions["antidote"] = 0
        if action_result.get("poison_target"):
            self.state.witch_poison_target = action_result["poison_target"]
            self.state.witch_potions["poison"] = 0
        
        print(f"女巫行动: 救助={self.state.witch_save_target}, 毒杀={self.state.witch_poison_target}")
        
        return {"phase": "guard_night_action"}
    
    @listen(witch_night_action)
    def guard_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-守卫流程
        """
        from tasks.night_tasks import create_guard_protect_task
        from agents.guard_agent import create_guard_agent
        
        # 找到守卫
        guard_id = self._find_player_by_role(Role.GUARD)
        if not guard_id or self.state.player_status[guard_id] == PlayerStatus.DEAD:
            return {"phase": "day_announcement"}
        
        # 创建守卫Crew
        guard_agent = create_guard_agent(guard_id)
        guard_task = create_guard_protect_task(self.state.alive_players)
        
        guard_crew = Crew(
            agents=[guard_agent],
            tasks=[guard_task],
            process=Process.sequential,
            memory=True,
            verbose=True
        )
        
        result = guard_crew.kickoff()
        
        # 更新守卫守护目标
        self.state.guard_protect_target = self._extract_target_from_result(result)
        print(f"守卫守护: {self.state.guard_protect_target}")
        
        return {"phase": "day_announcement"}
    
    @listen(guard_night_action)
    def day_announcement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        白天-夜晚结果公布
        """
        from utils.game_logic import process_night_results
        from agents.game_master_agent import create_game_master_agent
        
        # 处理夜间结果
        night_result = process_night_results(
            werewolf_target=self.state.werewolf_target,
            witch_save_target=self.state.witch_save_target,
            witch_poison_target=self.state.witch_poison_target,
            guard_protect_target=self.state.guard_protect_target
        )
        
        # 更新玩家状态
        for dead_player in night_result["dead_players"]:
            self.state.player_status[dead_player] = PlayerStatus.DEAD
        
        # 记录夜间结果
        self.state.night_results.append({
            "day": self.state.day_count,
            "dead_players": night_result["dead_players"],
            "protection_successful": night_result["protection_successful"]
        })
        
        # 打印结果
        print(f"\n=== 第{self.state.day_count}天白天 ===")
        if night_result["dead_players"]:
            print(f"昨夜死亡: {night_result['dead_players']}")
        else:
            print("昨夜平安夜")
        
        # 检查游戏是否结束
        if self._check_game_end():
            return {"phase": "game_over"}
        
        return {"phase": "discussion"}
    
    @listen(day_announcement)
    def discussion_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        白天-发言讨论阶段
        """
        from tasks.day_tasks import create_discussion_tasks
        from agents.base_agent import create_agents_by_ids
        
        # 获取存活玩家
        alive_players = self.state.alive_players
        if len(alive_players) <= 2:
            return {"phase": "game_over"}
        
        # 创建讨论Crew - 所有存活玩家参与
        discussion_agents = create_agents_by_ids(alive_players, self.state.player_roles)
        discussion_tasks = create_discussion_tasks(alive_players, self.state)
        
        discussion_crew = Crew