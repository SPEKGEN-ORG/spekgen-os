# File delivery — preferencia Gibran

**Correcto**: Claude ejecuta `open` directamente cuando termina un entregable. No dar al user nada que tenga que copiar/pegar.

```bash
open "/ruta/archivo.pdf"                       # abre el archivo
open -R "/ruta/archivo.pdf"                    # revela en Finder
open "/ruta/carpeta/"                          # abre carpeta en Finder
```

**NO hacer**:
- ❌ Dar comando `open` al user para que lo copie en terminal
- ❌ Dar markdown links con `file://` — no funcionan
- ❌ Dar paths como texto esperando que los click

**Hacer**:
- ✅ Ejecutar `open` con la Bash tool directamente al terminar
- ✅ Para PDFs/docs: abrir el archivo + revelar en Finder (ambos)
- ✅ Para carpetas completas: solo `open` la carpeta
