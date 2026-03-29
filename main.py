import os
import sys

# Add the project root to sys.path to enable package imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

import src.modeling.model_one as model_one

def main():
    print("--- Drone Energy Consumption Analysis Pipeline ---")
    # Ensure results directories exist
    os.makedirs('results/figures', exist_ok=True)
    os.makedirs('results/tables', exist_ok=True)
    
    # Run the main modeling logic
    model_one.main()
    print("--- Analysis Complete. Results saved in results/ ---")

if __name__ == "__main__":
    main()
