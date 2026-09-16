# Multi-Agent Cloud Service Categorization System
## Comprehensive Project Report & Academic Outline

---

## 1. Abstract
The proliferation of cloud computing providers offering varied Quality of Service (QoS), pricing models, and service architectures makes finding the optimal cloud service a complex multi-criteria optimization challenge. This project implements a decentralized multi-agent system comprising a Client Agent, Negotiator Agent, and Seller Agent, integrated with a Mamdani-style Fuzzy Logic Inference Engine and an informed $A^*$ heuristic search algorithm. The system evaluates multidimensional cloud attributes (exploitation time, cost, and trustworthiness) and returns the most desirable candidate matching user-defined constraints. A responsive web interface provides complete transparency into the negotiation dialogue, algorithmic scores, and comparative metrics.

---

## 2. Introduction

### 2.1 Problem Statement
Cloud consumers frequently face "choice overload" when selecting among Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS). Traditional keyword or filter-based search engines lack the reasoning required to balance non-linear trade-offs between pricing, reliability, and execution latency.

### 2.2 Motivation
Automated service discovery requires:
1. **Decoupled Roles**: Consumers, brokers, and service providers have competing objectives that require agent-based negotiation.
2. **Soft Constraint Handling**: Rigid binary constraints fail to capture subtle linguistic preferences (e.g., "reasonably priced and highly reliable").
3. **Informed Exploration**: Brute-force scanning does not scale when candidate pools grow large.

### 2.3 Objective
To design, implement, and validate an end-to-end multi-agent system that:
- Categorizes cloud services into SaaS, IaaS, and PaaS.
- Employs fuzzy logic to calculate continuous desirability scores.
- Applies $A^*$ heuristic search to isolate the globally optimal candidate.
- Logs and visualizes the negotiation steps live on a modern dashboard.

---

## 3. Literature Review
This implementation is grounded in the foundational methodology proposed by:
- **Reference Paper**: *“Multiple Intelligent Agent Coordination Strategy for Categorizing and Searching Appropriate Cloud Services”* (IEEE, 2017).
- **Core Insights**:
  - Highlights the role of autonomous software agents in eliminating human-in-the-loop bottlenecks during cloud procurement.
  - Proves the mathematical validity of applying fuzzy logic to convert non-linear cloud QoS parameters into a normalized single score.
  - Demonstrates that heuristic graph search ($A^*$) outperforms unguided search in finding optimal trade-offs.

---

## 4. System Architecture

```text
[ Client Browser ] <==== HTTP / JSON ====> [ Flask Server (app.py) ]
                                                    |
         +------------------------------------------+------------------------------------------+
         |                                          |                                          |
         v                                          v                                          v
+-----------------+                      +--------------------+                      +-----------------+
|   ClientAgent   | <=== Request / ====> |  NegotiatorAgent   | <=== Availability == |   SellerAgent   |
| (Requirements)  |      Contracts       |  (Central Broker)  |      & Pricing ===== |  (Provider Rep) |
+-----------------+                      +---------+----------+                      +-----------------+
                                                   |
                        +--------------------------+--------------------------+
                        |                                                     |
                        v                                                     v
            +-----------------------+                             +-----------------------+
            |  Fuzzy Logic Engine   |                             |   A* Search Engine    |
            |    (scikit-fuzzy)     |                             |  - Cost Penalty g(n)  |
            | - Time, Cost, Trust   |                             |  - Heuristic h(n)     |
            | - Mamdani Rules       |                             |  - Priority Queue     |
            +-----------------------+                             +-----------------------+
                        |                                                     |
                        +--------------------------+--------------------------+
                                                   |
                                                   v
                                     +---------------------------+
                                     |      SQLite Database      |
                                     | (users, services, logs,   |
                                     |  providers, contracts)    |
                                     +---------------------------+
```

---

## 5. Methodology

### 5.1 Fuzzy Logic Engine (`fuzzy/fuzzy_engine.py`)
- **Universes of Discourse**:
  - `time`: $[0, 10]$ (mapped from max duration up to 24h)
  - `cost`: $[0, 10]$ (mapped from hourly price up to $8/hr)
  - `trust`: $[0.0, 1.0]$ (direct vendor trust rating)
  - `score`: $[0.0, 1.0]$ (output desirability)
- **Membership Functions**:
  - Triangular membership functions (`trimf`) partitioned into `Low` and `High` for all antecedents and consequents.
- **Rule Base**:
  - **Rule 1**: $\text{IF } \text{time is LOW} \land \text{cost is LOW} \land \text{trust is HIGH} \implies \text{score is GOOD}$
  - **Rule 2**: $\text{IF } \text{time is HIGH} \lor \text{cost is HIGH} \lor \text{trust is LOW} \implies \text{score is BAD}$
- **Defuzzification**: Centroid defuzzification via `skfuzzy.control.ControlSystemSimulation`.

