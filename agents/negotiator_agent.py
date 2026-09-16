import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

try:
    from agents.seller_agent import SellerAgent
except ImportError:
    from seller_agent import SellerAgent

from fuzzy.fuzzy_engine import score_service_row
from search.astar import astar_explain

class NegotiatorAgent:
    def __init__(self, db):
        self.db = db

    def handle_request(self, request):
        """
        Orchestrates the full flow. Returns a result dict:

            {
                'success': bool,
                'chosen': dict or None,
                'candidates': list of dicts (all scored services),
                'total_considered': int,
                'filtered_count': int,
                'contract_id': int or None,
                'reason': str  # if failure
            }
        """
        # 1. Log receipt
        self.db.log('NEGOTIATOR', "Received request, gathering services...")

        # 2. Fetch services of requested type
        rows = self.db.get_services_by_type(request['service_type'])
        self.db.log('NEGOTIATOR', f"Found {len(rows)} candidate services")

        # 3. Check if none
        if not rows:
            self.db.log('NEGOTIATOR', "No services found for requested type. Negotiation failed.")
            return {
                'success': False,
                'chosen': None,
                'candidates': [],
                'total_considered': 0,
                'filtered_count': 0,
                'contract_id': None,
                'reason': 'No services of that type'
            }

        # 4. Score each with fuzzy
        scored = []
        for r in rows:
            d = dict(r)
            d['fuzzy_score'] = score_service_row(r)
            scored.append(d)
        self.db.log('FUZZY', f"Scored {len(scored)} services with fuzzy engine")

        # 5. Run A*
        prefs = {
            'max_price': request['max_price'],
            'min_trust': request['min_trust'],
            'min_score': request.get('min_score', 0.0),
            'service_type': request['service_type']
        }
        explanation = astar_explain(scored, prefs)
        self.db.log('ASTAR', f"Filtered to {explanation['filtered_count']} of {explanation['total_count']} services")
        for reason in explanation['rejected_reasons']:
            self.db.log('ASTAR', f"  - rejected: {reason}")

        # 6. If no chosen
        if not explanation['chosen']:
            self.db.log('NEGOTIATOR', "No service matched. Negotiation failed.")
            return {
                'success': False,
                'chosen': None,
                'candidates': scored,
                'total_considered': explanation['total_count'],
                'filtered_count': explanation['filtered_count'],
                'contract_id': None,
                'reason': 'No service matched criteria'
            }

        # 7. Seller confirmation
        chosen = explanation['chosen']
        seller = SellerAgent(chosen['provider_id'], chosen['provider_name'], self.db)
        seller.confirm(chosen)

        # 8. Create contract
        contract_id = self.db.create_contract(
            user_id=request['user_id'],
            service_id=chosen['id'],
            final_price=chosen['price'],
            fuzzy_score=chosen['fuzzy_score']
        )
        self.db.log('NEGOTIATOR', f"Contract #{contract_id} created for '{chosen['name']}'")

        # 9. Return success dict
        return {
            'success': True,
            'chosen': chosen,
            'candidates': scored,
            'total_considered': explanation['total_count'],
            'filtered_count': explanation['filtered_count'],
            'contract_id': contract_id,
            'reason': ''
        }

    def reset_session_logs(self):
        self.db.reset_logs()
        self.db.log('SYSTEM', 'Agent session started')

if __name__ == "__main__":
    from database.db import Database
    try:
        from agents.client_agent import ClientAgent
    except ImportError:
        from client_agent import ClientAgent

    db = Database()
    db.reset_logs()

    client = ClientAgent(user_id=1, username='demo', db=db)
    negotiator = NegotiatorAgent(db=db)

    req = client.build_request(
        service_type='SaaS',
        max_price=5.0,
        min_trust=0.75,
        min_score=0.0,
        duration=4
    )
    result = negotiator.handle_request(req)

    print("\n--- RESULT ---")
    print("Success      :", result['success'])
    print("Chosen       :", result['chosen']['name'] if result['chosen'] else None)
    print("Fuzzy score  :", result['chosen']['fuzzy_score'] if result['chosen'] else None)
    print("Contract id  :", result.get('contract_id'))

    if result['chosen']:
        client.receive_contract(result['contract_id'], result['chosen']['name'])

    print("\n--- AGENT LOG ---")
    for row in reversed(db.get_logs()):
        print(f"[{row['agent_type']:10}] {row['message']}")
