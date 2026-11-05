# Corrección 01 · Datos del catálogo e inventario

Fecha: 5 de noviembre de 2026
Archivos: `data/espacios.json`, `data/inventario.json`, `scripts/validar_datos.py`

## Antes

El equipo preparó `espacios.json` (6 espacios) e `inventario.json` (10 artículos). Escribimos `scripts/validar_datos.py` con las reglas del equipo y los datos pasaron todas: 6 espacios, aforos coherentes, sin campos antiguos, sin "ficticio/a" en textos para el cliente, media correcta e inventario con espacios existentes.

Pasar el validador no quiere decir que no haya incoherencias. Al leer los datos como un cliente y como un comercial, salieron incoherencias que el validador no podía detectar.

## Problema

| # | Incoherencia encontrada | Gravedad |
|---|---|---|
| 1 | El Atelier de Sant Antoni tiene aforo de banquete de 35, pero la mesa redonda no se puede usar en él. Parecía que no había mesas para un banquete. | Alta |
| 2 | Las `url` de media son rutas de archivo y los archivos aún no existen. | Alta |
| 3 | El Mirador de Montjuïc tiene banquete de 120 exactos: con la conversación de referencia (cena para 120) entra sin margen. | Media |
| 4 | El guardarropa se recomienda a partir de 80 invitados, pero se podía usar en el Atelier, cuyo aforo máximo es 65. | Baja |
| 5 | El Mirador incluye calefactores en la terraza y el inventario ofrece calefactores para el Mirador. No quedaba claro si eran los mismos. | Baja |
| 6 | El tagline del Mirador hablaba de "vistas al skyline de la ciudad" y el full_profile de "vistas al mar y al puerto". | Baja |
| 7 | `project` está en inglés ("Space Enquiry - Barcelona Venues") y el nombre de la empresa sigue pendiente. | Baja |
| 8 | Llum del Poblenou incluye mesas y sillas para 200, pero su aforo de cóctel es 250. | Baja |
| 9 | El validador exigía un plano por espacio, pero no que estuviera aprobado. | Media |

## Cambio

| # | Qué decidimos | Por qué |
|---|---|---|
| 1 | No se quita la limitación. Nota en `mesa-redonda-10`: "El Atelier no la necesita: sus mesas configurables sirven para banquete." | El Atelier sí puede montar un banquete con su propio mobiliario; faltaba decirlo. |
| 4 | Se quita `sp-atelier-sant-antoni` de `usable_in` del guardarropa. | Con 65 de aforo máximo, el Atelier nunca llega al umbral de 80 invitados. |
| 5 | Nota en `calefactor`: "Unidades adicionales a las que ya tiene la terraza del Mirador." | Así el comercial no confunde los incluidos con los extra. |
| 6 | Tagline del Mirador: "Salón panorámico con terraza privada y vistas al mar y al puerto". | El tagline y el full_profile prometen lo mismo. |
| 9 | El validador exige al menos un plano **aprobado** por espacio. | Un plano no aprobado no se puede enseñar al cliente, así que no cuenta. |
| 2 | Sin cambios en los datos. | Se resuelve en el chat web, que mostrará imagen o enlace y nunca la ruta. |
| 3 | Sin cambios. | Lo cubre la regla del 90 % del recomendador, que lo marcará como "al límite". |
| 7 | Sin cambios por ahora. | Se cambiará cuando decidamos el nombre de la empresa. |
| 8 | Sin cambios. | Es correcto: en cóctel no hace falta silla para todos. |

## Después

- El validador vuelve a dar "todo correcto": 6 espacios, 24 elementos de media (23 aprobados) y 10 artículos de inventario. La única media no aprobada es `jardi-gracia-foto-02` (foto anterior a la reforma).
- Prueba del nuevo control: en una copia de los datos con el plano de Llum del Poblenou marcado como no aprobado, el validador da el error "sp-llum-poblenou: no tiene ningún plano aprobado".
- Las 9 incoherencias tienen decisión. Quedan dos tareas para más adelante: el chat web no debe mostrar rutas (2) y hay que cambiar `project` cuando tengamos el nombre de la empresa (7).

## Lección

Que el validador pase no significa que los datos tengan sentido. Las reglas automáticas comprueban la forma de los datos. Las incoherencias de contenido salen al leer los datos como un cliente y como un comercial.
