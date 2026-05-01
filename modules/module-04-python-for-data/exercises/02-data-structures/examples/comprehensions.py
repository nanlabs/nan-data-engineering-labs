"""
Ejemplos Avanzados: Comprehensions en Python

Este archivo muestra patrones avanzados de list/dict/set comprehensions
que son comunes en ingeniería de datos.
"""

# =============================================================================
# 1. LIST COMPREHENSIONS AVANZADAS
# =============================================================================

print("=" * 70)
print("LIST COMPREHENSIONS AVANZADAS")
print("=" * 70)

# Comprehension con múltiples condiciones
print("\n1. Filtrado con múltiples condiciones:")
numeros = range(30)
multiplos_3_y_5 = [n for n in numeros if n % 3 == 0 and n % 5 == 0]
print(f"Múltiplos de 3 Y 5: {multiplos_3_y_5}")

multiplos_3_o_5 = [n for n in numeros if n % 3 == 0 or n % 5 == 0]
print(f"Múltiplos de 3 O 5: {multiplos_3_o_5}")

# Comprehension anidada (flatten)
print("\n2. Flatten con comprehension anidada:")
matriz = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
aplanada = [elemento for fila in matriz for elemento in fila]
print(f"Matriz: {matriz}")
print(f"Aplanada: {aplanada}")

# Comprehension con if-else (ternario)
print("\n3. Transformación condicional:")
numeros = [1, 2, 3, 4, 5]
resultado = ["par" if n % 2 == 0 else "impar" for n in numeros]
print(f"Números: {numeros}")
print(f"Clasificación: {resultado}")

# Comprehension para crear pares (tuplas)
print("\n4. Crear pares (producto cartesiano):")
letras = ['A', 'B', 'C']
numeros = [1, 2, 3]
pares = [(letra, numero) for letra in letras for numero in numeros]
print(f"Letras: {letras}, Números: {numeros}")
print(f"Combinaciones: {pares}")

# Comprehension con función aplicada
print("\n5. Aplicar función a cada elemento:")
palabras = ["hola", "mundo", "python"]
longitudes = [len(palabra) for palabra in palabras]
mayusculas = [palabra.upper() for palabra in palabras]
print(f"Palabras: {palabras}")
print(f"Longitudes: {longitudes}")
print(f"Mayúsculas: {mayusculas}")

# Comprehension con enumerate
print("\n6. Comprehension con enumerate:")
palabras = ["python", "es", "genial"]
indexadas = [f"{i}: {palabra}" for i, palabra in enumerate(palabras)]
print(f"Palabras indexadas: {indexadas}")

# =============================================================================
# 2. DICT COMPREHENSIONS AVANZADAS
# =============================================================================

print("\n" + "=" * 70)
print("DICT COMPREHENSIONS AVANZADAS")
print("=" * 70)

# Crear diccionario desde dos listas
print("\n1. Combinar dos listas en dict:")
claves = ["a", "b", "c"]
valores = [1, 2, 3]
diccionario = {k: v for k, v in zip(claves, valores)}
print(f"Claves: {claves}, Valores: {valores}")
print(f"Diccionario: {diccionario}")

# Filtrar diccionario por valor
print("\n2. Filtrar diccionario por condición:")
ventas = {"enero": 100, "febrero": 150, "marzo": 80, "abril": 200}
ventas_altas = {mes: valor for mes, valor in ventas.items() if valor >= 100}
print(f"Ventas: {ventas}")
print(f"Ventas >= 100: {ventas_altas}")

# Transformar valores de diccionario
print("\n3. Transformar valores:")
precios = {"laptop": 1000, "mouse": 20, "teclado": 50}
precios_iva = {producto: precio * 1.21 for producto, precio in precios.items()}
print(f"Precios: {precios}")
print(f"Precios con IVA (21%): {precios_iva}")

# Crear diccionario de frecuencias
print("\n4. Diccionario de frecuencias:")
palabras = ["python", "es", "genial", "python", "es", "python"]
frecuencias = {palabra: palabras.count(palabra) for palabra in set(palabras)}
print(f"Palabras: {palabras}")
print(f"Frecuencias: {frecuencias}")

# Invertir diccionario anidado
print("\n5. Diccionario anidado:")
usuarios = [
    {"nombre": "Ana", "edad": 25},
    {"nombre": "Luis", "edad": 30},
    {"nombre": "María", "edad": 28}
]
por_nombre = {user["nombre"]: user["edad"] for user in usuarios}
print(f"Usuarios: {usuarios}")
print(f"Por nombre: {por_nombre}")

# =============================================================================
# 3. SET COMPREHENSIONS AVANZADAS
# =============================================================================

print("\n" + "=" * 70)
print("SET COMPREHENSIONS AVANZADAS")
print("=" * 70)

# Eliminar duplicados con transformación
print("\n1. Eliminar duplicados con transformación:")
palabras = ["Hola", "hola", "HOLA", "Mundo", "mundo"]
palabras_unicas = {palabra.lower() for palabra in palabras}
print(f"Palabras: {palabras}")
print(f"Únicas (lowercase): {palabras_unicas}")

