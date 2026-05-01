# SQL Foundations - Assets

This directory contains visual diagrams and quick reference cheatsheets to supplement the SQL learning materials.

## 📊 Diagrams

Interactive Mermaid diagrams that visualize SQL concepts.

### [Query Execution Flow](diagrams/query-execution-flow.md)
**What**: Step-by-step visualization of how PostgreSQL processes SQL queries
**Covers**: Parser → Rewriter → Planner → Cost Estimator → Executor
**Use When**: Understanding EXPLAIN output, query optimization

**Key Concepts**:
- Parsing and syntax validation
- Query planning and cost estimation
- Access methods (Sequential, Index, Bitmap scans)
- Join algorithms (Nested Loop, Hash, Merge)

---

### [JOIN Types Visual Guide](diagrams/join-types.md)
**What**: Complete visual breakdown of all JOIN types with examples
**Covers**: INNER, LEFT, RIGHT, FULL OUTER JOINs

**Includes**:
- Visual representation of matching/non-matching rows
- Venn diagram comparisons
- Common patterns (finding unmatched rows, data integrity checks)
- Performance considerations

**Use When**:
- Choosing the right JOIN type for your query
- Understanding NULL values in JOIN results
- Debugging unexpected JOIN results

---

### [Window Functions Explained](diagrams/window-functions.md)
**What**: Deep dive into window function mechanics
**Covers**: ROW_NUMBER, RANK, PARTITION BY, LAG/LEAD, Frame clauses

**Key Visualizations**:
- Difference between GROUP BY and window functions
- ROW_NUMBER vs RANK vs DENSE_RANK comparison
- PARTITION BY grouping behavior
- LAG/LEAD timeline visualization
- Running totals and moving averages
- Frame specification examples

**Use When**:
- Implementing ranking within groups
- Calculating running totals or moving averages
- Comparing rows with previous/next values
- Understanding frame clauses (ROWS BETWEEN...)

---

## 📋 Cheatsheets

Quick reference guides with syntax, examples, and best practices.

### [SQL Basics](cheatsheets/sql-basics.md)
**Comprehensive reference** covering fundamental SQL operations.

**Sections**:
1. **SELECT & Projection**: Column selection, aliases, calculated columns
2. **WHERE - Filtering**: Comparison operators, IN, BETWEEN, LIKE, NULL handling
3. **ORDER BY - Sorting**: Single/multiple columns, NULL ordering
4. **LIMIT & OFFSET**: Pagination formulas and patterns
5. **Aggregate Functions**: COUNT, SUM, AVG, MIN, MAX
6. **GROUP BY**: Grouping data, HAVING clause, filtering groups
7. **JOINS**: INNER, LEFT, RIGHT, multiple JOINs
8. **Subqueries**: WHERE, SELECT, FROM subqueries
9. **CTEs**: WITH clause, multiple CTEs
10. **Common Functions**: String, Date, Math, NULL functions
11. **CASE Expressions**: Conditional logic in queries
12. **DISTINCT**: Unique values

**Quick Reference Table**: Operations and syntax at a glance
**Execution Order**: FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT

**Use When**:
- Writing basic queries
- Remembering syntax for specific operations
- Understanding query execution order
- Quick lookup for function signatures

---

### [Window Functions](cheatsheets/window-functions.md)
**Complete guide** to analytical window functions.

**Sections**:
1. **Ranking Functions**: ROW_NUMBER, RANK, DENSE_RANK, NTILE
2. **Analytical Functions**: LAG, LEAD, FIRST_VALUE, LAST_VALUE
3. **Aggregate Functions**: SUM, AVG, COUNT as window functions
4. **PARTITION BY**: Grouping without collapsing rows
5. **Frame Clauses**: ROWS/RANGE, boundary specifications
6. **Common Patterns**:
   - Top N per group
   - Moving averages
   - Year-over-year comparisons
   - Cumulative percentages
   - Gap and island problems
