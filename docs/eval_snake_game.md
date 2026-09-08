# Evaluación manual: Snake en pygame (NL vs SCL)

Protocolo para comparar un prompt en lenguaje natural contra su
equivalente en SCL, usando dos sesiones aisladas (sin memoria
compartida entre ellas) para no contaminar la comparación.

Importante: los dos prompts de abajo llevan **la misma información**
(mismas restricciones), solo cambia el formato. Esto aísla el efecto
de SCL como formato — no mide "prompt detallado vs. prompt vago", que
es una comparación distinta y menos interesante.

## Prompt A — Lenguaje natural

```
Escribime un script de Python que implemente el juego de la viborita
(snake) usando pygame, en un solo archivo, usando solo la librería
pygame como dependencia externa. Controles con las flechas del
teclado, sin permitir que la serpiente revierta 180° sobre sí misma.
El juego termina si la serpiente choca contra una pared o contra su
propio cuerpo. La comida debe reaparecer en una posición aleatoria
cada vez que se come, haciendo crecer a la serpiente. Mostrá el
puntaje en pantalla en todo momento. Al terminar el juego, mostrá una
pantalla de "Game Over" con el puntaje final, y permití reiniciar la
partida presionando la tecla R. La velocidad debe ser fija y jugable
(usá el reloj de pygame para controlar el framerate).
```

## Prompt B — SCL

```
gen_code | in:spec | out:pygame_snake_script | constraint:single_file,pygame_only,arrow_key_controls,no_180_reversal,wall_collision_ends_game,self_collision_ends_game,food_random_respawn,score_display,game_over_screen,restart_on_r_key,fixed_speed | fmt:python_script
```

(Es una instancia válida de `SCLObject` — se puede reconstruir con
`SCLObject.model_validate({"action": ["gen_code"], "in": ["spec"], "out": ["pygame_snake_script"], "constraint": [...], "fmt": "python_script"})`
y volver a serializar con `scl.serializer.serialize` para confirmarlo.)

## Cómo correr el experimento

1. Sesión 1: pegar Prompt A solo, sin contexto adicional.
2. Sesión 2 (nueva, sin memoria de la sesión 1): pegar Prompt B solo.
   Si el modelo no conoce la sintaxis SCL, agregar antes una línea
   explicando el formato (`ACTION | in:X | out:Y | constraint:Z | fmt:W`)
   — pero sin agregar información nueva sobre el juego en sí.
3. Guardar el código resultante de cada sesión tal cual, sin editarlo.
4. Ejecutar cada script por separado y completar el checklist de abajo,
   a ciegas (evaluar los dos antes de decidir cuál "se ve mejor").

## Checklist de comportamiento (13 ítems, Sí/No)

**Ejecución**
1. Corre sin excepciones no capturadas durante al menos 30s de juego manual.
2. Es un único archivo ejecutable (`python snake.py`), sin módulos propios adicionales.
3. La única dependencia externa importada es `pygame`.

**Mecánica core**
4. La serpiente se mueve sola de forma continua (no requiere mantener la tecla presionada).
5. Las flechas cambian la dirección; un giro de 180° instantáneo se ignora (no mata ni revierte la serpiente).
6. Aparece comida en una posición aleatoria dentro del área jugable.
7. Al comer, la serpiente crece un segmento y aparece nueva comida en otra posición aleatoria.
8. El puntaje se muestra en pantalla y se actualiza al comer.

**Fin del juego**
9. Chocar contra una pared termina la partida.
10. Chocar contra el propio cuerpo termina la partida.
11. Al terminar, se muestra una pantalla de "Game Over" con el puntaje final.
12. Presionar R reinicia la partida sin cerrar la ventana.

**Calidad de juego**
13. La velocidad es fija y jugable (usa `clock.tick(...)` o equivalente, no es ilegible ni tediosa).

**Puntaje de completitud funcional:** `items_cumplidos / 13`.

## Otras métricas a registrar

- **Tokens del prompt** (Prompt A vs Prompt B) — con un tokenizer
  (tiktoken, o el conteo que reporta Ollama/la API). Como ambos llevan
  la misma información, esta es la comparación de "ahorro neto" real.
- **Turnos hasta versión utilizable** — si el primer intento no corre o
  falla el checklist, cuántas correcciones hicieron falta hasta pasar
  el checklist completo. Esto es el proxy de "costo de ambigüedad" que
  el conteo de tokens del prompt inicial no captura.
- **Tokens de la respuesta completa** (opcional) — si además querés
  medir si un prompt más estructurado produce respuestas más
  concisas (menos explicación innecesaria alrededor del código).

## Nota sobre round-trip / fidelidad semántica

La métrica de "round-trip NL→SCL→NL' comparado por similitud" (pensada
originalmente para tareas de texto como resumen o extracción) no
aplica bien acá: no hay un "NL' " natural que comparar por similitud
de texto cuando la salida es código. El checklist de arriba es el
reemplazo correcto para tareas de generación: mide si la intención se
preservó, en términos de comportamiento verificable, en vez de
similitud textual.

## Variante opcional: NL vago (ambigüedad real)

Si además querés medir qué pasa con la forma en que la gente escribe
prompts en la práctica (sin enumerar todas las restricciones), corré
una tercera sesión con:

```
Hazme el juego de la viborita (snake) en Python usando pygame.
```

y puntuala con el mismo checklist. La brecha entre esta sesión y el
Prompt A/B de arriba mide cuánto se pierde por dejar restricciones
implícitas — que es la motivación original de SCL — separada de la
brecha entre A y B, que mide el efecto del formato en sí.
