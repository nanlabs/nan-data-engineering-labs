#!/bin/bash
# Validación completa de todos los ejercicios

echo "🧪 Ejecutando validación completa..."
echo ""

# Verificar pytest
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest no instalado. Ejecuta: pip install pytest"
    exit 1
fi

# Ir al directorio de validación
cd "$(dirname "$0")/../validation" || exit

# Ejecutar tests con opciones verbose
pytest -v \
    --tb=short \
    --maxfail=5 \
    --color=yes \
    .

# Capturar exit code
EXIT_CODE=$?

echo ""
echo "=" * 60

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ TODOS LOS TESTS PASARON"
    echo "=" * 60
    echo ""
    echo "🎉 Felicitaciones! Has completado el Módulo 05"
    echo ""
    echo "📊 Próximos pasos sugeridos:"
    echo "   • Revisar assets/optimization-checklist.md"
    echo "   • Comparar Delta vs Iceberg en assets/iceberg-comparison.md"
    echo "   • Explorar casos de uso reales en theory/03-use-cases.md"
else
    echo "⚠️  ALGUNOS TESTS FALLARON"
    echo "=" * 60
    echo ""
    echo "💡 Tips para debugging:"
    echo "   • Ver logs detallados: pytest -vv"
    echo "   • Ejecutar test específico: pytest validation/test_01_delta_basics.py::test_create_delta_table"
    echo "   • Verificar servicios: docker-compose ps"
    echo "   • Ver logs de Spark: docker logs spark-master"
fi

echo ""
exit $EXIT_CODE
