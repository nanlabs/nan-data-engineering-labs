# Window Functions Explained

## Concept Overview

```mermaid
flowchart LR
    subgraph "Regular Aggregation (GROUP BY)"
        Input1[10 rows] --> GroupBy[GROUP BY category]
        GroupBy --> Output1[3 rows<br/>one per group]
    end

    subgraph "Window Function"
        Input2[10 rows] --> WindowFunc[OVER ...]
        WindowFunc --> Output2[10 rows<br/>with calculated values]
    end

    style Input1 fill:#e1f5ff
    style Output1 fill:#d4edda
    style Input2 fill:#e1f5ff
    style Output2 fill:#fff3cd
```

**Key Difference**:
- **GROUP BY**: Collapses rows into groups
- **Window Functions**: Keep all rows, add calculated columns

---

## Window Function Components

```mermaid
graph TD
    WF[Window Function] --> Func[Function Type]
    WF --> Window[Window Specification]

    Func --> Rank[Ranking<br/>ROW_NUMBER, RANK, DENSE_RANK]
    Func --> Agg[Aggregate<br/>SUM, AVG, COUNT, MIN, MAX]
    Func --> Value[Value<br/>LAG, LEAD, FIRST_VALUE, LAST_VALUE]

    Window --> Partition[PARTITION BY<br/>Define groups]
    Window --> Order[ORDER BY<br/>Define ordering]
    Window --> Frame[Frame Clause<br/>Define row range]

    Partition -.-> Example1["PARTITION BY category"]
    Order -.-> Example2["ORDER BY price DESC"]
    Frame -.-> Example3["ROWS BETWEEN 2 PRECEDING AND CURRENT ROW"]

    style WF fill:#e1f5ff
    style Func fill:#d4edda
    style Window fill:#fff3cd
```

---

## ROW_NUMBER() vs RANK() vs DENSE_RANK()

```mermaid
graph TD
    subgraph "Sample Data: Products by Price"
        D1["Laptop: $1000"]
        D2["Monitor: $500"]
        D3["Keyboard: $500"]
        D4["Mouse: $100"]
    end

    subgraph "ROW_NUMBER()"
        R1["1 - Laptop"]
        R2["2 - Monitor"]
        R3["3 - Keyboard"]
        R4["4 - Mouse"]
    end

    subgraph "RANK()"
        RK1["1 - Laptop"]
        RK2["2 - Monitor"]
        RK3["2 - Keyboard"]
        RK4["4 - Mouse"]
    end

    subgraph "DENSE_RANK()"
        DR1["1 - Laptop"]
        DR2["2 - Monitor"]
        DR3["2 - Keyboard"]
        DR4["3 - Mouse"]
    end

    D1 --> R1
    D2 --> R2
    D3 --> R3
    D4 --> R4

    D1 --> RK1
    D2 --> RK2
    D3 --> RK3
    D4 --> RK4

    D1 --> DR1
    D2 --> DR2
    D3 --> DR3
    D4 --> DR4

    style R2 fill:#fff3cd
    style R3 fill:#fff3cd
    style RK2 fill:#ffcccc
    style RK3 fill:#ffcccc
    style RK4 fill:#cce5ff
    style DR4 fill:#d4edda
```

| Function | Ties? | Gap After Tie? |
|----------|-------|----------------|
| **ROW_NUMBER()** | ❌ No (arbitrary order) | N/A |
| **RANK()** | ✅ Yes (same rank) | ✅ Yes (skip numbers) |
| **DENSE_RANK()** | ✅ Yes (same rank) | ❌ No (consecutive) |

**Example**:
```sql
SELECT
    product_name,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) AS row_num,
    RANK() OVER (ORDER BY price DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY price DESC) AS dense_rank
FROM products;
```

---

## PARTITION BY Visualization

```mermaid
graph TD
    subgraph "Data"
        All[All Products]
    end

    subgraph "PARTITION BY category"
        P1[Electronics Group]
        P2[Books Group]
        P3[Furniture Group]
    end

    subgraph "Ranking Within Each Partition"
        E1["1. Laptop $1000<br/>2. Monitor $500<br/>3. Mouse $100"]
        B1["1. SQL Book $50<br/>2. Python Book $40"]
        F1["1. Chair $300<br/>2. Desk $200"]
    end

    All --> P1
    All --> P2
    All --> P3

    P1 --> E1
    P2 --> B1
    P3 --> F1

    style All fill:#e1f5ff
    style P1 fill:#d4edda
    style P2 fill:#fff3cd
    style P3 fill:#ffcccc
```

**Without PARTITION BY**: Ranks globally across all products
**With PARTITION BY category**: Ranks reset within each category

```sql
-- Global ranking
SELECT
    product_name,
    category,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) AS global_rank
FROM products;

-- Ranking per category
SELECT
    product_name,
    category,
    price,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS category_rank
FROM products;
```

---

## LAG() and LEAD() Flow

