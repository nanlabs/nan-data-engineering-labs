# Flujo de Trabajo de Terraform

## Diagrama del Ciclo de Vida de Terraform

```mermaid
flowchart TD
    Start([Inicio]) --> Write[Escribir Configuration .tf]
    Write --> Init[terraform init]
    Init --> InitDesc[Descarga Providers<br/>Inicializa Backend<br/>Configure Modules]
    InitDesc --> Validate[terraform validate]
    Validate --> ValidDesc{¿Sintaxis<br/>Correcta?}
    ValidDesc -->|No| Fix[Corregir Errores]
    Fix --> Write
    ValidDesc -->|Sí| Format[terraform fmt]
    Format --> Plan[terraform plan]
    Plan --> PlanDesc[Genera Plan de Ejecución<br/>Muestra Cambios]
    PlanDesc --> Review{¿Revisar<br/>Cambios?}
    Review -->|Modificar| Write
    Review -->|Aprobar| Apply[terraform apply]
    Apply --> ApplyDesc[Create/Modifica<br/>Recursos]
    ApplyDesc --> State[(State File<br/>terraform.tfstate)]
    State --> Monitor[Monitorear Recursos]
    Monitor --> Change{¿Requiere<br/>Cambios?}
    Change -->|Sí| Write
    Change -->|No| Maintain[Mantener]
    Maintain --> Destroy{¿Eliminar<br/>Infraestructura?}
    Destroy -->|Sí| DestroyCmd[terraform destroy]
    DestroyCmd --> End([Fin])
    Destroy -->|No| Monitor

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Apply fill:#FFD700
    style State fill:#87CEEB
    style DestroyCmd fill:#FF6347
```

## Comandos Principales

```mermaid
graph LR
    subgraph "Inicialización"
        A[terraform init] --> B[terraform validate]
        B --> C[terraform fmt]
    end

    subgraph "Planificación"
        C --> D[terraform plan]
        D --> E[terraform plan -out=plan.tfplan]
    end

    subgraph "Aplicación"
        E --> F[terraform apply]
        F --> G[terraform apply plan.tfplan]
    end

    subgraph "Gestión"
        G --> H[terraform show]
        H --> I[terraform state list]
        I --> J[terraform output]
    end

    subgraph "Limpieza"
        J --> K[terraform destroy]
    end

    style A fill:#E1F5FF
    style D fill:#FFF4E1
    style F fill:#FFE1E1
    style K fill:#FFB6C1
```

## Gestión de Workspaces

```mermaid
flowchart LR
    Start([Proyecto Terraform]) --> Default[workspace: default]
    Default --> Create1[terraform workspace new dev]
    Default --> Create2[terraform workspace new staging]
    Default --> Create3[terraform workspace new prod]

    Create1 --> Dev[Workspace: dev]
    Create2 --> Staging[Workspace: staging]
    Create3 --> Prod[Workspace: prod]

    Dev --> StateDev[(State: dev)]
    Staging --> StateStaging[(State: staging)]
    Prod --> StateProd[(State: prod)]

    Dev --> Switch1[terraform workspace select]
    Staging --> Switch1
    Prod --> Switch1

    Switch1 --> List[terraform workspace list]
    List --> Show[terraform workspace show]

    style Dev fill:#E8F5E9
    style Staging fill:#FFF3E0
    style Prod fill:#FFEBEE
    style StateDev fill:#C8E6C9
    style StateStaging fill:#FFE0B2
    style StateProd fill:#FFCDD2
```

## Flujo de Trabajo en Equipo

```mermaid
sequenceDiagram
    participant Dev as Desarrollador
    participant Git as Git Repository
    participant CI as CI/CD Pipeline
    participant S3 as S3 Backend
    participant AWS as AWS

    Dev->>Git: 1. Commit cambios .tf
    Git->>CI: 2. Trigger pipeline
    CI->>CI: 3. terraform init
    CI->>S3: 4. Obtener state lock
    S3-->>CI: 5. Lock adquirido
    CI->>CI: 6. terraform validate
    CI->>CI: 7. terraform plan
    CI->>Dev: 8. Mostrar plan
    Dev->>CI: 9. Aprobar cambios
    CI->>CI: 10. terraform apply
    CI->>AWS: 11. Crear/Modificar recursos
    AWS-->>CI: 12. Recursos actualizados
    CI->>S3: 13. Actualizar state
    CI->>S3: 14. Liberar lock
    S3-->>CI: 15. Lock liberado
    CI->>Dev: 16. Deployment exitoso

    Note over S3: State Locking previene<br/>conflictos concurrentes
    Note over AWS: Recursos de infraestructura<br/>gestionados por Terraform
```

## Best Practices Flow

```mermaid
flowchart TD
    A[Código Terraform] --> B{Pre-commit Hooks}
    B --> C[terraform fmt]
    B --> D[terraform validate]
    B --> E[tflint]
    B --> F[tfsec]

    C --> G{¿Formato OK?}
    D --> H{¿Validation OK?}
    E --> I{¿Lint OK?}
    F --> J{¿Seguridad OK?}

    G -->|No| Fix1[Corregir Formato]
    H -->|No| Fix2[Corregir Sintaxis]
    I -->|No| Fix3[Corregir Lint]
    J -->|No| Fix4[Corregir Seguridad]

    Fix1 --> A
    Fix2 --> A
    Fix3 --> A
    Fix4 --> A

    G -->|Sí| K[Commit]
    H -->|Sí| K
    I -->|Sí| K
    J -->|Sí| K

    K --> L[Push to Branch]
    L --> M[Pull Request]
    M --> N[Code Review]
    N --> O{¿Aprobado?}
    O -->|No| P[Solicitar Cambios]
    P --> A
    O -->|Sí| Q[Merge to Main]
    Q --> R[CI/CD Pipeline]
    R --> S[terraform plan]
    S --> T{¿Plan OK?}
    T -->|No| U[Rollback]
    T -->|Sí| V[terraform apply]
    V --> W[Actualizar Docs]
    W --> X[Notificar Equipo]

    style K fill:#90EE90
    style Q fill:#FFD700
    style V fill:#87CEEB
    style U fill:#FF6347
```

## Uso

Estos diagramas muestran:
1. El ciclo de vida completo de Terraform
2. Los comandos principales y su secuencia
3. Gestión de múltiples workspaces
4. Flujo de trabajo colaborativo con state locking
5. Best practices y validaciones pre-commit

Para visualizar estos diagramas en VS Code, instala la extensión "Markdown Preview Mermaid Support".
