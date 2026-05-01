# Architecture Diagrams for Module 02

This directory contains visual diagrams to help understand storage concepts.

## Available Diagrams

All diagrams are defined in Mermaid format and can be viewed in:
- GitHub (renders Mermaid automatically)
- VS Code (with Mermaid extension)
- [Mermaid Live Editor](https://mermaid.live/)

## Diagram Files

### 1. medallion-architecture.mmd
Visual representation of Bronze → Silver → Gold data lake architecture.

**Shows**:
- Data flow through layers
- Storage formats per layer
- Data quality progression
- Consumer types per layer

**Use in**: Exercise 01, Theory concepts

---

### 2. file-format-decision-tree.mmd
Decision tree for choosing the right file format.

**Helps answer**:
- Which format for my use case?
- CSV vs JSON vs Parquet vs Avro?
- When to use each format?

**Use in**: Exercise 02, Format selection

---

### 3. partitioning-strategies.mmd
Comparison of different partitioning approaches.

**Compares**:
- No partitioning
- Date-based (year/month/day)
- Geography-based (country/region)
- Hybrid (date + geography)

**Use in**: Exercise 03, Partition design

---

### 4. compression-comparison.mmd
Visual comparison of compression algorithms.

**Compares**:
- Snappy (fast, moderate compression)
- Gzip (slow, high compression)
- LZ4 (very fast, lower compression)
- Zstd (balanced, modern)

**Use in**: Exercise 04, Compression selection

---

### 5. schema-evolution-flow.mmd
Workflow for handling schema changes.

**Shows**:
- Adding new columns
- Changing data types
- Backward compatibility
- Forward compatibility

**Use in**: Exercise 05, Schema evolution

---

### 6. glue-catalog-architecture.mmd
AWS Glue Data Catalog architecture.

**Shows**:
- S3 → Glue Crawler → Glue Catalog → Athena
- Table registration
- Partition discovery
- Query flow

**Use in**: Exercise 06, Glue setup

---

### 7. s3-lifecycle-policy.mmd
S3 storage class transitions over time.

**Shows**:
- Standard → Standard-IA → Glacier → Deep Archive
- Cost per GB over time
- Retrieval time comparison

**Use in**: Exercise 01, Lifecycle policies

---

### 8. data-lake-cost-optimization.mmd
Cost optimization strategies visual.

**Shows**:
- Format compression savings
- Lifecycle policy savings
- Partition pruning query cost reduction
- Total cost comparison

**Use in**: All exercises, Cost optimization

---

## How to Use These Diagrams

### In Markdown Documents
```markdown
# My Section
![Medallion Architecture](assets/diagrams/medallion-architecture.mmd)
```

### Render in VS Code
1. Install "Markdown Preview Mermaid Support" extension
2. Open any `.mmd` file
3. Press `Ctrl+Shift+V` (Preview)

### Export as Images
```bash
# Using mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i medallion-architecture.mmd -o medallion-architecture.png

# Generate SVG (better quality)
mmdc -i medallion-architecture.mmd -o medallion-architecture.svg
```

### Edit Diagrams
1. Copy diagram content
2. Open [Mermaid Live Editor](https://mermaid.live/)
3. Paste and edit
4. Copy back to `.mmd` file

---

## Diagram Standards

All diagrams follow these conventions:

- **Nodes**: Rectangular boxes for components
- **Arrows**: Show data flow direction
- **Colors**:
  - Blue: Input/Source
  - Green: Processing/Transformation
  - Yellow: Storage
  - Red: Output/Consumer
- **Labels**: Clear, concise descriptions
- **Layout**: Left-to-right flow (TD for top-down when needed)

---

## Contributing

When adding new diagrams:

1. Use clear, descriptive names
2. Add description in this README
3. Follow existing color scheme
4. Test rendering in GitHub/VS Code
5. Keep diagrams focused (one concept per diagram)

---

**Last Updated**: February 2, 2026
**Module**: 02 - Storage Basics
