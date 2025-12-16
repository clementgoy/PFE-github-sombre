import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from agent.core.base_agent import BaseAgent
    print("BaseAgent imported")
    
    from agent.core.coordinator import Coordinator
    print("Coordinator imported")

    from agent.agents.specialist import SpecialistAgent
    print("SpecialistAgent imported")

    from agent.agents.foraging import ForagingAgent
    print("ForagingAgent imported")

    from agent.agents.extract import ExtractAgent
    print("ExtractAgent imported")
    
    from agent.agents.relations import RelationsAgent
    print("RelationsAgent imported")

    from agent.agents.structuring import StructuringAgent
    print("StructuringAgent imported")

    from agent.agents.schema import SchemaAgent
    print("SchemaAgent imported")

    from agent.agents.hypothesis import HypothesisAgent
    print("HypothesisAgent imported")

    from agent.agents.build_case import BuildCaseAgent
    print("BuildCaseAgent imported")

    from agent.agents.test_agent import TestAgent
    print("TestAgent imported")

    from agent.agents.presentation import PresentationAgent
    print("PresentationAgent imported")
    
    print("ALL IMPORTS SUCCESSFUL")

except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
