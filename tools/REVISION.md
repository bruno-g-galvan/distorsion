# Daily automatic review

Instructions for the scheduled task that reviews the agenda every day.
You can edit this file: the next review follows whatever it says.

## Goal

Make every upcoming show in `data/agenda.json` match what its sources say today
(date, time, venue, lineup, price, ticket status), and add newly announced metal
shows in Argentina as drafts.

## Rules that are never broken

1. **Only facts you read today on a page you opened, and only on the allowed
   sites.** The allowed sites are the domains listed in `tools/FUENTES.md` (outside
   its "Para sumar" section) plus the links already saved in each show's sources
   and ticket links. Don't open anything else: use WebSearch with `allowed_domains`
   set to those domains, and WebFetch only on their pages. No memory, no
   assumptions. `tools/actualizar.py` rejects any source outside that list.
2. **Never publish or unpublish, never delete, never touch** the verification
   level, the featured flag, flyers, photos or descriptions. `tools/actualizar.py`
   already blocks this; never edit `agenda.json` by hand.
3. **New shows always go in as drafts**, with a source and an internal note.
4. **Date or venue changes and cancellations on a published show** need an
   official source (the band, the promoter, the venue or the ticket seller) or two
   independent media outlets saying the same thing. Otherwise, don't change it:
   leave a `nota_interna` (internal note) explaining what you saw and where.
5. **When in doubt, write an internal note.** It is better to alert the editor
   than to change something wrongly.
6. Don't touch anything outside `data/` and `reports/`.

The site is in Spanish. Write every text that ends up in `agenda.json` or in the
report (internal notes, the `resumen` summary, link labels) in Spanish.

## Steps

1. Add the repository to the session with `add_repo` (owner `bruno-g-galvan`,
   repo `distorsion`, access `push`) and clone it as the tool instructs.
2. Inside the repo, run `python3 tools/actualizar.py listar`. It returns the
   upcoming shows with their `id`, details, sources and internal note.
3. Check every show, in this order: published shows first, then drafts in the
   next 45 days, then the rest. Use WebSearch and WebFetch (the shell can't reach
   the web), only on the allowed sites. Start with the links the show already has,
   then the metal agendas, producers and ticket sellers in `tools/FUENTES.md`,
   then the media outlets there.
   - Something changed and it is confirmed: add it to `actualizar` with `campos`
     (the changed fields) and `fuentes` (sources).
   - Nothing changed and you confirmed it: add it to `actualizar` with `fuentes`
     and `"revisado": true`.
   - A draft is now confirmed by a better source, or there is something the
     editor should look at: write a `nota_interna`. It replaces the previous one,
     so write it in full.
   - Ticket status values: `anunciado` (announced), `venta` (on sale), `ultimas`
     (last tickets), `agotado` (sold out), `gratis` (free), `puerta` (at the door),
     `reprogramado` (rescheduled), `cancelado` (cancelled).
4. Look for new metal shows in Argentina in the next 6 months, reading the full
   agendas on the allowed sites: start with the metal agendas (Del Otro Lado Metal,
   Metal-Daze, El Carpo Rock) and the producers (Icarus Music, Noiseground), then
   the rest of `tools/FUENTES.md`. Include Argentine bands and shows outside Buenos
   Aires, not just international tours. Each one goes in `nuevos` with at least one
   source. Say in `nota_interna` if it only came from an aggregator (Songkick,
   Eventworld), or if two sources disagree on the date or venue.
5. Write `cambios.json` outside the repo (in your temporary folder) using the
   format explained at the top of `tools/actualizar.py`, and include a `resumen`
   of one or two sentences.
6. Run `python3 tools/actualizar.py aplicar <path>/cambios.json --prueba`. If it
   reports an error, fix the file and run it again. Then run it without `--prueba`.
7. Save and push:
   ```
   git add data/agenda.json reports/
   git commit -m "Revisión automática DD/MM: N actualizados, M nuevos"
   git push origin main
   ```
   If the push is rejected because someone published from the editor in the
   meantime: `git fetch origin main && git reset --hard FETCH_HEAD`, run step 6
   again without `--prueba`, then commit and push again.
   If nothing changed and there are no new shows, still push the day's report.
8. Finish with a short summary in Spanish: how many shows you checked, what
   changed in published shows (already live on the site), how many new drafts are
   waiting for review, and what needs the editor's attention.
