# PROMPT_PACK_PRODUCT — 8 SCALIST prompts para Soul Training de productos

> Template reusable para CUALQUIER producto (HC, GR, LF, MG). Reemplazar todos los placeholders `{...}` con specs reales del producto antes de pegar en Gemini Nano Banana Pro.
>
> **Uso:** Copia todo este archivo como `PROMPTS.md` en la carpeta de batch del producto, reemplaza placeholders, y úsalo como hoja de pegado.

## Placeholders a reemplazar

| Placeholder | Qué va | Ejemplo (ArtriDog HC) |
|---|---|---|
| `{PRODUCT_NAME}` | Nombre del producto | ArtriDog |
| `{BRAND_NAME}` | Marca | Healthy Chuchos |
| `{CONTAINER_TYPE}` | Tipo de envase | white HDPE plastic jar with white ribbed screw cap |
| `{CONTAINER_SIZE}` | Tamaño/peso | 225 g jar, 9cm tall x 10cm diameter |
| `{COLOR_PALETTE}` | Colores brand | teal #20838A, coral #F4A57C, navy #1F2A5C, white |
| `{KEY_VISUALS}` | Elementos clave label | "Healthy Chuchos" mascot logo (orange/teal cat-dog), Bernese Mountain Dog illustration with orange skeleton highlight, paw print in 'o' of ArtriDog wordmark |
| `{TAGLINE}` | Subtítulo | Suplemento nutricional / Coadyuvante para la salud articular |
| `{SIZE_LABEL_TEXT}` | Texto de peso | cont. neto 225 g |
| `{INGREDIENT_LIST}` | Para flat-lay | turmeric powder, apple slices, glucosamine crystalline powder, black peppercorns, Boswellia resin |
| `{LIFESTYLE_PET}` | Para shot 7 | Bernese Mountain Dog (matching the breed shown on the label) |

---

## Identity Lock prefix (común a los 8 prompts)

```
IDENTITY LOCK: Using the uploaded reference image of the {PRODUCT_NAME} 
{CONTAINER_TYPE}, preserve 100% of the product's exact geometry, label 
artwork, typography, brand logos, color palette ({COLOR_PALETTE}), and 
all key visual elements: {KEY_VISUALS}. Do not alter, redraw, or 
hallucinate new label details. The {CONTAINER_TYPE} must remain physically 
identical to the reference across all generated images.
```

Cada prompt abajo asume este prefix antepuesto.

---

## 1 — Hero Packshot 3/4 Angle (canonical)

```
{IDENTITY_LOCK_PREFIX}

A photorealistic high-end commercial product shot, square 1:1 composition. 
The {PRODUCT_NAME} {CONTAINER_TYPE} (from the reference image) sits on a 
smooth white seamless infinity background, photographed from a slight 
three-quarter angle that shows the front label fully readable while 
revealing the curved side of the container and the texture of the cap.

Three-point softbox lighting setup: a large key softbox at 45 degrees 
from the upper-left providing soft diffused illumination across the front 
label, a smaller fill softbox from the lower-right reducing shadow 
density, and a hair-light from behind creating a subtle rim highlight 
along the right edge. Realistic specular highlights and subsurface 
scattering through the white surface. Deep ambient occlusion shadow 
grounds the container against the surface. The cap shows crisp specular 
reflections.

Shot on a Hasselblad H6D medium format, 120mm macro lens, f/8 aperture 
for edge-to-edge sharpness from cap to base. Organic film grain, subtle 
chromatic aberration on the highlights. Native 4K resolution.

Avoid plastic synthetic rendering, avoid floating container without 
contact shadow, avoid label artwork distortion, avoid digital sticker 
overlay appearance on the label. The container must feel weighty and 
physically present.
```

---

## 2 — Hero Packshot Frontal (label maximum legibility)

```
{IDENTITY_LOCK_PREFIX}

A photorealistic studio packshot, square 1:1 composition. The 
{PRODUCT_NAME} {CONTAINER_TYPE} is photographed at perfectly perpendicular 
front angle, eye-level, centered, with the entire front label visible 
and razor-sharp readable. The container floats slightly above a soft 
white reflective acrylic surface that produces a clean gradient 
reflection beneath.

Lighting: a large diffused softbox directly above the camera position 
creating an even, flat illumination across the entire front label with 
zero hot spots, plus two stripbox edge lights at far left and far right 
producing soft rim highlights down the curved sides. The cap shows fine 
specular detail. Realistic ambient occlusion where the container meets 
the acrylic surface.

Shot on a Phase One XF IQ4 medium format, 80mm macro lens, f/11 for 
absolute label sharpness. Subtle film grain and slight halation around 
highlights. Native 4K resolution. Catalog-grade commercial product 
photography aesthetic.

Avoid distorted label text, avoid uneven lighting hotspots, avoid 
floating shadows, avoid any AI artifacts on the typography. The label 
must read as crisp printed material on textured paper.
```

