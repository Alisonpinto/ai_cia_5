import heapq
import os
import sys

def astar_select_best(services, user_prefs):
    """
    services: list of dicts or sqlite3.Row, each must have keys:
        'id', 'name', 'price', 'trustworthiness', 'fuzzy_score', 'service_type'
    user_prefs: dict with optional keys:
        'max_price'   (float, default 999)
        'min_trust'   (float 0..1, default 0.0)
        'min_score'   (float 0..1, default 0.0)
        'service_type' (str, optional - filters by type)

    Returns: single best service dict, or None if no candidate passes filters.
    """
    max_price = user_prefs.get('max_price', 999)
    min_trust = user_prefs.get('min_trust', 0.0)
    min_score = user_prefs.get('min_score', 0.0)
    service_type = user_prefs.get('service_type')

    heap = []
    counter = 0

    for item in services:
        s = dict(item)
        if s.get('price', 0) > max_price:
            continue
        if s.get('trustworthiness', 0.0) < min_trust:
            continue
        if s.get('fuzzy_score', 0.0) < min_score:
            continue
        if service_type and s.get('service_type') != service_type:
            continue

        g = s['price'] / 20.0
        h = s['fuzzy_score'] * 0.7 + s['trustworthiness'] * 0.3
        f = -(h - g * 0.3)

        heapq.heappush(heap, (f, counter, s))
        counter += 1

    if not heap:
        return None

    _, _, best = heapq.heappop(heap)
    return best

def astar_explain(services, user_prefs):
    """
    Returns a dict for the demo / agent log:
        {
            'filtered_count': int,
            'total_count': int,
            'chosen': dict or None,
            'rejected_reasons': list of strings (why each service was filtered out)
        }
    Useful for showing the A* decision process in the UI.
    """
    max_price = user_prefs.get('max_price', 999)
    min_trust = user_prefs.get('min_trust', 0.0)
    min_score = user_prefs.get('min_score', 0.0)
    service_type = user_prefs.get('service_type')

    total_count = len(services)
    candidates = []
    rejected_reasons = []

    for item in services:
        s = dict(item)
        name = s.get('name', f"Service #{s.get('id')}")
        reasons = []

        if s.get('price', 0) > max_price:
            reasons.append(f"price {s.get('price')} > max {max_price}")
        if s.get('trustworthiness', 0.0) < min_trust:
            reasons.append(f"trust {s.get('trustworthiness')} < min {min_trust}")
        if s.get('fuzzy_score', 0.0) < min_score:
            reasons.append(f"fuzzy score {s.get('fuzzy_score', 0.0)} < min {min_score}")
        if service_type and s.get('service_type') != service_type:
            reasons.append(f"service_type '{s.get('service_type')}' != '{service_type}'")

        if reasons:
            rejected_reasons.append(f"{name}: {', '.join(reasons)}")
        else:
            candidates.append(s)

    chosen = astar_select_best(candidates, user_prefs)

    return {
        'filtered_count': len(candidates),
        'total_count': total_count,
        'chosen': chosen,
        'rejected_reasons': rejected_reasons
    }

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    from fuzzy.fuzzy_engine import score_service_row
    import sqlite3

    # Connect to our seeded DB
    db_path = os.path.join("instance", "cloud_agents.db")
    if not os.path.exists(db_path):
        db_path = os.path.join(base_dir, "instance", "cloud_agents.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT s.*, p.name AS provider_name
        FROM services s
        JOIN providers p ON p.id = s.provider_id
        WHERE s.service_type = 'SaaS'
    """).fetchall()

    # Score each with fuzzy
    services = []
    for r in rows:
        d = dict(r)
        d['fuzzy_score'] = score_service_row(r)
        services.append(d)

    prefs = {'max_price': 5.0, 'min_trust': 0.75, 'min_score': 0.0}
    best = astar_select_best(services, prefs)
    print("Candidates:", len(services))
    print("Best service:", best['name'] if best else None)
    print("Fuzzy score :", best['fuzzy_score'] if best else None)
    print("Price       :", best['price'] if best else None)
