# Distorsión

La agenda de shows de metal en Argentina. Cada fecha verificada, cada cambio a la vista.

Sitio estático publicado con GitHub Pages: no hay servidor ni base de datos. Todo vive en este repositorio.

## Qué hay en el repo

| Archivo | Para qué sirve |
| --- | --- |
| `index.html` | El sitio completo: agenda, páginas de shows, bandas y lugares, el símbolo 3D, el formulario "Sumá tu show" y el editor. |
| `data/agenda.json` | Los datos: shows, bandas, lugares y ajustes del sitio. |
| `img/` | Flyers y fotos, comprimidos a WebP o JPG desde el editor. |
| `favicon.svg` | El ícono de la pestaña. |
| `.nojekyll` | Le dice a GitHub Pages que publique los archivos tal cual. |

## Cómo cargar y editar shows

1. Creá un token en GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
   - Repository access: **Only select repositories** → este repo.
   - Permissions → Repository permissions → **Contents: Read and write**.
2. Entrá al sitio agregando `#editor` al final de la dirección (por ejemplo `https://bruno-g-galvan.github.io/distorsion/#editor`).
3. Pegá el token. Si marcás "Recordarme", queda guardado solo en ese navegador.
4. Cargá o editá shows, bandas y lugares. Cuando termines, tocá **Publicar cambios**: el editor hace un commit en este repo con los datos y las imágenes nuevas.
5. GitHub Pages tarda alrededor de un minuto en mostrar la versión nueva.

El token nunca se sube al repo ni sale de tu navegador, salvo hacia la API de GitHub.

## Revisión automática diaria

Todos los días, una tarea programada de Claude revisa los shows próximos contra sus fuentes, actualiza lo que cambió y suma como borrador los shows nuevos que encuentra. Sube los cambios a este repo, y GitHub Pages los publica.

- Las reglas están en [`tools/REVISION.md`](tools/REVISION.md). Si las editás, la próxima revisión sigue la versión nueva.
- Los cambios pasan por [`tools/actualizar.py`](tools/actualizar.py), que no deja publicar, despublicar ni borrar shows, ni tocar flyers, fotos, descripciones o niveles de verificación.
- En los shows publicados, cada cambio de fecha, horario, lugar, estado, line-up o precio queda en el historial público del show.
- El informe de cada día queda en `reports/AAAA-MM-DD.md`.
- Si publicás desde el editor mientras corre la revisión, tus cambios se combinan con los suyos en vez de pisarse.

## Publicar con GitHub Pages

En el repo: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, rama `main`, carpeta `/ (root)`.

Para usar un dominio propio, cargalo en esa misma pantalla (Custom domain) y apuntá el DNS a GitHub Pages.
