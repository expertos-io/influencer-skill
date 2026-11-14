# Influencer IA · Contenido

Skill para Codex, Claude Code y cualquier agente: crea fotos y vídeos con tu influencer de IA desde el chat.

- Conecta tu cuenta de tu comunidad (con su dirección web).
- Recrea fotos y carruseles de Instagram con tu influencer.
- Recrea reels y vídeos con tu influencer.
- Ve y descarga lo que ya hiciste (fotos y vídeos) y tus planes de contenido.
- Todo con tus créditos.

## Instalar

Pídeselo a tu agente:

> Instala la skill de https://github.com/expertos-io/influencer-skill: clónala en `~/.codex/skills/influencer-ia-contenido` (si usas Claude Code, en `~/.claude/skills/influencer-ia-contenido`). Cuando esté instalada, úsala para conectarme a mi comunidad.

O a mano:

```bash
git clone https://github.com/expertos-io/influencer-skill.git ~/.codex/skills/influencer-ia-contenido
```

Para actualizarla: `git -C ~/.codex/skills/influencer-ia-contenido pull`.

## Para otra comunidad

La comunidad a la que se conecta es una sola línea, al principio de `scripts/influencer.py`:

```python
COMMUNITY_SITE = ""   # p. ej. "https://app.tumarca.com"
```

Vacía = la web principal (cada persona entra y elige su comunidad). Con una dirección, la skill se conecta
directamente a esa comunidad y no pregunta nada.
