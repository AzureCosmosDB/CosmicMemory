"""
Utils module - Helper functions for CosmicMemory.
"""
from .processing import generate_embedding, summarize_thread
from .cosmos_interface import (
    create_container,
    insert_memory,
    semantic_search,
    recent_memories,
    remove_item,
    get_memories_by_user,
    get_memories_by_thread,
    get_summary_by_thread,
    get_memory_by_id
)

__all__ = [
    'generate_embedding',
    'summarize_thread',
    'create_container',
    'insert_memory',
    'semantic_search',
    'recent_memories',
    'remove_item',
    'get_memories_by_user',
    'get_memories_by_thread',
    'get_summary_by_thread',
    'get_memory_by_id'
]
