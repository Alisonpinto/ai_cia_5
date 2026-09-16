class ClientAgent:
    def __init__(self, user_id, username, db):
        self.user_id = user_id
        self.username = username
        self.db = db

    def build_request(self, service_type, max_price, min_trust, min_score=0.0, duration=2):
        """
        Builds a request dict and logs it.
        Returns:
            {
                'user_id': int,
                'username': str,
                'service_type': str,
                'max_price': float,
                'min_trust': float,
                'min_score': float,
                'duration': int
            }
        """
        self.db.log('CLIENT', f"[{self.username}] Requested {service_type} | max_price={max_price} | min_trust={min_trust}")
        return {
            'user_id': self.user_id,
            'username': self.username,
            'service_type': service_type,
            'max_price': max_price,
            'min_trust': min_trust,
            'min_score': min_score,
            'duration': duration
        }

    def receive_contract(self, contract_id, service_name):
        """
        Called when negotiator confirms the deal.
        Logs the receipt.
        """
        self.db.log('CLIENT', f"[{self.username}] Contract #{contract_id} confirmed for '{service_name}'")
