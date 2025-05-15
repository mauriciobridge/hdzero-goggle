from PIL import Image
import numpy as np
import os
import sys

def convert_png_to_lvgl_c(png_file_path, c_file_path, img_name=None):
    """
    Convierte un archivo PNG a un archivo C con formato LVGL.
    
    Args:
        png_file_path: Ruta al archivo PNG de entrada
        c_file_path: Ruta de salida para el archivo C
        img_name: Nombre de la imagen en LVGL (por defecto: derivado del nombre del archivo)
    """
    try:
        # Si no se especifica un nombre de imagen, usamos el nombre base del archivo
        if img_name is None:
            img_name = os.path.splitext(os.path.basename(png_file_path))[0]
        
        # Abrir la imagen PNG
        img = Image.open(png_file_path)
        
        # Convertir a RGBA si no está en ese formato
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Obtener dimensiones
        width, height = img.size
        
        # Convertir la imagen a un array numpy para procesamiento
        img_array = np.array(img)
        
        # Crear el array de bytes en formato LVGL
        bytes_data = []
        
        # Para formato BGRA (en LVGL, según el archivo original)
        for y in range(height):
            for x in range(width):
                # Obtener valor RGBA
                r, g, b, a = img_array[y, x]
                
                # Verificar si este píxel debe ser chroma key
                # Si los valores R, G, B indican un color negro total (0,0,0), podríamos querer mantener la transparencia
                if r == 0 and g == 0 and b == 0 and a < 128:
                    # Hacer que sea verde para el chroma key
                    b = 0
                    g = 255
                    r = 0
                    a = 255  # Opaco para el chroma key
                
                # En el formato LVGL según el script de conversión inversa, el orden es BGRA
                bytes_data.append(b)  # Blue
                bytes_data.append(g)  # Green
                bytes_data.append(r)  # Red
                bytes_data.append(a)  # Alpha
                
        # Generar el contenido del archivo C
        c_content = generate_lvgl_c_file(img_name, width, height, bytes_data)
        
        # Guardar el archivo C
        with open(c_file_path, 'w') as f:
            f.write(c_content)
        
        print(f"Archivo C generado exitosamente: {c_file_path}")
        print(f"Nombre de la imagen: {img_name}")
        print(f"Nombre del mapa de datos: {img_name}_map")
        print(f"Dimensiones: {width}x{height}")
        return True
    
    except Exception as e:
        print(f"Error al convertir la imagen: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_lvgl_c_file(img_name, width, height, bytes_data):
    """
    Genera el contenido del archivo C en formato LVGL.
    
    Args:
        img_name: Nombre de la imagen
        width: Ancho de la imagen
        height: Alto de la imagen
        bytes_data: Lista de bytes en formato LVGL
    
    Returns:
        Contenido del archivo C como string
    """
    # Crear el array de bytes en formato C
    bytes_per_line = 16  # Número de bytes por línea
    formatted_data = ""
    
    # Generar los datos en bloques
    for i in range(0, len(bytes_data), bytes_per_line):
        # Obtener los bytes para esta línea
        line_bytes = bytes_data[i:i+bytes_per_line]
        
        # Formatear cada línea
        line = ", ".join([f"0x{byte:02x}" for byte in line_bytes])
        
        # Añadir la línea al resultado
        formatted_data += line
        
        # Añadir coma y nueva línea si no es la última línea
        if i + bytes_per_line < len(bytes_data):
            formatted_data += ",\n"
    
    # Plantilla del archivo C basada en img_star.c
    template = f"""#if defined(LV_LVGL_H_INCLUDE_SIMPLE)
#include "lvgl.h"
#else
#include "lvgl/lvgl.h"
#endif


#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_{img_name.upper()}
#define LV_ATTRIBUTE_IMG_{img_name.upper()}
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_{img_name.upper()} uint8_t {img_name}_map[] = {{
#if LV_COLOR_DEPTH == 1 || LV_COLOR_DEPTH == 8
  /*Pixel format: Red: 3 bit, Green: 3 bit, Blue: 2 bit*/

#error NOT IMPLEMENTED

#endif
#if LV_COLOR_DEPTH == 16 && LV_COLOR_16_SWAP == 0
  /*Pixel format: Red: 5 bit, Green: 6 bit, Blue: 5 bit*/

#error NOT IMPLEMENTED

#endif
#if LV_COLOR_DEPTH == 16 && LV_COLOR_16_SWAP != 0
  /*Pixel format: Red: 5 bit, Green: 6 bit, Blue: 5 bit BUT the 2 bytes are swapped*/

#error NOT IMPLEMENTED

#endif
#if LV_COLOR_DEPTH == 32
  /*Pixel format: Fix 0xFF: 8 bit, Red: 8 bit, Green: 8 bit, Blue: 8 bit*/
  /* actually it is other way around */
{formatted_data}
#endif
}};

const lv_img_dsc_t {img_name} = {{
  .header.cf = LV_IMG_CF_TRUE_COLOR_CHROMA_KEYED,
  .header.always_zero = 0,
  .header.reserved = 0,
  .header.w = {width},
  .header.h = {height},
  .data_size = {width * height} * LV_COLOR_SIZE / 8,
  .data = {img_name}_map,
}};
"""
    return template

def main():
    if len(sys.argv) < 2:
        print("Uso: python png_to_lvgl.py imagen.png [imagen.c] [nombre_imagen]")
        print("  imagen.png: Ruta al archivo PNG de entrada")
        print("  imagen.c: (Opcional) Ruta de salida para el archivo C (por defecto: nombre_png.c)")
        print("  nombre_imagen: (Opcional) Nombre de la imagen en LVGL (por defecto: nombre base del archivo)")
        return 1
    
    # Obtener parámetros
    png_file_path = sys.argv[1]
    
    # Nombre base del archivo de entrada
    base_name = os.path.splitext(os.path.basename(png_file_path))[0]
    
    # Nombre del archivo C de salida (opcional)
    if len(sys.argv) > 2:
        c_file_path = sys.argv[2]
    else:
        c_file_path = f"{base_name}.c"
    
    # Nombre de la imagen en LVGL (opcional)
    img_name = None  # Por defecto, se usará el nombre base del archivo
    if len(sys.argv) > 3:
        img_name = sys.argv[3]
    
    # Convertir PNG a archivo C de LVGL
    success = convert_png_to_lvgl_c(png_file_path, c_file_path, img_name)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())