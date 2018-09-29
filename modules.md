




In each module, we dive into the middle of a subject and swim our way out, going from the abstract to the concrete:
 * Abstract models
 * Fundamental challenges
 * Protocols and mechanisms


## Module 1: Time and Asynchrony

* The Synchronous and asynchronous network models. Partial orders.
* Clock skew.  Causality.  Causality violations.  
* FIFO, Causal and totally-ordered delivery and broadcast protocols. Lamport clocks.  Vector clocks. Consistent snapshots.

## Module 2: Fault Tolerance

* Fault models.  Reliability. Availability. Principles of redundancy.
* Partial failure.  Non-independence of faults. Replication anomalies (see also Module 3).
* Reliable delivery and broadcast.  Primary/Backup, Chain and Quorum replication.  Recovery. Write-ahead logging.  Checkpointing.  Failure detection.  

## Module 3: Consistency

* Consistency models (single-copy consistency, sequential consistency, linearizability, serializability, causal consistency and other weak models)
* Message reordering in the presence of redundancy.  Race conditions. Replica divergence.
* Consistency in replicated systems.   Two-phase locking.  Optimistic concurrency control.  Two-phase commit.  Consensus.

## Module 4: Parallelism and Scaleout

* Scaleability.  Data parallellism.  Embarrassing parallelism.
* Amdahl's law.  CALM Theorem.
* Distributed data processing systems and programming models.
