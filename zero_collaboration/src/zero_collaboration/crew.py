# src/crew.py
from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class ZeroCollaboration:
    """协作撰写《AI 医疗保健的未来》文章的团队"""

    # 指定 YAML 路径（相对于项目根目录）
    agents_config_path = "config/agents.yaml"
    tasks_config_path  = "config/tasks.yaml"

    # ----------------- Agents -----------------
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],      # type: ignore[index]
            verbose=True
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config['editor'],      # type: ignore[index]
            verbose=True
        )

    # ----------------- Task -----------------
    @task
    def article_task(self) -> Task:
        return Task(
            config=self.tasks_config['article_task']  # type: ignore[index]
        )

    # ----------------- Crew -----------------
    @crew
    def crew(self) -> Crew:
        """组装团队与任务流程"""
        return Crew(
            agents=[
                self.researcher(),
                self.writer(),
                self.editor(),
            ],
            tasks=[
                self.article_task(),
            ],
            process=Process.sequential,   # 顺序执行；若需角色自分配可改为 Process.hierarchical
            verbose=True,
        )
