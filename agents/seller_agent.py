class SellerAgent:
    def __init__(self, provider_id, provider_name, db):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.db = db

    def can_fulfill(self, service_row):
        """Returns True if this seller owns the given service."""
        return service_row['provider_id'] == self.provider_id

    def confirm(self, service_row):
        """
        Logs that this seller confirms the service.
        Returns True.
        """
        self.db.log('SELLER', f"[{self.provider_name}] Confirming '{service_row['name']}' at ${service_row['price']}/hr")
        return True