---

## 3 — Macro Label Detail (texture closeup)

```
{IDENTITY_LOCK_PREFIX}

A photorealistic extreme macro photograph, square 1:1 composition, 
focused on the front label of the {PRODUCT_NAME} {CONTAINER_TYPE}. The 
frame fills with the central portion of the label showing the wordmark, 
"{TAGLINE}" subtitle, and the upper portion of any label illustration. 
The container curvature is visible as soft falloff at the edges of the 
frame.

The label paper texture shows visible matte fiber weave at macro scale, 
subtle grain, and the printed inks show slight micro-texture as if 
offset-printed on premium uncoated paper. Tiny imperfections like a 
single dust mote and a barely-visible micro-scratch add authenticity.

Lighting: soft directional window light from the upper-right at 30 
degrees grazing across the label surface, revealing paper texture 
through micro-shadows in the fiber weave. Shallow depth of field with 
the wordmark in tack-sharp focus and the edges falling into creamy 
defocus.

Shot on a Canon EOS R5 with a 100mm macro lens, f/4, focus-stacked for 
crisp typography. Organic film grain. 4K native resolution.

Avoid digital pixel artifacts on the typography, avoid synthetic flat 
overlay aesthetic on the label, avoid retouched skin-smooth paper 
appearance. The label must feel like real printed material under a 
macro lens.
```

---

## 4 — Top-Down Flat Lay with Ingredients

```
{IDENTITY_LOCK_PREFIX}

A photorealistic editorial flat-lay overhead shot, square 1:1 
composition, shot from directly above at 90 degrees. The {PRODUCT_NAME} 
{CONTAINER_TYPE} (cap visible from above) is positioned slightly 
off-center to the right. Surrounding the container in an artful natural 
arrangement: {INGREDIENT_LIST}.

The surface beneath is a textured dark slate stone with natural mineral 
veining, subtle chips at the edges, and matte finish that absorbs light 
cleanly without reflection.

Lighting: soft diffused daylight from the top of the frame creating 
gentle shadows extending downward, revealing the three-dimensional 
texture of every ingredient. Subsurface scattering visible in any 
translucent ingredient. Specular micro-highlights on metallic elements. 
Ambient occlusion shadows ground every element to the slate.

Shot on a Sony A7R IV, 90mm macro lens, f/11 for total depth of field, 
overhead tripod position. Organic film grain. Native 4K resolution. 
Editorial natural-wellness magazine aesthetic.

Avoid floating ingredients without grounding shadows, avoid fake 
plastic-looking ingredients, avoid sterile vacuum cleanliness. The 
arrangement must feel like a natural editorial styling shoot.
```

---

## 5 — Marble + Golden Hour Lifestyle

```
{IDENTITY_LOCK_PREFIX}

A photorealistic lifestyle product photograph, square 1:1 composition. 
The {PRODUCT_NAME} {CONTAINER_TYPE} rests centered on a polished white 
Carrara marble countertop with subtle grey veining and natural mineral 
imperfections. The marble surface shows a soft realistic reflection of 
the container beneath.

Background: a softly out-of-focus modern Mexican kitchen with hints of 
warm wood cabinetry on the left and a window on the right where late 
afternoon golden hour sunlight streams in at a low 25-degree angle, 
casting warm directional light across the container from camera-right 
and creating a long soft shadow that extends to camera-left across the 
marble.

The golden hour light wraps around the curved surface creating warm 
specular highlights on the right edge and rim lighting along the cap, 
while the left side falls into cool ambient shadow tones. Floating 
dust particles drift through the warm light beam adding atmospheric 
depth.

Shot on a Canon EOS R5, 85mm f/1.4 lens, shallow depth of field with 
the container tack-sharp and the kitchen background blurred into creamy 
bokeh. Organic film grain mimicking Kodak Portra 400, slight halation 
around highlights, subtle chromatic aberration. Native 4K resolution.

Avoid sterile studio lighting, avoid floating container, avoid label 
distortion. The scene must feel like a candid early-evening 
home-photography moment.
```

---

## 6 — Dramatic Chiaroscuro (low-key)

