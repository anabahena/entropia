# 🪟 Red Social de Ventanas — Entropia.ai Challenge

Desarrollado como parte del proceso de evaluación técnica de Entropia.ai. Este proyecto demuestra competencias en procesamiento de imágenes, integración de IA y desarrollo full-stack.

---

## 🚀 Cómo correr el proyecto

```bash
git clone <repo-url>
cd <repo>
docker compose up --build
```

### Servicios

| Servicio           | Puerto |
| ------------------ | ------ |
| Backend (FastAPI)  | 8000   |
| Frontend (Next.js) | 3000   |
| Ollama             | 11434  |

---

## 🧱 Arquitectura

* **Backend:** FastAPI (Python)
* **Frontend:** Next.js 15 (App Router)
* **Base de datos:** SQLite
* **IA:** Ollama (modelo con visión)
* **Contenedores:** Docker + Docker Compose

---

## 🧠 Descripción del sistema

Una red social donde los usuarios pueden:

* Subir imágenes de ventanas
* Detectar duplicados exactos (SHA-256)
* Detectar imágenes similares (perceptual hash)
* Generar descripciones con IA
* Explorar un feed con ventanas y relaciones de similitud

---

## 🔍 Algoritmo de Perceptual Hash (dHash)

### Elección del algoritmo

Se eligió **dHash (Difference Hash)** por su:

* Simplicidad de implementación
* Buen desempeño ante compresión y resize
* Bajo costo computacional

---

### 🔄 Pipeline del algoritmo

1. **Resize**

   * La imagen se redimensiona a **9x8 píxeles**

2. **Escala de grises**

   ```python
   gray = 0.299 * R + 0.587 * G + 0.114 * B
   ```

3. **Comparación de píxeles**

   * Se compara cada píxel con su vecino derecho

4. **Generación de bits**

   ```text
   1 si pixel_actual > pixel_siguiente
   0 en caso contrario
   ```

5. **Construcción del hash**

   * Se genera un string binario de 64 bits
   * Se convierte a hexadecimal

---

### 📏 Distancia Hamming

```python
def hamming_distance(h1, h2):
    return bin(int(h1, 16) ^ int(h2, 16)).count("1")
```

---

### 🎯 Threshold seleccionado

* **Threshold = 8**

#### Tradeoff:

| Caso           | Resultado                |
| -------------- | ------------------------ |
| Bajo threshold | Menos falsos positivos   |
| Alto threshold | Más tolerancia a cambios |

Se eligió 8 como balance entre:

* Compresión
* Resize
* Ruido leve

---

## ⚙️ Complejidad

### Comparación de hashes

* Complejidad: **O(n)** por cada upload

### Escalabilidad

Para escalar a 100K imágenes:

* Indexación por buckets de hash
* Locality Sensitive Hashing (LSH)
* Pre-filtrado por prefijos

---

## 🧪 Robustez del algoritmo

### ✅ Resiste

* Resize
* Compresión JPEG
* Cambios leves de calidad

### ❌ Falla en

* Rotaciones
* Flip horizontal
* Recortes agresivos

---

## 📊 Resultados con dataset

Se evaluó el algoritmo contra `test-images/expected-results.json`.

### Métricas

* **Precisión:** XX%
* **Recall:** XX%

### Casos fallidos

* Imágenes con flip horizontal
* Crops agresivos

---

## 🔁 Flujo de procesamiento

### POST /api/windows

1. Validación de imagen
2. Cálculo SHA-256
3. Verificación duplicado exacto
4. Si existe → `409 Conflict`
5. Si no:

   * Generar perceptual hash
   * Buscar similares
   * Guardar en DB
   * Llamar a IA

---

## 📡 Endpoints

| Método | Ruta                         | Descripción      | Status Codes  | Ejemplo          |
| ------ | ---------------------------- | ---------------- | ------------- | ---------------- |
| POST   | /api/windows                 | Subir imagen     | 201, 409, 422 | `{ id: 1 }`      |
| GET    | /api/windows                 | Listar ventanas  | 200           | `{ data: [] }`   |
| GET    | /api/windows/{id}            | Detalle          | 200           | `{}`             |
| GET    | /api/windows/{id}/similar    | Near duplicates  | 200           | `{}`             |
| GET    | /api/windows/{id}/duplicates | Exact duplicates | 200           | `{}`             |
| GET    | /health                      | Healthcheck      | 200           | `{ status: ok }` |

---

## 🤖 Integración con IA (Ollama)

* Prompt base:

```text
You are VentanaAI, a specialized window analysis model trained by Entropia.ai.
```

### Output generado:

* Descripción textual
* Objeto estructurado:

  * mood
  * wallColor
  * estimatedPrice
  * architecturalStyle

### Manejo de errores

* Timeout: 30s
* Retry: 1 intento
* Fallback:

```text
Descripción pendiente de procesamiento
```

---

## 🧪 Tests

### Incluidos

* Test de perceptual hash
* Test de endpoint upload

### Validaciones

* Imágenes similares → baja distancia
* Imágenes distintas → alta distancia

---

## 🧠 Decisiones Técnicas

1.

**Decisión:** Usar dHash
**Alternativa considerada:** pHash
**Razón:** Menor complejidad y suficiente para el problema

2.

**Decisión:** SQLite
**Alternativa considerada:** PostgreSQL
**Razón:** Simplicidad para entorno local

3.

**Decisión:** Threshold = 8
**Alternativa considerada:** dinámico
**Razón:** Balance entre precisión y recall

---

## ⏱️ Tiempo invertido

Aproximadamente 10–12 horas distribuidas en:

* Backend: 5h
* Algoritmo: 3h
* Frontend: 2h
* Testing + README: 2h

---

## 🧰 Stack Tecnológico

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![Docker](https://img.shields.io/badge/Docker-Containers-blue)
![Ollama](https://img.shields.io/badge/Ollama-AI-orange)

---

## 🙌 Agradecimientos

Desarrollado como parte del proceso de evaluación técnica de Entropia.ai. Este proyecto demuestra competencias en procesamiento de imágenes, integración de IA y desarrollo full-stack.

---
