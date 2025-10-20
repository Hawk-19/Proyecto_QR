import segno
from PIL import Image, ImageDraw
import os

def generar_qr(url: str, output_path: str, logo_path: str = None):
    scale = 20          # Tamaño de cada módulo
    border = 4          # Margen alrededor del QR
    dot_scale = 0.6     # Escala de los puntos
    def is_position_marker(x, y, size):
        """Detecta los marcadores de posición (esquinas)"""
        return (
            (x <= 6 and y <= 6) or
            (x >= size - 7 and y <= 6) or
            (x <= 6 and y >= size - 7)
        )
    # Generar QR y obtener la matriz
    qr = segno.make(url, error='h')
    matrix = qr.matrix
    qr_size = len(matrix)
    img_size = (qr_size + 2 * border) * scale
    # Crear imagen en blanco
    img = Image.new("RGBA", (img_size, img_size), "white")
    draw = ImageDraw.Draw(img)
    # Dibujar módulos
    for y, row in enumerate(matrix):
        for x, cell in enumerate(row):
            if not cell:
                continue
            px = (x + border) * scale
            py = (y + border) * scale
            if is_position_marker(x, y, qr_size):
                draw.rectangle([px, py, px + scale, py + scale], fill="black")
            else:
                dot_size = int(scale * dot_scale)
                offset = (scale - dot_size) // 2
                draw.ellipse(
                    [px + offset, py + offset, px + offset + dot_size, py + offset + dot_size],
                    fill="black"
                )
    # Agregar logo centrado (solo si existe)
    if logo_path and os.path.exists(logo_path):
        print("Insertando logo:", logo_path)
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = img_size // 4
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        pos = ((img_size - logo_size) // 2, (img_size - logo_size) // 2)
        # Crear imagen temporal para hacer el composite
        temp = Image.new("RGBA", img.size, (0, 0, 0, 0))
        temp.paste(logo, pos, mask=logo)
        img = Image.alpha_composite(img, temp)
    # Guardar QR final
    img.save(output_path)
    print("QR generado en:", output_path)
