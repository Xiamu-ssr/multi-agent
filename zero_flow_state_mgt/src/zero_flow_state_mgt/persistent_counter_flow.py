from crewai.flow.flow import Flow, listen, start
from crewai.flow.persistence import persist
from pydantic import BaseModel

class CounterState(BaseModel):
    value: int = 0

@persist()  # Apply to the entire flow class
class PersistentCounterFlow(Flow[CounterState]):
    def __init__(self, **kwargs):
        # 使用固定的标识符来确保状态持久化
        super().__init__(**kwargs)
        # 可以通过设置一个固定的标识符来确保状态一致性
        
    @start()
    def increment(self):
        self.state.value += 1
        print(f"Incremented to {self.state.value}")
        return self.state.value

    @listen(increment)
    def double(self, value):
        self.state.value = value * 2
        print(f"Doubled to {self.state.value}")
        return self.state.value

def run():  
    # First run
    flow1 = PersistentCounterFlow()
    result1 = flow1.kickoff()
    print(f"First run result: {result1}")

    # Second run - state is automatically loaded
    flow2 = PersistentCounterFlow()
    result2 = flow2.kickoff()
    print(f"Second run result: {result2}")  # Will be higher due to persisted state

if __name__ == "__main__":
    run()