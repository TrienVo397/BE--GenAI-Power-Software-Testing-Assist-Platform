"""
Test script to verify LLM integration in chat endpoints
"""

import asyncio
from datetime import datetime

async def test_llm_import():
    """Test that we can import the LLM components"""
    try:
        from ai.agents.conversation_agent import graph, AgentState, llm
        print("✓ Successfully imported LLM components")
        return True
    except Exception as e:
        print(f"✗ Failed to import LLM components: {e}")
        return False

async def test_simple_llm_response():
    """Test simple LLM response"""
    try:
        from ai.agents.conversation_agent import llm
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content="You are a helpful QA testing assistant."),
            HumanMessage(content="Hello, how are you?")
        ]
        
        response = llm.invoke(messages)
        print(f"✓ Simple LLM response: {response.content[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Failed to get simple LLM response: {e}")
        return False

async def test_agent_response():
    """Test agent response"""
    try:
        from ai.agents.conversation_agent import graph, AgentState
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Create agent state
        conversation_state = AgentState(
            messages=[
                SystemMessage(content="You are a helpful QA testing assistant."),
                HumanMessage(content="Hello, how are you?")
            ],
            project_name="Test Project",
            context="",
            requirements=[],
            testCases=[]
        )
        
        # Test agent
        config = {"configurable": {"thread_id": "test-session"}}
        response = graph.invoke(conversation_state, config=config)  # type: ignore
        print(f"✓ Agent response received with {len(response.get('messages', []))} messages")
        return True
    except Exception as e:
        print(f"✗ Failed to get agent response: {e}")
        return False

async def main():
    print("Testing LLM Integration")
    print("=" * 50)
    
    # Test imports
    import_success = await test_llm_import()
    if not import_success:
        print("Cannot proceed with tests due to import failure")
        return
    
    # Test simple LLM
    await test_simple_llm_response()
    
    # Test agent
    await test_agent_response()
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main())
