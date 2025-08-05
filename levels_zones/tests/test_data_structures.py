"""
Test to understand actual HVN and Camarilla data structures
"""

import sys
from pathlib import Path

# Add levels_zones directory to path
levels_zones_root = Path(__file__).parent.parent
sys.path.insert(0, str(levels_zones_root))

def inspect_timeframe_result():
    """Create a sample TimeframeResult to see its structure"""
    print("=== TIMEFRAME RESULT INSPECTION ===")
    
    from calculations.volume.hvn_engine import TimeframeResult
    
    # Try to create an instance and see what parameters it needs
    try:
        # Check if it's a dataclass by looking at its signature
        import inspect
        sig = inspect.signature(TimeframeResult.__init__)
        print(f"TimeframeResult.__init__ signature: {sig}")
        
        # Check if it has any class-level hints
        if hasattr(TimeframeResult, '__annotations__'):
            print(f"TimeframeResult annotations: {TimeframeResult.__annotations__}")
            
        # Try to see the source or docstring
        if TimeframeResult.__doc__:
            print(f"TimeframeResult docstring: {TimeframeResult.__doc__}")
            
    except Exception as e:
        print(f"Error inspecting TimeframeResult: {e}")

def inspect_camarilla_result():
    """Create a sample CamarillaResult to see its structure"""
    print("\n=== CAMARILLA RESULT INSPECTION ===")
    
    from calculations.pivots.camarilla_engine import CamarillaResult
    
    try:
        import inspect
        sig = inspect.signature(CamarillaResult.__init__)
        print(f"CamarillaResult.__init__ signature: {sig}")
        
        if hasattr(CamarillaResult, '__annotations__'):
            print(f"CamarillaResult annotations: {CamarillaResult.__annotations__}")
            
        if CamarillaResult.__doc__:
            print(f"CamarillaResult docstring: {CamarillaResult.__doc__}")
            
    except Exception as e:
        print(f"Error inspecting CamarillaResult: {e}")

def test_hvn_engine():
    """Test running the actual HVN engine with sample data"""
    print("\n=== TESTING HVN ENGINE ===")
    
    try:
        from calculations.volume.hvn_engine import HVNEngine
        
        # Try to create the engine
        hvn_engine = HVNEngine()
        print(f"✅ HVNEngine created successfully")
        
        # See what methods it has
        methods = [method for method in dir(hvn_engine) if not method.startswith('_')]
        print(f"HVNEngine methods: {methods}")
        
    except Exception as e:
        print(f"❌ Error with HVNEngine: {e}")
        import traceback
        traceback.print_exc()

def test_camarilla_engine():
    """Test running the actual Camarilla engine"""
    print("\n=== TESTING CAMARILLA ENGINE ===")
    
    try:
        from calculations.pivots.camarilla_engine import CamarillaEngine
        
        camarilla_engine = CamarillaEngine()
        print(f"✅ CamarillaEngine created successfully")
        
        methods = [method for method in dir(camarilla_engine) if not method.startswith('_')]
        print(f"CamarillaEngine methods: {methods}")
        
    except Exception as e:
        print(f"❌ Error with CamarillaEngine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("DATA STRUCTURES INSPECTION")
    print("=" * 50)
    
    inspect_timeframe_result()
    inspect_camarilla_result()
    test_hvn_engine()
    test_camarilla_engine()
    
    print("\n" + "=" * 50)
    print("Inspection complete!")