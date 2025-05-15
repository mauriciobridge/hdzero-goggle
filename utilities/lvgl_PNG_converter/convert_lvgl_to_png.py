from PIL import Image
import numpy as np
import re
import os
import sys

def convert_lvgl_image(c_file_path, output_path):
    # Leer el archivo
    with open(c_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extraer las dimensiones
    width_match = re.search(r'\.header\.w\s*=\s*(\d+)', content)
    height_match = re.search(r'\.header\.h\s*=\s*(\d+)', content)
    
    if not width_match or not height_match:
        raise ValueError("No se pudieron encontrar las dimensiones de la imagen")
    
    width = int(width_match.group(1))
    height = int(height_match.group(1))
    
    print(f"Dimensiones de la imagen: {width}x{height}")
    
    # Extraer los datos del mapa
    # Buscar en el contenido después de "LV_COLOR_DEPTH == 32"
    data_section = re.search(r'LV_COLOR_DEPTH == 32.*?\/\*Pixel format.*?\*\/.*?0x([^#]+)#endif', content, re.DOTALL)
    
    if not data_section:
        raise ValueError("No se pudieron encontrar los datos de la imagen para el formato de 32 bits")
    
    data_str = data_section.group(1)
    
    # Eliminar comentarios y espacios en blanco
    data_str = re.sub(r'/\*.*?\*/', '', data_str, flags=re.DOTALL)
    data_str = re.sub(r'//.*?$', '', data_str, flags=re.MULTILINE)
    
    # Extraer todos los valores hexadecimales
    hex_values = re.findall(r'0x[0-9a-fA-F]+|[0-9]+', data_str)
    
    # Convertir a bytes
    data_bytes = []
    for value in hex_values:
        try:
            if value.startswith('0x'):
                data_bytes.append(int(value, 16))
            else:
                data_bytes.append(int(value))
        except ValueError:
            pass
    
    # Crear la imagen
    img_array = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Para el archivo img_star.c, el formato parece ser BGRA, con bytes en el orden: B, G, R, A
    # Vamos a probar con este formato específico basado en el patrón de datos observado
    for y in range(height):
        for x in range(width):
            index = (y * width + x) * 4
            if index + 3 < len(data_bytes):
                # En este caso específico, el formato parece ser BGRA
                b = data_bytes[index]
                g = data_bytes[index + 1]
                r = data_bytes[index + 2]
                a = data_bytes[index + 3]
                
                # Si el color es verde (chroma key), hacerlo transparente
                if r == 0 and g == 255 and b == 0:
                    a = 0
                
                img_array[y, x] = [r, g, b, a]
    
    # Crear y guardar la imagen
    img = Image.fromarray(img_array, 'RGBA')
    img.save(output_path)
    print(f"Imagen guardada como {output_path}")

if __name__ == "__main__":
    input_file = 'img_star.c' if len(sys.argv) <= 1 else sys.argv[1]
    output_file = os.path.splitext(input_file)[0] + '.png'
    
    try:
        convert_lvgl_image(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()