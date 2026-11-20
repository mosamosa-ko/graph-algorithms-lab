# Algorithms and mathematical notes

## 1. Graph model and connectivity

The implementation uses a finite undirected multigraph `G = (V, E)`. Each edge has
a stable identifier, so two edges with the same endpoints remain distinct. Self-loops
are outside the current model.

### Connectivity problem

**Input:** a graph `G` and a start vertex `r`.

**Output:** all vertices reachable from `r`, in deterministic breadth-first or
depth-first discovery order. The graph is connected exactly when one traversal
reaches every vertex.

```text
BFS(G, r):
    discovered <- {r}
    queue <- [r]
    while queue is not empty:
        v <- pop_front(queue)
        for each neighbor w of v:
            if w is not discovered:
                add w to discovered
                push_back(queue, w)
    return discovered
```

With incidence sets, each vertex and edge is inspected a constant number of times,
so the running time is `O(|V| + |E|)` and auxiliary space is `O(|V|)`.

**Correctness argument.** Every discovered vertex is reachable because it is added
across an edge from an already reachable vertex. Conversely, take any reachable
vertex and a shortest path from `r`; induction along that path shows BFS eventually
discovers every vertex on it.

## 2. Two-terminal series-parallel networks

A network is a tuple `(G, s, t)` with distinct terminals `s` and `t`. The TTSP class
used here is the smallest class satisfying:

1. A single edge `(s, t)` is TTSP.
2. The series composition of TTSP networks is TTSP.
3. The parallel composition of TTSP networks is TTSP.

The code permits n-ary S and P nodes, which are flattened forms of binary
composition. Associativity justifies this representation; it does not imply that a
decomposition is unique.

### Materialization

**Input:** an S/P tree.

**Output:** its concrete multigraph, terminals, and the same tree annotated with
concrete edge IDs.

```text
BUILD(node, s, t):
    if node is an edge:
        add edge (s, t)
    if node is parallel P(c1, ..., ck):
        BUILD(ci, s, t) for every child ci
    if node is series S(c1, ..., ck):
        create k-1 fresh boundary vertices
        BUILD each child between consecutive boundaries
```

The procedure creates each graph element once and therefore takes `O(|V| + |E|)`
time and space.

## 3. Reduction-based recognition and decomposition

### Problem

**Input:** an undirected loop-free multigraph `G` and designated terminals `(s, t)`.

**Output:** either rejection or an S/P decomposition tree whose materialization
constructs `G` with terminals `(s, t)`.

### Reductions

- **Parallel reduction:** replace two or more edges with identical endpoints by one
  virtual edge whose tree is a P-node over their trees.
- **Series reduction:** for a nonterminal degree-two vertex `v` with distinct
  neighbors `u` and `w`, replace `(u, v)` and `(v, w)` by one virtual edge `(u, w)`
  whose tree is an S-node.

```text
REDUCE-TTSP(G, s, t):
    attach one edge leaf to every original edge
    while more than one virtual edge remains:
        if a parallel-edge group exists:
            replace it by a P virtual edge
        else if a nonterminal degree-two vertex exists:
            replace its two edges by an S virtual edge
        else:
            reject
    accept iff the remaining virtual edge joins s and t
```

### Complexity

The implementation recomputes endpoint groups and incidences after each reduction.
There are at most `|E| - 1` reductions and each scan is `O(|V| + |E|)`, giving the
conservative bound `O((|V| + |E|)^2)` and linear active state. More sophisticated
data structures support linear-time recognition in the directed setting described
by Valdes, Tarjan, and Lawler (1982); this repository does not claim to reproduce
that algorithm.

### Correctness argument and scope

**Soundness of acceptance.** Initially every virtual edge is a base TTSP network.
Each parallel reduction records a valid parallel composition, and each series
reduction records a valid series composition. By induction over the reduction
sequence, every virtual edge represents exactly the subnetwork in its stored tree.
If the final edge joins `s` and `t`, its tree is therefore a construction certificate
for the original network.

**Completeness basis.** The method uses the standard inverse-reduction
characterization of two-terminal series-parallel networks: a non-base TTSP
construction exposes a reducible series or parallel structure. The test suite
exhausts all ordered binary S/P expressions through six edges, but that finite test
is evidence about the implementation—not a proof of the characterization. A fully
formal, machine-checked completeness proof is outside this release.

Terminal choice matters: a graph can be series-parallel under one notion or terminal
pair without being TTSP under another. This recognizer answers only the specified
two-terminal question.

## 4. Dynamic programming on the decomposition tree

### Two-terminal reliability

Every edge `e` independently survives with probability `p_e`. Compute the
probability that `s` remains connected to `t`.

For a tree node `x`, let `R(x)` be the probability that its local terminals connect:

```text
R(edge e)       = p_e
R(S(x1,...,xk)) = product_i R(xi)
R(P(x1,...,xk)) = 1 - product_i (1 - R(xi))
```

The series recurrence requires every component to connect. The parallel recurrence
uses the complementary event that every branch fails. Independence applies because
construction-tree branches have disjoint edge sets.

A postorder traversal evaluates each tree node once, so time and stack space are
`O(|E|)` in the worst case.

### Independent reference check

For small networks, the test oracle enumerates all `2^|E|` survival states, computes
each state's probability, and checks terminal connectivity directly. This costs
`O(2^|E| (|V| + |E|))` time. Agreement with the DP on tested instances is a strong
implementation check, not a general mathematical proof.

## 5. References

1. R. J. Duffin. “Topology of Series-Parallel Networks.” *JMAA* 10 (1965),
   303–318. <https://doi.org/10.1016/0022-247X(65)90125-3>
2. J. Valdes, R. E. Tarjan, E. L. Lawler. “The Recognition of Series Parallel
   Digraphs.” *SIAM J. Comput.* 11(2) (1982), 298–313.
   <https://doi.org/10.1137/0211023>
3. D. Eppstein. “Parallel Recognition and Decomposition of Two Terminal
   Series-Parallel Graphs.” *Information and Computation* 75(1) (1987), 15–38.
   <https://doi.org/10.1016/0890-5401(87)90061-7>
