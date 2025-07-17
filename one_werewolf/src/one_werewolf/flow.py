from crewai.flow import Flow, start, listen, router
from crewai import Crew, Process
from typing import Dict, Any, List, Optional
import random
from game_state import GameState, Role, PlayerStatus, GamePhase, Item, NightAction, Team
import logging
from game_room import GameRoom

logger = logging.getLogger(__name__)


class WerewolfGameFlow(Flow[GameState]):
    game_room: GameRoom
    
    @start()
    def initialize_game(self) -> Dict[str, Any]:
        self.game_room = GameRoom()
        self.game_room.init_room()
        
        # 打印初始化信息
        print("=== 狼人杀游戏开始 ===")
        print(f"玩家身份分配: {[player.agent.role for player in self.game_room.game_state.players]}")
        print(f"第{self.game_room.game_state.day_count}夜开始")
    
    @listen(initialize_game)
    def werewolf_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-狼人投票杀人逻辑
        """
        # 游戏还未结束
        if self.game_room.check_game_end():
            return {"phase": "game_over"}
        
        # 狼人投票
        result = self.game_room.werewolf_vote()
        
        # 解析结果并更新状态
        target = self._extract_target_from_result(result)
        self.game_room.game_state.night_action.werewolf_target = target
        print(f"狼人选择击杀: {self.game_room.game_state.night_action.werewolf_target}")
        
        return {"phase": "prophet_night_action"}
    
    @listen(werewolf_night_action)
    def prophet_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-预言家流程
        """
        # TODO: 导入模块创建
        # from tasks.night_tasks import create_prophet_check_task
        # from agents.prophet_agent import create_prophet_agent
        
        # 找到预言家
        prophet_id = self._find_player_by_role(Role.PROPHET)
        if not prophet_id or self.state.player_status[prophet_id] == PlayerStatus.DEAD:
            return {"phase": "witch_night_action"}
        
        # TODO: 创建预言家Crew实现
        # prophet_agent = create_prophet_agent(prophet_id)
        # prophet_task = create_prophet_check_task(
        #     self.state.alive_players, 
        #     {}  # 已查验的玩家信息可以从state中获取
        # )
        #
        # prophet_crew = Crew(
        #     agents=[prophet_agent],
        #     tasks=[prophet_task],
        #     process=Process.sequential,
        #     memory=True,
        #     verbose=True
        # )
        #
        # result = prophet_crew.kickoff()
        
        # 模拟结果
        result = {"target": "agent_1", "role": "villager"}
        
        # 更新预言家已验证信息
        target, role_str = self._extract_prophet_result(result)
        if target:
            # 这里需要保存预言家查验结果
            # 可以在night_action中添加一个属性来保存
            print(f"预言家验证 {target}: {role_str}")
        
        return {"phase": "witch_night_action"}
    
    @listen(prophet_night_action)
    def witch_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-女巫流程
        """
        # TODO: 导入模块创建
        # from tasks.night_tasks import create_witch_action_task
        # from agents.witch_agent import create_witch_agent
        
        # 找到女巫
        witch_id = self._find_player_by_role(Role.WITCH)
        if not witch_id or self.state.player_status[witch_id] == PlayerStatus.DEAD:
            return {"phase": "guard_night_action"}
        
        # 获取女巫物品信息
        witch_items = {}
        if witch_id in self.state.item_manager.player_items:
            witch_items = self.state.item_manager.player_items[witch_id]
        
        # TODO: 创建女巫Crew实现
        # witch_agent = create_witch_agent(witch_id)
        # witch_task = create_witch_action_task(
        #     self.state.night_action.werewolf_target,
        #     witch_items,
        #     self.state.alive_players
        # )
        #
        # witch_crew = Crew(
        #     agents=[witch_agent],
        #     tasks=[witch_task],
        #     process=Process.sequential,
        #     memory=True,
        #     verbose=True
        # )
        #
        # result = witch_crew.kickoff()
        
        # 模拟结果
        result = {"save_target": self.state.night_action.werewolf_target, "poison_target": None}
        
        # 更新女巫行动结果
        action_result = self._extract_witch_result(result)
        if action_result.get("save_target"):
            self.state.night_action.witch_save_target = action_result["save_target"]
            # 使用解药
            if witch_id in self.state.item_manager.player_items:
                self.state.item_manager.use_item(witch_id, Item.ANTIDOTE)
                
        if action_result.get("poison_target"):
            self.state.night_action.witch_poison_target = action_result["poison_target"]
            # 使用毒药
            if witch_id in self.state.item_manager.player_items:
                self.state.item_manager.use_item(witch_id, Item.POISON)
        
        print(f"女巫行动: 救助={self.state.night_action.witch_save_target}, 毒杀={self.state.night_action.witch_poison_target}")
        
        return {"phase": "guard_night_action"}
    
    @listen(witch_night_action)
    def guard_night_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚-守卫流程
        """
        # TODO: 导入模块创建
        # from tasks.night_tasks import create_guard_protect_task
        # from agents.guard_agent import create_guard_agent
        
        # 找到守卫
        guard_id = self._find_player_by_role(Role.GUARD)
        if not guard_id or self.state.player_status[guard_id] == PlayerStatus.DEAD:
            return {"phase": "day_announcement"}
        
        # TODO: 创建守卫Crew实现
        # guard_agent = create_guard_agent(guard_id)
        # guard_task = create_guard_protect_task(self.state.alive_players)
        #
        # guard_crew = Crew(
        #     agents=[guard_agent],
        #     tasks=[guard_task],
        #     process=Process.sequential,
        #     memory=True,
        #     verbose=True
        # )
        #
        # result = guard_crew.kickoff()
        
        # 模拟结果
        result = {"target": "agent_2"}
        
        # 更新守卫守护目标
        self.state.night_action.guard_protect_target = self._extract_target_from_result(result)
        print(f"守卫守护: {self.state.night_action.guard_protect_target}")
        
        return {"phase": "day_announcement"}
    
    @listen(guard_night_action)
    def day_announcement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        白天-夜晚结果公布
        """
        # TODO: 导入模块创建
        # from utils.game_logic import process_night_results
        # from agents.game_master_agent import create_game_master_agent
        
        # 处理夜间结果
        night_result = self._process_night_results(
            werewolf_target=self.state.night_action.werewolf_target,
            witch_save_target=self.state.night_action.witch_save_target,
            witch_poison_target=self.state.night_action.witch_poison_target,
            guard_protect_target=self.state.night_action.guard_protect_target
        )
        
        # 更新玩家状态
        for dead_player in night_result["dead_players"]:
            self.state.player_status[dead_player] = PlayerStatus.DEAD
        
        # 记录夜间行动
        self.state.night_record.add_night_action_record(
            self.state.day_count,
            self.state.night_action
        )
        
        # 准备下一天的夜间行动记录
        self.state.night_action = NightAction()
        self.state.day_count += 1
        
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
        # TODO: 导入模块创建
        # from tasks.day_tasks import create_discussion_tasks
        # from agents.base_agent import create_agents_by_ids
        
        # 获取存活玩家
        alive_players = self.state.alive_players
        if len(alive_players) <= 2:
            return {"phase": "game_over"}
        
        # TODO: 创建讨论Crew - 所有存活玩家参与
        # discussion_agents = create_agents_by_ids(alive_players, self.state.player_roles)
        # discussion_tasks = create_discussion_tasks(alive_players, self.state)
        #
        # discussion_crew = Crew(
        #     agents=discussion_agents,
        #     tasks=discussion_tasks,
        #     process=Process.sequential,
        #     memory=True,
        #     verbose=True
        # )
        #
        # result = discussion_crew.kickoff()
        
        # 模拟结果
        print("讨论阶段完成")
        
        return {"phase": "voting_phase"}
    
    @listen(discussion_phase)
    def voting_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        白天-投票阶段
        """
        # TODO: 实现投票逻辑
        # 模拟每个玩家投票
        for player_id in self.state.alive_players:
            # 随机选择一个投票目标(除自己外)
            possible_targets = [p for p in self.state.alive_players if p != player_id]
            if not possible_targets:
                continue
                
            target = random.choice(possible_targets)
            # 创建投票并添加到day_vote中
            from game_state import Vote
            vote = Vote(voter_id=player_id, target_id=target, reason="模拟投票")
            self.state.day_vote.add_vote_record(player_id, vote)
        
        # 统计投票结果
        vote_count = {}
        for _, vote in self.state.day_vote.vote.items():
            if vote.target_id not in vote_count:
                vote_count[vote.target_id] = 0
            vote_count[vote.target_id] += 1
        
        # 找出票数最多的玩家
        max_votes = 0
        voted_out = None
        for player, count in vote_count.items():
            if count > max_votes:
                max_votes = count
                voted_out = player
        
        # 如果有人被投出
        if voted_out:
            self.state.player_status[voted_out] = PlayerStatus.DEAD
            print(f"投票结果: {voted_out} 被投票出局")
        else:
            print("投票结果: 平局，无人出局")
        
        # 记录投票
        self.state.day_vote_record.add_day_vote_record(
            self.state.day_count,
            self.state.day_vote
        )
        
        # 重置当天投票
        self.state.day_vote = self.state.day_vote.__class__()
        
        # 检查游戏是否结束
        if self._check_game_end():
            return {"phase": "game_over"}
        
        return {"phase": "night_phase"}
    
    @listen(voting_phase)
    def night_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        进入夜晚阶段
        """
        print(f"\n=== 第{self.state.day_count}夜 ===")
        self.state.current_phase = GamePhase.NIGHT
        
        return {"phase": "werewolf_night_action"}
    
    @listen(night_phase, discussion_phase, voting_phase)
    def game_over(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        游戏结束
        """
        print("\n=== 游戏结束 ===")
        if self.state.winner == Team.WEREWOLF:
            print("狼人阵营获胜!")
        else:
            print("好人阵营获胜!")
        
        return {"phase": "end"}
    
    # 辅助方法
    def _find_player_by_role(self, role: Role) -> Optional[str]:
        """查找指定角色的玩家ID"""
        for player_id, player_role in self.state.player_roles.items():
            if player_role == role:
                return player_id
        return None
    
    def _extract_target_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """从结果中提取目标玩家"""
        return result.get("target")
    
    def _extract_prophet_result(self, result: Dict[str, Any]) -> tuple:
        """从结果中提取预言家查验结果"""
        target = result.get("target")
        role = result.get("role")
        return target, role
    
    def _extract_witch_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """从结果中提取女巫行动结果"""
        return {
            "save_target": result.get("save_target"),
            "poison_target": result.get("poison_target")
        }
    
    def _process_night_results(self, werewolf_target: Optional[str], 
                               witch_save_target: Optional[str],
                               witch_poison_target: Optional[str],
                               guard_protect_target: Optional[str]) -> Dict[str, Any]:
        """处理夜间行动结果"""
        dead_players = []
        protection_successful = False
        
        # 处理狼人击杀
        if werewolf_target:
            # 如果被女巫救或被守卫守护，则不会死亡
            if werewolf_target == witch_save_target or werewolf_target == guard_protect_target:
                protection_successful = True
            else:
                dead_players.append(werewolf_target)
        
        # 处理女巫毒杀
        if witch_poison_target and witch_poison_target not in dead_players:
            dead_players.append(witch_poison_target)
        
        return {
            "dead_players": dead_players,
            "protection_successful": protection_successful
        }
    
    def _check_game_end(self) -> bool:
        """检查游戏是否结束"""
        # 计算存活的狼人和好人数量
        alive_werewolves = len(self.state.alive_werewolves)
        alive_villagers = len(self.state.alive_villagers)
        
        # 判断游戏是否结束
        if alive_werewolves == 0:
            self.state.game_over = True
            self.state.winner = Team.GOOD
            return True
        elif alive_werewolves >= alive_villagers:
            self.state.game_over = True
            self.state.winner = Team.WEREWOLF
            return True
        
        return False