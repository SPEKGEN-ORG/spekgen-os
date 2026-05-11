---
name: Make text:pattern no soporta (?i) inline flag
description: Make's text:pattern operator falla silenciosamente con (?i) inline flag al inicio del regex — usar character classes explicitos
type: feedback
---

**Regla**: El operador `text:pattern` de Make (filter conditions) NO soporta el inline flag `(?i)` al inicio del regex. Cuando lo ve, falla el match silenciosamente (no throw, no log) y retorna false siempre. Lo mismo aplica a cualquier otra bandera posicional tipo `(?m)`, `(?s)`.

**Workaround**: Usar character classes explicitos letra por letra para case-insensitivity:

```
# WRONG (Make's text:pattern lo rompe silenciosamente):
(?i)^\s*(hola+|buenas|hi+)[\s!]*$

# RIGHT (character classes por letra):
^\s*([Hh][Oo][Ll][Aa]+|[Bb][Uu][Ee][Nn][Aa][Ss]|[Hh][Ii]+)[\s!]*$
```

**Como se detecto**: 2026-04-10 durante test E2E del GR WhatsApp bot. Gibran mando `hola` al bot. Ambas ejecuciones (msg#1 `hola` y msg#2 `hola, buscas algo para reflujo`) corrieron 8 ops = ruta Claude (greeting shortcut serian 6 ops). El greeting shortcut nunca disparo porque el pattern `(?i)^\s*(hola+|...)...$` no matcheaba NADA. Invertido (`text:notpattern`) el filter siempre retornaba true → todo caia a Claude route. Fix: character classes explicitos. Validado con 16/16 casos Python antes de push.

**Why**: Make filter regex engine no compila o trata literal los `(?i)` → `^` anchor requiere "hola" empiece con `(?i)` literal → jamas matchea. El costo: Claude corrio en mensajes que debieron ser canned greetings → ~$0.015 USD extra por saludo + latencia extra ~2s.

**How to apply**:
- Cualquier `text:pattern` o `text:notpattern` en Make filters: NO usar `(?i)`, `(?m)`, `(?s)` al inicio
- Si necesitas case-insensitive, character classes explicitos por letra (`[Hh][Oo][Ll][Aa]`)
- Siempre validar el regex en Python antes de push al blueprint (`re.match(pattern, test_input)`)
- Dentro del groupo `(?i:...)` tampoco es seguro — evitarlo. Mejor character class por letra
- Hermano del bug plural (`text:notcontains` vs `text:notcontain`): ambos fallan silenciosamente, ambos deben validarse contra docs de Make
- Documentado en `GR_BOT_CHANGELOG.md` entry 2026-04-10 22:56
