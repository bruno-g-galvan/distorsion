# Revisión automática diaria

Instrucciones para la tarea programada que revisa la agenda todos los días.
Se pueden editar: la próxima revisión sigue lo que diga este archivo.

## Objetivo

Que cada show próximo de `data/agenda.json` refleje lo que dicen hoy sus fuentes
(fecha, horario, lugar, line-up, precio, estado de las entradas) y sumar como
borrador los shows de metal nuevos que se anuncien en Argentina.

## Reglas que no se rompen

1. **Solo hechos que leíste hoy en una página que abriste.** Nada de memoria ni
   de suposiciones. Un dato sin fuente abierta hoy no entra.
2. **Nunca publicar ni despublicar, nunca borrar, nunca tocar** el nivel de
   verificación, el destacado, flyers, fotos ni descripciones. La herramienta
   `tools/actualizar.py` ya lo impide; no edites `agenda.json` a mano.
3. **Shows nuevos: siempre como borrador**, con fuente y nota interna.
4. **Cambios de fecha o de lugar y cancelaciones en un show publicado**: solo con
   una fuente oficial (la banda, la productora, el lugar o la ticketera) o con dos
   medios independientes que lo digan. Si no, no lo cambies: dejá una
   `nota_interna` explicando qué viste y dónde.
5. **Ante la duda, nota interna.** Es mejor avisarle al editor que cambiar algo mal.
6. No toques nada fuera de `data/` y `reports/`.

## Pasos

1. Sumá el repositorio a la sesión con `add_repo` (owner `bruno-g-galvan`, repo
   `distorsion`, acceso `push`) y clonalo como indique la herramienta.
2. Dentro del repo: `python3 tools/actualizar.py listar`. Te devuelve los shows
   próximos con su `id`, datos, fuentes y nota interna.
3. Revisá cada show, en este orden: los publicados, después los borradores de los
   próximos 45 días, después el resto. Usá WebSearch y WebFetch (la terminal no
   llega a la web). Buscá primero en las fuentes que ya tiene el show, después en
   las cuentas oficiales, la página de la ticketera y medios (Indie Hoy, Rolling
   Stone, Ámbito, etc.).
   - Si algo cambió y está confirmado: va en `actualizar` con `campos` y `fuentes`.
   - Si está igual y lo confirmaste: va en `actualizar` con `fuentes` y `"revisado": true`.
   - Si un borrador quedó confirmado por una fuente mejor, o hay algo para que el
     editor revise: `nota_interna` (reemplaza la anterior, así que escribila
     completa).
   - Estados de entradas: `anunciado`, `venta`, `ultimas`, `agotado`, `gratis`,
     `puerta`, `reprogramado`, `cancelado`.
4. Buscá shows nuevos de metal en Argentina en los próximos 6 meses: la lista de
   metal de Buenos Aires en Songkick, las agendas de Indie Hoy por lugar (Uniclub,
   El Teatrito, El Teatro Flores, Club Cultural Bula, Groove, C Art Media), el
   Movistar Arena, y bandas argentinas (Rata Blanca, Almafuerte, Horcas, Malón,
   Carajo, Hermética y sus derivados, Lethal, Avernal, Nvlo y otras de la escena).
   Cada uno va en `nuevos` con al menos una fuente. Indicá en `nota_interna` si
   salió solo de un agregador.
5. Escribí `cambios.json` fuera del repo (en tu carpeta temporal) con el formato
   que explica `tools/actualizar.py`, e incluí un `resumen` de una o dos frases.
6. `python3 tools/actualizar.py aplicar <ruta>/cambios.json --prueba`. Si da error,
   corregí y repetí. Después corrélo sin `--prueba`.
7. Guardá y subí:
   ```
   git add data/agenda.json reports/
   git commit -m "Revisión automática DD/MM: N actualizados, M nuevos"
   git push origin main
   ```
   Si el push es rechazado porque alguien publicó desde el editor mientras tanto:
   `git fetch origin main && git reset --hard FETCH_HEAD`, volvé a correr el paso 6
   sin `--prueba`, y repetí el commit y el push.
   Si no hubo ningún cambio ni show nuevo, igual subí el informe del día.
8. Terminá con un resumen corto: cuántos shows revisaste, qué cambió en los
   publicados (eso ya está en el sitio), cuántos borradores nuevos hay para revisar
   y qué necesita atención del editor.
