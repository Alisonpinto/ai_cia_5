import os
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Universes
time_universe = np.arange(0, 11, 1)       # 0..10
cost_universe = np.arange(0, 11, 1)       # 0..10
trust_universe = np.arange(0, 1.05, 0.05)  # 0..1

# Antecedents
time_var = ctrl.Antecedent(time_universe, 'time')
cost_var = ctrl.Antecedent(cost_universe, 'cost')
trust_var = ctrl.Antecedent(trust_universe, 'trust')

# Consequent
score_var = ctrl.Consequent(np.arange(0, 1.05, 0.05), 'score')

# Membership functions (triangular)
time_var['low'] = fuzz.trimf(time_universe, [0, 0, 5])
time_var['high'] = fuzz.trimf(time_universe, [5, 10, 10])

cost_var['low'] = fuzz.trimf(cost_universe, [0, 0, 5])
cost_var['high'] = fuzz.trimf(cost_universe, [5, 10, 10])

trust_var['low'] = fuzz.trimf(trust_universe, [0, 0, 0.5])
trust_var['high'] = fuzz.trimf(trust_universe, [0.5, 1, 1])

score_var['bad'] = fuzz.trimf(score_var.universe, [0, 0, 0.5])
score_var['good'] = fuzz.trimf(score_var.universe, [0.5, 1, 1])

# Rules
rule1 = ctrl.Rule(time_var['low'] & cost_var['low'] & trust_var['high'], score_var['good'])
rule2 = ctrl.Rule(time_var['high'] | cost_var['high'] | trust_var['low'], score_var['bad'])

system = ctrl.ControlSystem([rule1, rule2])
simulator = ctrl.ControlSystemSimulation(system)

def evaluate_service(time, cost, trust):
    """
    time:  numeric, will be clipped to [0,10]
    cost:  numeric, will be clipped to [0,10]
    trust: numeric 0..1, will be clipped to [0,1]
    Returns: float score between 0 and 1
    """
    try:
        t = float(np.clip(time, 0, 10))
        c = float(np.clip(cost, 0, 10))
        tr = float(np.clip(trust, 0, 1))

        sim = ctrl.ControlSystemSimulation(system)
        sim.input['time'] = t
        sim.input['cost'] = c
        sim.input['trust'] = tr
        sim.compute()
        return round(float(sim.output['score']), 3)
    except Exception:
        return 0.5

def score_service_row(service_row):
    """
    Takes a sqlite3.Row (from services table) and returns fuzzy score.
    Maps:
        time  = min(service_row['duration'] / 2.4, 10)  # 24h -> 10
        cost  = min(service_row['price'] * 1.25, 10)    # 8$/h -> 10
        trust = service_row['trustworthiness']
    Returns evaluate_service(time, cost, trust)
    """
    time = min(service_row['duration'] / 2.4, 10)
    cost = min(service_row['price'] * 1.25, 10)
    trust = service_row['trustworthiness']
    return evaluate_service(time, cost, trust)

def generate_membership_plots(out_dir="static/plots"):
    """
    Ensures out_dir exists.
    Saves two PNG files using matplotlib:
        - membership_inputs.png : 3 subplots (time, cost, trust) showing LOW/HIGH
        - membership_output.png : score showing BAD/GOOD
    Use Agg backend so it works headless.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not os.path.isabs(out_dir):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.path.join(base_dir, out_dir)

    os.makedirs(out_dir, exist_ok=True)

    # 1. Inputs Plot (3 subplots)
    fig, (ax0, ax1, ax2) = plt.subplots(nrows=3, figsize=(8, 9))

    ax0.plot(time_universe, time_var['low'].mf, 'b', linewidth=1.5, label='Low')
    ax0.plot(time_universe, time_var['high'].mf, 'g', linewidth=1.5, label='High')
    ax0.set_title('Time (Exploitation Moment)')
    ax0.set_ylabel('Membership')
    ax0.legend()
    ax0.grid(True, linestyle='--', alpha=0.5)

    ax1.plot(cost_universe, cost_var['low'].mf, 'b', linewidth=1.5, label='Low')
    ax1.plot(cost_universe, cost_var['high'].mf, 'r', linewidth=1.5, label='High')
    ax1.set_title('Cost (Exploitation Cost)')
    ax1.set_ylabel('Membership')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2.plot(trust_universe, trust_var['low'].mf, 'r', linewidth=1.5, label='Low')
    ax2.plot(trust_universe, trust_var['high'].mf, 'g', linewidth=1.5, label='High')
    ax2.set_title('Trust (Trustworthiness)')
    ax2.set_ylabel('Membership')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    inputs_path = os.path.join(out_dir, "membership_inputs.png")
    fig.savefig(inputs_path, dpi=200)
    plt.close(fig)

    # 2. Output Plot
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(score_var.universe, score_var['bad'].mf, 'r', linewidth=1.5, label='Bad')
    ax.plot(score_var.universe, score_var['good'].mf, 'g', linewidth=1.5, label='Good')
    ax.set_title('Score (Desirability)')
    ax.set_ylabel('Membership')
    ax.set_xlabel('Score')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    output_path = os.path.join(out_dir, "membership_output.png")
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

if __name__ == "__main__":
    print("Test cases:")
    print("  low time, low cost, high trust ->", evaluate_service(2, 2, 0.95))
    print("  high time, high cost, low trust ->", evaluate_service(9, 9, 0.2))
    print("  mixed ->", evaluate_service(5, 4, 0.75))
    generate_membership_plots()
    print("Plots saved to static/plots/")