7. **Performance Tips**: WINDOW clause, indexing strategies
8. **Common Mistakes**: LAST_VALUE frames, WHERE clause limitations

**Comparison Tables**:
- ROW_NUMBER vs RANK vs DENSE_RANK with examples
- When to use GROUP BY vs Window Functions

**Use When**:
- Implementing analytics queries
- Calculating running totals or moving averages
- Ranking within groups
- Comparing with previous/next periods
- Debugging window function behavior

---

### [Query Optimization](cheatsheets/optimization.md)
**Practical guide** to analyzing and improving query performance.

**Sections**:
1. **EXPLAIN**: Query plan analysis, ANALYZE option, output formats
2. **Understanding Plans**: Scan methods, join algorithms, cost interpretation
3. **Indexes**:
   - B-Tree (default, composite, order matters)
   - Unique indexes
   - Partial indexes (WHERE clause)
   - Expression indexes (computed values)
   - Covering indexes (INCLUDE)
4. **Index Usage**:
   - Good candidates (WHERE, JOIN, ORDER BY columns)
   - Poor candidates (low cardinality, small tables)
5. **Optimization Techniques**:
   - SELECT only needed columns
   - Filter early (push WHERE down)
   - Avoid DISTINCT when possible
   - EXISTS vs IN comparisons
   - JOIN vs Subquery tradeoffs
6. **Common Anti-Patterns**:
   - Implicit type conversion
   - OR with different columns
   - NOT IN with NULLs
   - Leading wildcards in LIKE
7. **Monitoring**: Finding slow queries, missing indexes, unused indexes
8. **Maintenance**: REINDEX, ANALYZE, index bloat

**Optimization Checklist**: Step-by-step workflow
**Quick Reference Table**: Techniques and when to use them

**Use When**:
- Query is slow in production
- Deciding which indexes to create
- Understanding EXPLAIN output
- Comparing optimization approaches
- Regular performance audits

---

## 🎯 How to Use These Assets

### During Learning
1. **Start with Cheatsheets**: Use [SQL Basics](cheatsheets/sql-basics.md) while working through exercises
2. **Visual Reinforcement**: Reference diagrams when concepts feel abstract
3. **Keep Handy**: Bookmark for quick syntax lookups

### During Problem Solving
1. **Stuck on JOINs?** → [JOIN Diagrams](diagrams/join-types.md)
2. **Need Rankings?** → [Window Functions Cheatsheet](cheatsheets/window-functions.md)
3. **Query Too Slow?** → [Optimization Guide](cheatsheets/optimization.md)

### During Code Review
1. Check optimization cheatsheet for anti-patterns
2. Verify JOIN type choice against visual guide
3. Ensure proper window function usage (frame clauses!)

---

## 📁 File Structure

```
assets/
├── README.md                           # This file
├── diagrams/
│   ├── query-execution-flow.md         # How queries are processed
│   ├── join-types.md                   # Visual JOIN comparison
│   └── window-functions.md             # Window function mechanics
└── cheatsheets/
    ├── sql-basics.md                   # Core SQL reference (12 sections)
    ├── window-functions.md             # Analytical functions guide
    └── optimization.md                 # Performance tuning reference
```

---

## 🔗 Related Resources

### Module Content
- **Theory**: [concepts.md](../theory/concepts.md) - Detailed explanations
- **Exercises**: [exercises/](../exercises/) - Hands-on practice
- **Infrastructure**: [infrastructure/](../infrastructure/) - Database setup

### Workflow
1. **Read** theory concepts
2. **Reference** these assets while learning
3. **Practice** with exercises
4. **Return** to cheatsheets for quick lookup

---

## 💡 Tips for Effective Use

### For Beginners
- Start with [SQL Basics Cheatsheet](cheatsheets/sql-basics.md)
- Use diagrams to understand JOIN behavior before writing complex queries
- Reference execution order when debugging unexpected results