```mermaid
graph LR
    subgraph "Order Timeline"
        O1["Jan: $100"]
        O2["Feb: $150"]
        O3["Mar: $120"]
        O4["Apr: $180"]
    end

    subgraph "LAG (Previous Value)"
        L1["NULL"]
        L2["$100"]
        L3["$150"]
        L4["$120"]
    end

    subgraph "Current"
        C1["$100"]
        C2["$150"]
        C3["$120"]
        C4["$180"]
    end

    subgraph "LEAD (Next Value)"
        LD1["$150"]
        LD2["$120"]
        LD3["$180"]
        LD4["NULL"]
    end

    O1 --> C1
    O2 --> C2
    O3 --> C3
    O4 --> C4

    C1 -.->|look back| L1
    C2 -.->|look back| L2
    C3 -.->|look back| L3
    C4 -.->|look back| L4

    C1 -.->|look ahead| LD1
    C2 -.->|look ahead| LD2
    C3 -.->|look ahead| LD3
    C4 -.->|look ahead| LD4

    style L1 fill:#ffcccc
    style LD4 fill:#ffcccc
```

**Use Cases**:
- **LAG**: Compare with previous period (month-over-month growth)
- **LEAD**: Compare with next period (predict trends)

```sql
SELECT
    order_date,
    total_amount,
    LAG(total_amount) OVER (ORDER BY order_date) AS prev_order,
    total_amount - LAG(total_amount) OVER (ORDER BY order_date) AS change_from_prev,
    LEAD(total_amount) OVER (ORDER BY order_date) AS next_order
FROM orders;
```

---

## Running Total with Frame

```mermaid
graph TD
    subgraph "Sales Data"
        S1["Jan: $100"]
        S2["Feb: $150"]
        S3["Mar: $120"]
        S4["Apr: $180"]
    end

    subgraph "Running Total"
        RT1["$100<br/>(Jan)"]
        RT2["$250<br/>(Jan + Feb)"]
        RT3["$370<br/>(Jan + Feb + Mar)"]
        RT4["$550<br/>(All months)"]
    end

    subgraph "3-Month Moving Average"
        MA1["$100<br/>(only Jan)"]
        MA2["$125<br/>(Jan-Feb avg)"]
        MA3["$123<br/>(Jan-Mar avg)"]
        MA4["$150<br/>(Feb-Apr avg)"]
    end

    S1 --> RT1
    S1 --> S2
    S2 --> RT2
    S2 --> S3
    S3 --> RT3
    S3 --> S4
    S4 --> RT4

    S1 --> MA1
    S2 --> MA2
    S3 --> MA3
    S4 --> MA4

    style RT4 fill:#d4edda
    style MA4 fill:#fff3cd
```

```sql
-- Running total
SELECT
    month,
    sales,
    SUM(sales) OVER (ORDER BY month) AS running_total
FROM monthly_sales;

-- 3-month moving average
SELECT
    month,
    sales,
    AVG(sales) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3m
FROM monthly_sales;
```

---

## Frame Specifications

```mermaid
graph LR
    subgraph "Frame Types"
        F1[ROWS BETWEEN<br/>Physical rows]
        F2[RANGE BETWEEN<br/>Logical range by value]
    end

    subgraph "Boundaries"
        B1[UNBOUNDED PRECEDING<br/>Start of partition]
        B2[n PRECEDING<br/>N rows before current]
        B3[CURRENT ROW<br/>Current row]
        B4[n FOLLOWING<br/>N rows after current]
        B5[UNBOUNDED FOLLOWING<br/>End of partition]
    end

    F1 --> B1
    F1 --> B2
    F1 --> B3
    F1 --> B4
    F1 --> B5

    style F1 fill:#d4edda
    style F2 fill:#fff3cd
    style B3 fill:#e1f5ff
```

**Common Frames**:
```sql
-- All rows up to current (running total)
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- 3 rows centered window
ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING

-- All rows in partition
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
```

---

## Complete Example

```sql
SELECT
    product_name,
    category,
    price,

    -- Ranking functions
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS row_num,
    RANK() OVER (PARTITION BY category ORDER BY price DESC) AS rank,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY price DESC) AS dense_rank,

    -- Analytical functions
    LAG(price) OVER (PARTITION BY category ORDER BY price DESC) AS more_expensive,
    LEAD(price) OVER (PARTITION BY category ORDER BY price DESC) AS less_expensive,

    -- Aggregate as window function
    AVG(price) OVER (PARTITION BY category) AS avg_category_price,
    price - AVG(price) OVER (PARTITION BY category) AS diff_from_avg,

    -- First and last
    FIRST_VALUE(product_name) OVER (PARTITION BY category ORDER BY price DESC) AS most_expensive,
    LAST_VALUE(product_name) OVER (
        PARTITION BY category
        ORDER BY price DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS least_expensive

FROM products
ORDER BY category, price DESC;
```
