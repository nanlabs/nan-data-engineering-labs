# Hints - Exercise 01: Basic Queries

Do you need help? There are clues here without revealing the full solutions.

## Projection (01_projection.sql)

**Query 1 - Nombre y email**
- 💡 Usa `SELECT column1, column2, column3 FROM table`
- 💡 No necesitas WHERE si quieres todos los registros

**Query 2 - Aliases in Spanish**
- 💡 Sintaxis de alias: `column_name AS alias_name`
- 💡 Los alias pueden tener espacios si usas comillas: `AS "nombre producto"`

**Query 3 - First 5 orders**
- 💡 `LIMIT n` va al final de la query
- 💡 Order first if you need the "firsts" of any specific criteria

**Query 5 - Todas excepto timestamps**
- 💡 No existe `SELECT * EXCEPT` en PostgreSQL
- 💡 You must explicitly list the columns you want

## Filtrado (02_filtering.sql)

**Query 1 - Multiple conditions**
- 💡 Usa `AND` para combinar condiciones que deben cumplirse todas
- 💡 Sintaxis: `WHERE condition1 AND condition2`

**Query 3 - OR vs IN**
- 💡 `WHERE status = 'a' OR status = 'b'` es equivalente a `WHERE status IN ('a', 'b')`
- 💡 `IN`it is more readable with many values

**Query 4 - Negation**
- 💡 `NOT IN ('a', 'b', 'c')`is the clearest way
- 💡 Also valid:`!= 'a' AND != 'b' AND != 'c'`but more verbose

**Query 8 - Booleanos**
- 💡 En PostgreSQL: `WHERE column = TRUE` o `WHERE column = FALSE`
- 💡 Also valid:`WHERE column` o `WHERE NOT column`

## Pattern Matching (03_patterns.sql)

**Query 1 - Email de Gmail**
- 💡 `%` significa "cualquier secuencia de caracteres"
- 💡 Para emails que terminan en gmail.com: `'%@gmail.com'`

**Query 2 - Contiene Laptop**
- 💡 Para "contiene": `'%palabra%'`
- 💡 Para "comienza con": `'palabra%'`
- 💡 Para "termina en": `'%palabra'`

**Query 5 - BETWEEN**
- 💡 `BETWEEN a AND b` es inclusivo (incluye a y b)
- 💡 Equivalente a: `>= a AND <= b`

**Query 6 - Fechas con BETWEEN**
- 💡 Formato de fecha: `'YYYY-MM-DD'`
- 💡 Para todo 2023: desde '2023-01-01' hasta '2023-12-31'

**Query 7 - NULL checks**
- 💡 NO uses `= NULL` o `!= NULL`, no funciona
- 💡 Usa `IS NULL` o `IS NOT NULL`

## Ordenamiento (04_sorting.sql)

**Query 1 - Mayor a menor**
- 💡 `DESC` = descendente (de mayor a menor)
- 💡 `ASC` = ascendente (de menor a mayor)

**Query 4 - Top N**
- 💡 Combina `ORDER BY column DESC` con `LIMIT n`
- 💡 El orden es: WHERE → ORDER BY → LIMIT

**Query 5 - Sort by multiple columns**
- 💡 Sintaxis: `ORDER BY col1 ASC, col2 DESC, col3 ASC`
- 💡 Se ordena primero por col1, luego por col2 (para empates), etc.

**Query 7 - Last N**
- 💡 "Latest" = most recent = descending order by date
- 💡 Do not confuse with the last ones in the table (that would be ORDER BY primary_key DESC)

## Pagination (05_pagination.sql)

**Query 2-3 - OFFSET**
- 💡 `OFFSET n` salta los primeros n registros
- 💡 Page 1: OFFSET 0, Page 2: OFFSET 10, Page 3: OFFSET 20

**Query 8 - Pagination Formula**
- 💡 For page N with size P:`OFFSET = (N - 1) * P`
- 💡 Ejemplos:
  - Page 1: (1-1) * 10 = 0
  - Page 2: (2-1) * 10 = 10
  - Page 4: (4-1) * 15 = 45

**Importante sobre ORDER BY**
- 💡 SIEMPRE usa ORDER BY con LIMIT/OFFSET
- 💡 Sin ORDER BY, el orden es indeterminado y puede cambiar entre queries

## Combination (06_combined.sql)

**Query 1 - Multiple conditions**
- 💡 Recommended order: WHERE → (more restrictions first) → ORDER BY → LIMIT
- 💡 Use parentheses for clarity if you combine AND/OR

**Query 3 - Filtrar y limitar**
- 💡 WHERE se aplica ANTES de ORDER BY y LIMIT
- 💡 Flujo: Filtrar → Ordenar → Limitar

**Query 6 - OR con LIKE**
- 💡 You need parentheses:`WHERE is_available = TRUE AND (condicion1 OR condicion2)`
- 💡 Without parentheses:`AND` tiene precedencia sobre `OR`

**Query BONUS - Query complejo**
- 💡 Construye paso a paso:
  1. Start with the most restrictive condition
  2. Agrega condiciones con AND
  3. Agrega ORDER BY al final
  4. Agrega LIMIT
- 💡 Test each condition individually before combining them

## Tips Generales

### Debugging de Queries
1. Empieza con `SELECT * FROM table` sin WHERE
2. Add one condition at a time
3. Verifica el count: `SELECT COUNT(*) FROM table WHERE ...`
4. Si no retorna nada, verifica que los valores existan en la table

### Performance
- `IN`vs multiple`OR`: usa `IN` para mejor performance
- `BETWEEN` vs `>= AND <=`: usa `BETWEEN` para claridad
- Siempre incluye `ORDER BY` con `LIMIT` para resultados consistentes

### Estilo SQL
- CAPITAL LETTERS for keywords: SELECT, FROM, WHERE
- snake_case para nombres de columns
- Consistent indentation
- Comentarios para queries complejos

### Testing
```bash
# Ver primeras líneas del resultado
psql -h localhost -U dataengineer -d ecommerce -c "SELECT * FROM users LIMIT 5"

# Contar resultados
psql -h localhost -U dataengineer -d ecommerce -c "SELECT COUNT(*) FROM users WHERE country = 'US'"

# Formato vertical para mejor lectura
psql -h localhost -U dataengineer -d ecommerce -c "\x" -c "SELECT * FROM users LIMIT 1"
```

### Common Pitfalls

❌ **Error**: `WHERE column = NULL`
✅ **Correcto**: `WHERE column IS NULL`

❌ **Error**: `LIMIT 10 ORDER BY column`
✅ **Correcto**: `ORDER BY column LIMIT 10`

❌ **Error**: `WHERE country = 'US' OR 'GB'`
✅ **Correcto**: `WHERE country IN ('US', 'GB')`

❌ **Error**: `LIKE 'gmail.com'` (busca exacto)
✅ **Correcto**: `LIKE '%gmail.com'` (busca que termine en)

❌ **Error**: No usar ORDER BY con LIMIT
✅ **Correcto**: Siempre `ORDER BY` antes de `LIMIT`for deterministic results

### Need More Help?

1. query PostgreSQL documentation
2. Revisa los ejemplos en el README.md
3. Usa `\d table_name` en psql para ver la estructura de la table
4. If you are still stuck, see the corresponding solution on`solution/`
