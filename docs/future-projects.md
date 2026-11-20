# Future research-project plans

These are plans, not completed projects. They should not be presented as existing
repositories until implementation and validation are complete.

## `gnn-from-scratch`

### Research purpose

Build a small, inspectable GNN stack that makes message passing, normalization,
aggregation, training, and evaluation explicit. The goal is to understand where
graph inductive bias enters—not to compete with PyTorch Geometric on features.

### Existing research to study

- GCN: Kipf and Welling (2017), <https://arxiv.org/abs/1609.02907>
- GraphSAGE: Hamilton, Ying, and Leskovec (2017),
  <https://arxiv.org/abs/1706.02216>
- GAT: Veličković et al. (2018), <https://arxiv.org/abs/1710.10903>
- Expressive power / 1-WL: Xu et al. (2019),
  <https://arxiv.org/abs/1810.00826>

### Implementation plan

1. Sparse adjacency and feature matrix conventions with explicit shape contracts.
2. NumPy reference implementations of GCN propagation and neighborhood aggregation.
3. PyTorch layers written without PyG, then gradient checks on tiny graphs.
4. GCN, GraphSAGE, and GAT under one training/evaluation interface.
5. Optional PyG comparison adapters kept outside the core implementation.

### Experiments

- Node classification on Cora/CiteSeer with fixed public splits and multiple seeds.
- Unit tests against hand-computed tiny graphs.
- Gradient checks and comparison with equivalent PyTorch/PyG layers when possible.
- Ablations for self-loops, normalization, depth, and aggregation.
- Oversmoothing measurements using representation similarity versus depth.

### Prerequisites

Linear algebra, probability, optimization, automatic differentiation, sparse
matrices, spectral graph theory basics, and careful ML evaluation.

### Expected artifacts

Typed source code, derivation notes, tests, fixed experiment configurations, raw
metrics, environment locks, plots generated from raw results, and a limitations
section. No leaderboard claim without comparable protocols.

## `dynamic-graph-bench`

### Research purpose

Create a controlled benchmark for graph algorithms under edge insertions and
deletions. The initial question is when incremental maintenance beats recomputation
for connectivity and simple local statistics.

### Existing research to study

- D. D. Sleator and R. E. Tarjan, “A Data Structure for Dynamic Trees” (1983),
  <https://doi.org/10.1016/0022-0000(83)90006-5>
- M. R. Henzinger and V. King, “Randomized Fully Dynamic Graph Algorithms with
  Polylogarithmic Time per Operation” (1995),
  <https://doi.org/10.1145/225058.225269>
- J. Holm, K. de Lichtenberg, and M. Thorup, “Poly-Logarithmic Deterministic Fully-
  Dynamic Algorithms for Connectivity...” (2001),
  <https://doi.org/10.1145/502090.502095>

### Implementation plan

1. Versioned update streams and immutable benchmark manifests.
2. Recompute-from-scratch BFS/DFS baseline.
3. Incremental connectivity for insertion-only streams using disjoint-set union.
4. Carefully scoped deletion-capable baseline; advanced dynamic trees only after
   correctness tests and literature review.
5. Adapter interface for independently maintained implementations.

### Experiments

- Synthetic Erdős–Rényi, Barabási–Albert, grid, and adversarial update streams.
- Public temporal-network datasets with documented licenses.
- Update latency distributions, query latency, peak memory, and correctness after
  every operation against full recomputation on small instances.
- Warmup, process isolation, repeated runs, confidence intervals, and environment
  capture. Separate algorithmic operation counts from wall-clock measurements.

### Prerequisites

Amortized analysis, disjoint-set union, trees and cuts, randomized algorithms,
benchmark methodology, statistics, and temporal-network data handling.

### Expected artifacts

Dataset/update-stream manifests, baseline implementations, oracle tests, a CLI,
raw benchmark tables, plotting scripts, environment metadata, and a report that
distinguishes empirical behavior from asymptotic guarantees.
