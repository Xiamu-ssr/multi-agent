# 定义了狼人杀中各种task
from game_state import GameState, Player, Role
from crewai import Task

class GameTask:
    
    @staticmethod
    def get_game_state_description(game_state: GameState) -> str:
        return game_state.get_game_state_description
    
    # 狼人投票任务
    @staticmethod
    def get_werewolf_vote_task(game_state: GameState) -> Task:
        return Task(
            description=f"作为狼人，你需要和其他狼人协商决定今晚击杀的目标。{game_state.get_game_state_description}",
            expected_output="选择的击杀目标玩家ID和理由,格式为json:{{'target_id': '玩家ID', 'reason': '理由'}}",
        )

    # 预言家任务
    @staticmethod
    def get_prophet_task(game_state: GameState) -> Task:
        return Task(
            description=f"作为预言家，你需要预言一个玩家的身份。{game_state.get_game_state_description}",
            expected_output="预言的玩家ID和身份,格式为json:{{'target_id': '玩家ID'}",
        )

    # 女巫任务
    @staticmethod
    def get_witch_task(game_state: GameState) -> Task:
        return Task(
            description=f"作为女巫，你需要使用解药或毒药。{game_state.get_game_state_description}, {Player.get_item_description(Role.WITCH)}",
            expected_output="使用的解药或毒药,格式为json:{{'item': '解药'或'毒药', 'target_id': '玩家ID'}}",
        )

    # 守卫任务
    @staticmethod
    def get_guard_task(game_state: GameState) -> Task:
        return Task(
            description=f"作为守卫，你需要守护一个玩家。{game_state.get_game_state_description}",
            expected_output="守护的玩家ID,格式为json:{{'target_id': '玩家ID'}}",
        )