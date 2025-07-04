#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from zero_memory.crew import ZeroMemory

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year)
    }
    
    try:
        ZeroMemory().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        ZeroMemory().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ZeroMemory().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    
    try:
        ZeroMemory().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


# 检查存储权限
def check_storage_permission():
    import os
    from crewai.utilities.paths import db_storage_path

    storage_path = db_storage_path()
    print(f"Storage path: {storage_path}")
    print(f"Path exists: {os.path.exists(storage_path)}")
    print(f"Is writable: {os.access(storage_path, os.W_OK) if os.path.exists(storage_path) else 'Path does not exist'}")

    # Create with proper permissions
    if not os.path.exists(storage_path):
        os.makedirs(storage_path, mode=0o755, exist_ok=True)
        print(f"Created storage directory: {storage_path}")

# 检查ChromaDB集合
def check_chroma_collection():
    import os
    import chromadb
    from crewai.utilities.paths import db_storage_path

    # Connect to CrewAI's ChromaDB
    storage_path = db_storage_path()
    chroma_path = os.path.join(storage_path, "knowledge")

    if os.path.exists(chroma_path):
        client = chromadb.PersistentClient(path=chroma_path)
        collections = client.list_collections()

        print("ChromaDB Collections:")
        for collection in collections:
            print(f"  - {collection.name}: {collection.count()} documents")
    else:
        print("No ChromaDB storage found")

def main():
    # check_storage_permission()
    check_chroma_collection()
    
if __name__ == "__main__":
    main()
