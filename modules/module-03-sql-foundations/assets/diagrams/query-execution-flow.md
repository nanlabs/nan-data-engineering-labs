# SQL Query Execution Flow

```mermaid
flowchart TD
    Start([SQL Query]) --> Parser[Parser]
    Parser --> |Syntax Check| ValidSyntax{Valid?}
    ValidSyntax --> |No| SyntaxError[Syntax Error]
    ValidSyntax --> |Yes| Rewriter[Query Rewriter]

    Rewriter --> |Simplify & Normalize| Planner[Query Planner]
    Planner --> |Analyze Paths| CostEstimator[Cost Estimator]

    CostEstimator --> |Evaluate Options| BestPlan{Select Best Plan}
    BestPlan --> SeqScan[Sequential Scan]
    BestPlan --> IndexScan[Index Scan]
    BestPlan --> BitmapScan[Bitmap Scan]
    BestPlan --> HashJoin[Hash Join]
    BestPlan --> NestedLoop[Nested Loop Join]
    BestPlan --> MergeJoin[Merge Join]

    SeqScan --> Executor[Query Executor]
    IndexScan --> Executor
    BitmapScan --> Executor
    HashJoin --> Executor
    NestedLoop --> Executor
    MergeJoin --> Executor

    Executor --> |Process Data| ResultSet[Result Set]
    ResultSet --> End([Return Results])

    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style Parser fill:#fff3cd
    style Planner fill:#fff3cd
    style CostEstimator fill:#fff3cd
    style Executor fill:#d4edda
    style ResultSet fill:#d4edda
    style SyntaxError fill:#f8d7da
```

## Execution Phases

### 1. Parsing
- **Input**: Raw SQL text
- **Process**: Lexical analysis, syntax validation
- **Output**: Parse tree (AST)

### 2. Query Rewriting
- **Input**: Parse tree
- **Process**: View expansion, rule application, simplification
- **Output**: Rewritten query tree

### 3. Planning
- **Input**: Query tree
- **Process**:
  - Generate possible execution paths
  - Estimate cost for each path (I/O, CPU, memory)
  - Consider indexes, statistics, constraints
- **Output**: Optimal execution plan

### 4. Execution
- **Input**: Execution plan
- **Process**: Execute operators in plan order
- **Output**: Result rows

## Access Methods

| Method | Use Case | Cost |
|--------|----------|------|
| **Sequential Scan** | Small tables, no index available | High for large tables |
| **Index Scan** | Selective queries, ordered results | Low for selective queries |
| **Bitmap Scan** | Medium selectivity, multiple indexes | Medium |
| **Index-Only Scan** | All columns in index | Very low |

## Join Algorithms

| Algorithm | Best For | Memory |
|-----------|----------|--------|
| **Nested Loop** | Small tables, indexed join key | Low |
| **Hash Join** | Large tables, equality join | High |
| **Merge Join** | Sorted inputs, equality join | Medium |