```
{IDENTITY_LOCK_PREFIX}

A photorealistic dramatic low-key product photograph, square 1:1 
composition. The {PRODUCT_NAME} {CONTAINER_TYPE} is centered against a 
deep matte black seamless background void, photographed from a slight 
three-quarter angle that shows the full front label.

Lighting: a single hard-edged spotlight positioned at 45 degrees from 
the upper-left at high intensity, creating dramatic chiaroscuro across 
the surface. The illuminated side reveals every label detail, brand 
colors pop against the darkness, and the curved surface shows 
pronounced specular highlights along its left edge. The right side 
falls into deep shadow with subtle rim light separating the silhouette 
from the black background.

The surface beneath is the same matte black material as the background, 
producing a deep contact shadow with strong ambient occlusion. Subtle 
atmospheric haze and a few floating dust particles catch the spotlight.

Shot on a Hasselblad H6D, 120mm macro lens, f/5.6, with deep tonal 
contrast. Heavy organic film grain mimicking pushed Kodak Tri-X 400 
contrast (in full color), subtle chromatic aberration on the highlight 
edge. Native 4K resolution.

Avoid flat soft lighting, avoid floating container, avoid plastic 
synthetic rendering. The image must feel cinematic, premium, and 
editorially dramatic.
```

---

## 7 — Lifestyle with Pet/Subject in Bokeh Background

```
{IDENTITY_LOCK_PREFIX}

A photorealistic candid lifestyle photograph, square 1:1 composition. 
The {PRODUCT_NAME} {CONTAINER_TYPE} sits in tack-sharp focus on a warm 
wooden floor in a sunlit Mexican home. The container fills the 
lower-right third of the frame, giving negative space to the upper-left 
where the lifestyle context unfolds.

In the soft creamy bokeh background, an actual {LIFESTYLE_PET} lies 
relaxed on a beige rug, out of focus but identifiable, with natural 
texture rendered as soft blurred patches. Warm directional sunlight 
from a window streams from the upper-right, creating soft diffused 
light across the container with gentle specular highlights and crisp 
readability on the label.

The background shows hints of a wooden coffee table leg, a soft beige 
rug, and warm afternoon sunlight pooling on the floor. Depth of field 
creates a beautiful separation between the in-focus container and the 
defocused but contextually rich domestic scene.

Shot on a Sony A7R IV, 85mm f/1.4 lens, shot at f/2 for shallow depth 
of field. Organic film grain mimicking Kodak Portra 400, subtle 
chromatic aberration, soft halation on the window light. Native 4K 
resolution.

Avoid plastic subject rendering, avoid sterile lighting, avoid label 
distortion, avoid floating container. The scene must feel like a real 
afternoon moment in a pet owner's home.
```

---

## 8 — Dynamic Action (frozen powder/liquid splash)

```
{IDENTITY_LOCK_PREFIX}

A photorealistic high-speed action product photograph, square 1:1 
composition. The {PRODUCT_NAME} {CONTAINER_TYPE} is centered in the 
frame with the cap removed and floating slightly above the container, 
frozen in mid-air. From the open mouth, a dynamic burst of supplement 
powder (matching the brand color tones) erupts upward in swirling 
clouds, with thousands of individual particles frozen mid-flight 
catching the light, creating a dramatic plume that fills the upper 
half of the frame.

Lighting: a high-intensity strobe from the upper-left creating crisp 
edge-light on every airborne particle, with a secondary fill light 
from below illuminating the cascading particles. Each individual grain 
is rendered with photorealistic detail, accurate motion freeze, 
subsurface scattering through the lighter particles, and realistic 
depth-of-field falloff.

Background: a clean light-grey seamless backdrop with subtle gradient 
darkening toward the corners. The container sits on a matching surface 
with realistic deep ambient occlusion contact shadow.

Shot on a Nikon Z9, 105mm macro lens, f/8, 1/8000s shutter speed using 
high-speed strobe synchronization. Organic film grain, slight halation 
on the brightest particles, chromatic aberration on the highlights. 
Native 4K resolution. Commercial supplement advertising aesthetic.

Avoid CGI plastic appearance, avoid uniform particle distribution, 
avoid floating container without contact shadow, avoid label distortion. 
The powder must feel real, the motion must feel captured rather than 
rendered, and the container must feel weighty.
```

---

## Checklist post-generación

Antes de subir a Higgsfield para Soul training, verifica cada output:

- [ ] **01_hero_3_4** — etiqueta legible, proporciones correctas, ambient occlusion presente
- [ ] **02_frontal** — etiqueta perfectamente recta, sin distorsión
- [ ] **03_macro_label** — texturas de papel visibles, typography afilada
- [ ] **04_flat_lay** — ingredientes con sombras realistas, producto con cap correcto
- [ ] **05_marble_golden_hour** — luz cálida coherente, mármol con reflejo
- [ ] **06_chiaroscuro** — fondo negro absoluto, spotlight dramático
- [ ] **07_lifestyle_bokeh** — pet identificable pero blurred, producto in-focus
- [ ] **08_action_splash** — partículas frozen, cap separated, sin CGI obvio

**Score mínimo:** 5/8 imágenes en ≥8/10 según rubric Gemini Realism Research.

Si <5 pasan: regenerar las que fallaron antes de Soul training. Soul aprende de lo que recibe — basura entra, basura sale para siempre.