### 5.2 A\* Search Algorithm (`search/astar.py`)
- **Node Representation**: Each candidate cloud service $n$.
- **Cost Function $g(n)$**:
  $$g(n) = \frac{\text{price}}{20.0}$$
  Represents normalized economic cost penalty.
- **Heuristic Function $h(n)$**:
  $$h(n) = (\text{fuzzy\_score} \times 0.7) + (\text{trustworthiness} \times 0.3)$$
- **Evaluation Function $f(n)$**:
  Since standard $A^*$ minimizes cost, we invert maximization:
  $$f(n) = -\left(h(n) - 0.3 \cdot g(n)\right)$$
- **Priority Queue**: Implemented via Python's standard `heapq` with tie-breaker indices.

### 5.3 Multi-Agent Coordination (`agents/`)
- **`ClientAgent`**: Generates and submits structured demand parameters: `service_type`, `max_price`, `min_trust`, `duration`.
- **`NegotiatorAgent`**: Orchestrates database querying, fuzzy scoring, $A^*$ selection, and contract finalization.
- **`SellerAgent`**: Asserts provider ownership and validates SLA fulfillment before contract sealing.

---

## 6. Implementation

### 6.1 Technology Stack
- **Language**: Python 3.10
- **Web Layer**: Flask 3.0.0 (session handling, templating, JSON REST API)
- **Storage**: Native SQLite3
- **Logic & Compute**: `scikit-fuzzy 0.4.2`, `numpy 1.26.4`, `matplotlib 3.8.0`
- **Frontend**: Vanilla HTML5, Modern CSS3 with dark mode and glassmorphism, Vanilla JavaScript ES6+
- **Charting**: Chart.js v4.4.1

### 6.2 Database Schema
1. `users`: Stores credentials, unique user keys (`KEY-XXXX-###`), and timestamps.
2. `providers`: 10 cloud providers with trust scores and geographical locations.
3. `services`: 20 cloud services with hardware specs (CPU, RAM, bandwidth, duration, price, category).
4. `contracts`: Finalized service contracts linking user, service, final price, and fuzzy score.
5. `agent_logs`: Append-only audit trail logging every message exchanged between agents.

---

## 7. Results & Discussion

### 7.1 Key Screenshots to Include in Final Report
1. **Login & Registration Page**: Demonstrating key-based authentication.
2. **Dashboard Overview**: 5-column live statistics grid and service-type selector.
3. **Parameter Configuration**: Dynamic sliders adjusting maximum price and trust thresholds.
4. **Negotiation Loading State**: Real-time spinner indicating agent processing.
5. **Winner Hero Card**: Highlighting winning service with radial score circle and compute specs.
6. **Candidates Comparison Table**: Full table categorizing services into Winner, Eligible, and Rejected states.
7. **Fuzzy Score Bar Chart**: Horizontal bar comparison highlighting chosen candidate.
8. **Candidate Distribution Doughnut Chart**: Proportion of evaluated services across categories.
9. **Agent Conversation Log**: Terminal trace displaying multi-agent interaction.
10. **Graceful Error Handling**: Fallback screen when constraints are overly restrictive.

### 7.2 Sample Numerical Evaluation
- **Input Parameters**: Service Type = `SaaS`, Max Price = `$5.00`, Min Trust = `0.75`
- **Output Match**: `DataForge AI OCR API`
- **Fuzzy Desirability Score**: $0.765$
- **Contract Generated**: Active in database with ID `#1`

---

## 8. Conclusion
The Multi-Agent Cloud Service Categorization System successfully demonstrates that agent-based decentralized negotiation coupled with fuzzy-heuristic reasoning provides a fast, robust, and transparent solution for cloud service selection. The implementation runs with minimal dependencies, zero ORM overhead, and delivers full algorithmic visibility.

---

## 9. Future Work
1. **Live Cloud API Integration**: Connecting the `SellerAgent` directly to AWS Cost Explorer, Azure Resource Graph, or GCP Pricing APIs.
2. **Ontology-Based Matching**: Incorporating OWL/RDF web ontologies for semantically rich cloud capability definitions.
3. **Dynamic Trust Evolution**: Applying reinforcement learning to update provider trust scores based on historical SLA compliance.
4. **Concurrency & Asynchronous Protocols**: Transitioning internal agent messaging to FIPA-ACL protocols over WebSockets.

---

## 10. References
1. *“Multiple Intelligent Agent Coordination Strategy for Categorizing and Searching Appropriate Cloud Services”*, IEEE International Conference on Cloud Computing, 2017.
2. scikit-fuzzy Documentation, *Fuzzy Logic Toolbox for SciPy*, https://pythonhosted.org/scikit-fuzzy/
3. Flask Documentation (v3.0.x), Pallets Projects, https://flask.palletsprojects.com/
4. Chart.js Documentation (v4.x), https://www.chartjs.org/docs/