# Encontrar elementos comunes
print("\n2. Elementos comunes entre listas:")
lista1 = [1, 2, 3, 4, 5]
lista2 = [4, 5, 6, 7, 8]
comunes = {x for x in lista1 if x in lista2}
print(f"Lista 1: {lista1}")
print(f"Lista 2: {lista2}")
print(f"Comunes: {comunes}")

# Extraer caracteres únicos
print("\n3. Caracteres únicos en texto:")
texto = "mississippi"
caracteres_unicos = {char for char in texto}
print(f"Texto: '{texto}'")
print(f"Caracteres únicos: {caracteres_unicos}")

# =============================================================================
# 4. PATRONES COMBINADOS (Real-world)
# =============================================================================

print("\n" + "=" * 70)
print("PATRONES COMBINADOS - CASOS REALES")
print("=" * 70)

# Caso 1: Procesamiento de datos de ventas
print("\n1. Pipeline de ventas:")
ventas_raw = [
    {"producto": "Laptop", "cantidad": 2, "precio": 1000},
    {"producto": "Mouse", "cantidad": 5, "precio": 20},
    {"producto": "Teclado", "cantidad": 3, "precio": 50},
]

# Calcular totales
totales = {venta["producto"]: venta["cantidad"] * venta["precio"] 
           for venta in ventas_raw}
print(f"Totales por producto: {totales}")

# Productos con venta > 100
productos_exitosos = {venta["producto"] 
                      for venta in ventas_raw 
                      if venta["cantidad"] * venta["precio"] > 100}
print(f"Productos con venta > 100: {productos_exitosos}")

# Caso 2: Limpieza de datos
print("\n2. Limpieza de datos:")
datos_sucios = ["  Python  ", "java", "JAVASCRIPT", "  ruby", "Python"]
datos_limpios = {dato.strip().lower() for dato in datos_sucios}
print(f"Datos sucios: {datos_sucios}")
print(f"Datos limpios: {datos_limpios}")

# Caso 3: Agrupar por categoría
print("\n3. Agrupar por categoría:")
productos = [
    {"nombre": "Laptop", "categoria": "Computadoras", "precio": 1000},
    {"nombre": "Mouse", "categoria": "Accesorios", "precio": 20},
    {"nombre": "Desktop", "categoria": "Computadoras", "precio": 1500},
    {"nombre": "Teclado", "categoria": "Accesorios", "precio": 50},
]

# Obtener categorías únicas
categorias = {p["categoria"] for p in productos}
print(f"Categorías: {categorias}")

# Productos por categoría
por_categoria = {
    cat: [p["nombre"] for p in productos if p["categoria"] == cat]
    for cat in categorias
}
print(f"Productos por categoría: {por_categoria}")

# Caso 4: Transformación de datos anidados
print("\n4. Transformación de datos anidados:")
usuarios = [
    {"id": 1, "nombre": "Ana", "skills": ["Python", "SQL"]},
    {"id": 2, "nombre": "Luis", "skills": ["Java", "Python", "AWS"]},
    {"id": 3, "nombre": "María", "skills": ["Python", "React"]},
]

# Todos los skills únicos
todos_skills = {skill 
                for usuario in usuarios 
                for skill in usuario["skills"]}
print(f"Skills únicos: {todos_skills}")

# Usuarios por skill
usuarios_python = [u["nombre"] 
                   for u in usuarios 
                   if "Python" in u["skills"]]
print(f"Usuarios con Python: {usuarios_python}")

# Conteo de skills por usuario
skill_counts = {u["nombre"]: len(u["skills"]) for u in usuarios}
print(f"Skills por usuario: {skill_counts}")

# =============================================================================
# 5. COMPREHENSIONS VS LOOPS TRADICIONALES
# =============================================================================

print("\n" + "=" * 70)
print("COMPREHENSIONS VS LOOPS TRADICIONALES")
print("=" * 70)

print("\nEjemplo: Filtrar y transformar")

# Con loop tradicional (más verboso)
print("\n❌ Con loop tradicional:")
numeros = [1, 2, 3, 4, 5]
resultado_loop = []
for n in numeros:
    if n % 2 == 0:
        resultado_loop.append(n ** 2)
print(f"Resultado: {resultado_loop}")

# Con comprehension (más conciso)
print("\n✅ Con comprehension:")
resultado_comp = [n ** 2 for n in numeros if n % 2 == 0]
print(f"Resultado: {resultado_comp}")

print("\n💡 Las comprehensions son:")
print("   • Más concisas")
print("   • Más legibles (una vez que te acostumbras)")
print("   • Generalmente más rápidas")
print("   • Más Pythonic")

print("\n⚠️  Pero usa loops cuando:")
print("   • La lógica es muy compleja")
print("   • Necesitas break/continue")
print("   • La comprehension es muy larga (> 80 caracteres)")

print("\n" + "=" * 70)
print("✅ Ejemplos completados")
print("=" * 70)
