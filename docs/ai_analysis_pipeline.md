# Pipeline automático de análisis IA

El pipeline es síncrono: después de confirmar un artículo, el sistema intenta ejecutar el proveedor mock y persiste el resultado. Una falla de IA no revierte la creación ni la actualización del artículo.

Las rutas reciben `AutomaticAnalysisResult`, un resultado serializable y seguro que no expone trazas ni mensajes internos del proveedor. Mientras el proceso sea síncrono, puede aumentar el tiempo de respuesta. Un sprint futuro deberá mover esta coordinación a una cola asíncrona.