### For Intermediate Users
- Keep [Window Functions Cheatsheet](cheatsheets/window-functions.md) handy for analytics work
- Use [Optimization Guide](cheatsheets/optimization.md) proactively, not just when slow
- Study EXPLAIN output patterns in [Query Execution Flow](diagrams/query-execution-flow.md)

### For Advanced Users
- Review optimization checklist before production deployments
- Use frame specifications guide for complex analytical queries
- Reference anti-patterns section during code reviews

---

## 🎓 Learning Paths

### Path 1: Fundamentals First
1. [SQL Basics Cheatsheet](cheatsheets/sql-basics.md) - Master foundation
2. [JOIN Types Diagram](diagrams/join-types.md) - Understand relationships
3. Practice exercises 01-02 with cheatsheet reference

### Path 2: Analytics Focus
1. [SQL Basics Cheatsheet](cheatsheets/sql-basics.md) - Quick foundation review
2. [Window Functions Diagram](diagrams/window-functions.md) - Visual concepts
3. [Window Functions Cheatsheet](cheatsheets/window-functions.md) - Deep dive
4. Practice exercises 04-05 with cheatsheet reference

### Path 3: Performance Optimization
1. [Query Execution Flow](diagrams/query-execution-flow.md) - How queries work
2. [Optimization Cheatsheet](cheatsheets/optimization.md) - Techniques
3. Practice exercise 06 with EXPLAIN analysis

---

## 📖 Printing Tips

All files are designed to be print-friendly:

- **Cheatsheets**: Print double-sided, keep at desk
- **Diagrams**: Render Mermaid to PNG/SVG before printing
- **Recommended Order**: SQL Basics → Window Functions → Optimization

### Rendering Mermaid Diagrams
```bash
# Using mermaid-cli
npm install -g @mermaid-js/mermaid-cli
mmdc -i diagrams/join-types.md -o join-types.pdf
```

Or use VS Code extension: "Markdown Preview Mermaid Support"

---

## 🤝 Contributing

Found an error or have a suggestion?
1. Check if concept is covered in appropriate file
2. Ensure additions maintain quick-reference format
3. Add visual examples where helpful
4. Keep cheatsheets concise (2-4 pages when printed)

---

## 📊 Asset Coverage Matrix

| Concept | Theory | Diagram | Cheatsheet | Exercises |
|---------|--------|---------|------------|-----------|
| SELECT/WHERE | ✅ | ❌ | ✅ | ✅ (Ex 01) |
| JOINs | ✅ | ✅ | ✅ | ✅ (Ex 02) |
| GROUP BY | ✅ | ❌ | ✅ | ✅ (Ex 03) |
| Window Functions | ✅ | ✅ | ✅ | ✅ (Ex 04) |
| CTEs | ✅ | ❌ | ✅ | ✅ (Ex 05) |
| Optimization | ✅ | ✅ | ✅ | ✅ (Ex 06) |

**Legend**: ✅ Available | ❌ Not needed

---

## 🔍 Quick Lookups

**Need syntax for...**
- Basic queries → [SQL Basics](cheatsheets/sql-basics.md) sections 1-5
- JOINs → [SQL Basics](cheatsheets/sql-basics.md) section 7 or [JOIN Diagram](diagrams/join-types.md)
- Window functions → [Window Functions Cheatsheet](cheatsheets/window-functions.md)
- Performance → [Optimization Cheatsheet](cheatsheets/optimization.md)

**Confused about...**
- JOIN results → [JOIN Visual Guide](diagrams/join-types.md)
- Window function behavior → [Window Functions Diagram](diagrams/window-functions.md)
- Query slowness → [Query Execution Flow](diagrams/query-execution-flow.md)

**Need examples of...**
- Common patterns → All cheatsheets have extensive examples
- Anti-patterns → [Optimization Cheatsheet](cheatsheets/optimization.md) section 6

---

*These assets are designed to be referenced frequently. Bookmark this README and the cheatsheets in your browser or IDE for instant access during development.*
