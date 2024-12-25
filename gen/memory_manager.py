memories = []

def remember(memory:str):
    """Stores a memory for the AI assistant"""
    memories.append(memory)
    print(f"Remembered '{memory}'")


def get_memories():
    """Returns a list of memories"""
    return [{'role': 'system', 'content': m} for m in memories]