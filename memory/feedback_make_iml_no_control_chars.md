# Make IML: no soporta CR/LF literal en argumentos de función

## Descubrimiento (2026-04-18, scenario 4781819 HC Bot)

Make IML **NO** acepta caracteres de control (CR `\r`, LF `\n`) literales como argumentos
dentro de expresiones IML, incluso cuando aparecen como secuencias de escape JSON válidas
(`\r\n` / `\n`) en el archivo JSON del blueprint.

### Ejemplo que FALLA (blueprint se marca isinvalid: true):
```
{{replace(7.data.content[1].text; "\n"; " ")}}
```
Make ve el `\n` (newline literal al parsear el JSON) dentro del argumento del replace()
y rechaza la expresión IML completa.

### Por qué ocurrió:
La función de Python en el builder escribía:
```python
"json": "{{trim(replace(replace(replace(replace(...; \"\\r\\n\"; \" \"); \"\\n\"; \" \"))}}"
```
En el JSON serializado, `\\n` → `\n` (literal newline) → Make lo rechaza.

### Solución correcta:
- NO intentar limpiar `\n` en Make IML para este caso de uso.
- Usar instrucción en el prompt del modelo (Claude/Haiku) que prohibe saltos de línea
  dentro de strings JSON. Ejemplo: "CRITICO EXTRA — JSON EN UNA SOLA LINEA" en HC_BOT_SYSTEM_PROMPT.md.
- Make IML sí acepta `\n` como separador ENTRE bloques IML (fuera de `{{...}}`), 
  por ejemplo en valores de template como `"historia:\nU: {{...}}\nB: {{...}}"`.
  El problema es específicamente DENTRO de argumentos de funciones IML.

### Costo histórico:
~2 horas de debugging + múltiples pushes fallidos en scenario 4781819 (2026-04-18).
