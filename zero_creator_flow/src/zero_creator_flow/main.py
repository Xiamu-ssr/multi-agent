#!/usr/bin/env python
import json
import os
from typing import List, Dict
from pydantic import BaseModel, Field
from crewai import LLM
from crewai.flow.flow import Flow, listen, start
from zero_creator_flow.crews.content_crew.content_crew import ContentCrew

# 定义结构化数据模型
class Section(BaseModel):
    title: str = Field(description="章节标题")
    description: str = Field(description="本节应涵盖内容的简要描述")

class GuideOutline(BaseModel):
    title: str = Field(description="指南标题")
    introduction: str = Field(description="主题介绍")
    target_audience: str = Field(description="目标读者描述")
    sections: List[Section] = Field(description="指南各章节列表")
    conclusion: str = Field(description="结论或总结")

    @classmethod
    def get_template_json(cls) -> str:
        """返回一个最小合法的 GuideOutline JSON 字符串（占位内容）"""
        template = GuideOutline(
            title="示例标题",
            introduction="示例介绍",
            target_audience="示例读者",
            sections=[Section(title="第一章：xxxx", description="xxxx")],
            conclusion="示例结论"
        )
        # v2 用 model_dump_json；设置 ensure_ascii=False 保留中文
        return template.model_dump_json(indent=2)

# 定义流程状态
class GuideCreatorState(BaseModel):
    topic: str = ""
    audience_level: str = ""
    guide_outline: GuideOutline = None
    sections_content: Dict[str, str] = {}

class GuideCreatorFlow(Flow[GuideCreatorState]):
    """创建综合指南的流程"""

    @start()
    def get_user_input(self):
        """获取用户输入：主题和读者层级"""
        print("\n=== 创建你的综合指南 ===\n")

        # 获取指南主题
        self.state.topic = input("请输入你想创建指南的主题：")

        # 获取目标读者层级并验证
        while True:
            audience = input("目标读者层级？（beginner/intermediate/advanced）").lower()
            if audience in ["beginner", "intermediate", "advanced"]:
                self.state.audience_level = audience
                break
            print("请输入 'beginner'、'intermediate' 或 'advanced'")

        print(f"\n正在为主题 '{self.state.topic}'，面向 '{self.state.audience_level}' 读者创建指南...\n")
        return self.state

    @listen(get_user_input)
    def create_guide_outline(self, state):
        """使用 LLM 生成结构化的指南大纲"""
        print("正在生成指南大纲...")

        # 初始化 LLM
        # llm = LLM(model="deepseek/deepseek-reasoner", response_format=GuideOutline)
        llm = LLM(model="deepseek/deepseek-reasoner")

        # 构建消息列表
        template_json = GuideOutline.get_template_json()
        messages = [
            {"role": "system", "content": f"""
            你是一个专门输出 JSON 的助手,不要输出任何解释性文字或额外字符。
            请根据以下模板输出 JSON 格式：
            {template_json}
            """},
            {"role": "user", "content": f"""
            请为主题 "{state.topic}"（面向 {state.audience_level} 级别学习者）
            创建详细的大纲。

            大纲应包括：
            1. 引人注目的指南标题
            2. 主题介绍
            3. 4-6 个涵盖关键方面的主要章节，每个章节的标题需要包含章节序号，如第一章：xxxx
            4. 结论或总结

            对每个章节，提供清晰的标题和简要说明。
            """}
        ]

        # 调用 LLM 并获取 JSON 格式响应
        response = llm.call(messages=messages)

        # 解析 JSON 响应
        outline_dict = json.loads(response)
        self.state.guide_outline = GuideOutline(**outline_dict)

        # 确保输出目录存在
        os.makedirs("output", exist_ok=True)

        # 将大纲保存到文件
        with open("output/guide_outline.json", "w", encoding='utf-8') as f:
            json.dump(outline_dict, f, indent=2, ensure_ascii=False)

        print(f"已生成包含 {len(self.state.guide_outline.sections)} 个章节的大纲")
        return self.state.guide_outline

    @listen(create_guide_outline)
    def write_and_compile_guide(self, outline):
        """撰写各章节并汇总生成最终指南"""
        print("正在撰写章节并汇总指南...")
        completed_sections = []

        # 逐节处理以保持上下文
        for section in outline.sections:
            print(f"正在处理章节：{section.title}")

            # 构建前置章节内容
            if completed_sections:
                previous_sections_text = "# 已完成章节\n\n"
                for title in completed_sections:
                    previous_sections_text += f"## {title}\n\n"
                    previous_sections_text += self.state.sections_content.get(title, "") + "\n\n"
            else:
                previous_sections_text = "尚未撰写任何章节。"

            # 调用 ContentCrew 生成本节内容
            result = ContentCrew().crew().kickoff(inputs={
                "section_title": section.title,
                "section_description": section.description,
                "audience_level": self.state.audience_level,
                "previous_sections": previous_sections_text,
                "draft_content": ""
            })

            # 存储章节内容
            self.state.sections_content[section.title] = ContentCrew.extract_markdown_content(result.raw)
            completed_sections.append(section.title)
            print(f"章节完成：{section.title}")

        # 汇总最终指南
        guide_content = f"# {outline.title}\n\n"
        guide_content += f"## 引言\n\n{outline.introduction}\n\n"

        for section in outline.sections:
            guide_content += self.state.sections_content.get(section.title, "") + "\n\n"

        guide_content += f"## 结论\n\n{outline.conclusion}\n\n"

        # 保存完整指南
        with open("output/complete_guide.md", "w") as f:
            f.write(guide_content)

        print("\n完整指南已保存至 output/complete_guide.md")
        return "指南创建完成"


def kickoff():
    """启动指南创建流程"""
    GuideCreatorFlow().kickoff()
    print("\n=== 流程完成 ===")
    print("你的综合指南已保存在 output 目录。")
    print("打开 output/complete_guide.md 查看。")


def plot():
    """生成流程可视化图"""
    flow = GuideCreatorFlow()
    flow.plot("guide_creator_flow")
    print("流程可视化已保存为 guide_creator_flow.html")

if __name__ == "__main__":
    kickoff()
