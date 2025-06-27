#!/usr/bin/env python
import sys
from debate_match_1.crew import DebateCrew

def run():
    """
    运行辩论赛 crew.
    """
    topic = input("用户辩题> ")
    
    # 创建辩论 crew 实例并直接运行辩论
    debate_crew = DebateCrew(max_rounds=3)
    result = debate_crew.run_debate(topic)
    
    print(f"\n=== 辩论结束 ===")
    print(f"最终结果: {result}")

def main():
    """主函数"""
    run()

def train():
    """
    训练 crew 以获得更好的结果.
    """
    topic = input("训练辩题> ")
    debate_crew = DebateCrew(max_rounds=2)
    
    try:
        debate_crew.crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs={"topic": topic})
    except Exception as e:
        raise Exception(f"训练时发生错误: {e}")

def replay():
    """
    重放 crew 执行以获得更好的结果.
    """
    try:
        debate_crew = DebateCrew()
        debate_crew.crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"重放时发生错误: {e}")

def test():
    """
    测试 crew 执行并返回结果.
    """
    topic = input("测试辞题> ")
    debate_crew = DebateCrew(max_rounds=1)
    
    try:
        result = debate_crew.crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs={"topic": topic})
        return result
    except Exception as e:
        raise Exception(f"测试时发生错误: {e}")

if __name__ == "__main__":
    run()