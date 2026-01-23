
import sys
import os

# Add backend to sys.path
backend_path = os.path.abspath("c:/Users/John Kyalo/Desktop/REPOS/Agent47/backend")
sys.path.append(backend_path)

try:
    # Trigger full model registration by importing core.database
    import core.database
    from core.database.models import Base
    
    # We can also explicitly import the agent models if we want to be sure they load
    from agents.clara.app.models import ClaraSupportTicket
    from agents.jackie.app.models import JackieMarketingCampaign
    from agents.eric.app.models import EricLead
    from agents.joe.app.models import JoeMarketTrend
    from agents.shakes.app.models import ShakesContentProject
    
    print("Successfully imported all core and agent models!")
    print("SQLAlchemy registry check passed (no mapper collisions or reserved name errors).")
except Exception as e:
    print(f"FAILED to verify models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
