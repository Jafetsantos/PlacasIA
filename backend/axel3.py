import cv2
import numpy as np
import pytesseract
import re
from datetime import datetime
import psycopg2
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

# Configuración de la base de datos
DB_CONFIG = {
    'dbname': 'placas',
    'user': 'postgres',
    'password': 'ADMIN',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def preprocess_image(image):
    # Convertir a escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Aplicar desenfoque gaussiano
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Aplicar umbral adaptativo
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Aplicar operaciones morfológicas
    kernel = np.ones((1, 1), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return morph

def detect_plate(image):
    # Preprocesar la imagen
    processed = preprocess_image(image)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(
        processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Filtrar contornos por área y relación de aspecto
    plates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)
        
        # Criterios para una placa
        if 2.0 < aspect_ratio < 5.0 and 1000 < w * h < 50000:
            plates.append((x, y, w, h))
    
    return plates

def extract_text(image, plate_region):
    x, y, w, h = plate_region
    roi = image[y:y+h, x:x+w]
    
    # Preprocesar ROI
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Configurar Tesseract para mejor reconocimiento
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text = pytesseract.image_to_string(thresh, config=custom_config)
    
    # Limpiar y validar el texto
    text = re.sub(r'[^A-Z0-9]', '', text)
    if len(text) >= 6:  # Longitud mínima para una placa
        return text
    return None

def detect_vehicle_info(image, plate_region):
    x, y, w, h = plate_region
    # Ajustar la región para incluir más del vehículo
    vehicle_roi = image[max(0, y-100):y+h, x:x+w]
    
    # Convertir a HSV para mejor detección de color
    hsv = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2HSV)
    
    # Detectar color dominante
    hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
    color_idx = np.argmax(hist)
    
    # Mapear colores comunes
    color_map = {
        range(0, 15): 'Rojo',
        range(15, 30): 'Naranja',
        range(30, 60): 'Amarillo',
        range(60, 90): 'Verde',
        range(90, 120): 'Azul',
        range(120, 150): 'Morado',
        range(150, 180): 'Rosa'
    }
    
    color = 'Desconocido'
    for range_colors, color_name in color_map.items():
        if color_idx in range_colors:
            color = color_name
            break
    
    # Detectar marca y modelo (esto es un ejemplo básico)
    # En una implementación real, usarías un modelo de ML entrenado
    marca = 'Desconocida'
    modelo = 'Desconocido'
    
    return {
        'marca': marca,
        'modelo': modelo,
        'color': color
    }

def process_frame(frame):
    try:
        # Detectar placas
        plates = detect_plate(frame)
        
        if not plates:
            return None
        
        # Procesar cada placa detectada
        results = []
        for plate in plates:
            # Extraer texto de la placa
            plate_text = extract_text(frame, plate)
            if not plate_text:
                continue
            
            # Detectar información del vehículo
            vehicle_info = detect_vehicle_info(frame, plate)
            
            # Verificar en la base de datos
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT p.id, p.estado, per.nombre_completo, per.cargo
                        FROM placas p
                        JOIN personas per ON p.persona_id = per.id
                        WHERE p.numero_placa = %s
                    """, (plate_text,))
                    
                    result = cursor.fetchone()
                    if result:
                        placa_id, estado, usuario, cargo = result
                        
                        # Registrar el acceso
                        cursor.execute("""
                            INSERT INTO registros_acceso (
                                placa_id, acceso, fecha_hora_entrada
                            ) VALUES (%s, %s, CURRENT_TIMESTAMP)
                            RETURNING id
                        """, (placa_id, 'Entrada' if estado == 'Activo' else 'Denegado'))
                        
                        acceso_id = cursor.fetchone()[0]
                        conn.commit()
                        
                        results.append({
                            'placa': plate_text,
                            'usuario': usuario,
                            'cargo': cargo,
                            'estado': estado,
                            'acceso': 'Entrada' if estado == 'Activo' else 'Denegado',
                            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                            'marca': vehicle_info['marca'],
                            'modelo': vehicle_info['modelo'],
                            'color': vehicle_info['color']
                        })
                finally:
                    conn.close()
        
        return results if results else None
        
    except Exception as e:
        print(f"Error en el procesamiento: {e}")
        return None

class RegistroUsuarioVehiculo:
    def __init__(self, parent, numero_placa):
        self.parent = parent
        self.numero_placa = numero_placa
        
        # Crear ventana
        self.window = tk.Toplevel(parent)
        self.window.title("Registro de Usuario")
        self.window.geometry("500x580")
        self.window.configure(bg="#f5f5f5")
        
        # Hacer que esta ventana sea modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.crear_widgets()
        
        # Centrar la ventana
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def crear_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.window, padx=25, pady=20, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(main_frame, 
                        text="Registro de Usuario y Vehículo", 
                        font=("Arial", 18, "bold"),
                        bg="#f5f5f5", fg="#333333")
        titulo.grid(row=0, column=0, columnspan=2, pady=(0, 25), sticky="w")
        
        # Separador horizontal
        separador = ttk.Separator(main_frame, orient="horizontal")
        separador.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Información de la placa
        tk.Label(main_frame, 
                text="Número de Placa:", 
                font=("Arial", 12, "bold"),
                bg="#f5f5f5", fg="#333333").grid(row=2, column=0, sticky="w", pady=10)
        
        tk.Label(main_frame, 
                text=self.numero_placa, 
                font=("Arial", 12),
                bg="#f5f5f5", fg="#0066cc").grid(row=2, column=1, sticky="w", pady=10)
        
        # Datos del usuario
        tk.Label(main_frame, 
                text="DATOS DEL USUARIO", 
                font=("Arial", 12, "bold"),
                bg="#f5f5f5", fg="#333333").grid(row=3, column=0, columnspan=2, sticky="w", pady=(15, 10))
        
        # Nombre completo
        tk.Label(main_frame, 
                text="Nombre Completo:", 
                font=("Arial", 11),
                bg="#f5f5f5").grid(row=4, column=0, sticky="w", pady=8)
        
        self.nombre_entry = tk.Entry(main_frame, font=("Arial", 11), width=30, bd=2, relief="groove")
        self.nombre_entry.grid(row=4, column=1, sticky="w", pady=8)
        
        # Cargo
        tk.Label(main_frame, 
                text="Cargo:", 
                font=("Arial", 11),
                bg="#f5f5f5").grid(row=5, column=0, sticky="w", pady=8)
        
        self.cargo_combo = ttk.Combobox(main_frame, 
                                      font=("Arial", 11), 
                                      width=28, 
                                      values=["Estudiante", "Docente", "Administrativo", "Visitante"],
                                      state="readonly")
        self.cargo_combo.current(0)
        self.cargo_combo.grid(row=5, column=1, sticky="w", pady=8)
        
        # Datos del vehículo
        tk.Label(main_frame, 
                text="DATOS DEL VEHÍCULO", 
                font=("Arial", 12, "bold"),
                bg="#f5f5f5", fg="#333333").grid(row=6, column=0, columnspan=2, sticky="w", pady=(15, 10))
        
        # Tipo de vehículo
        tk.Label(main_frame, 
                text="Tipo de Vehículo:", 
                font=("Arial", 11),
                bg="#f5f5f5").grid(row=7, column=0, sticky="w", pady=8)
        
        self.vehiculo_combo = ttk.Combobox(main_frame, 
                                         font=("Arial", 11), 
                                         width=28, 
                                         values=["Automóvil", "Motocicleta", "Camioneta", "SUV", "Pickup"],
                                         state="readonly")
        self.vehiculo_combo.current(0)
        self.vehiculo_combo.grid(row=7, column=1, sticky="w", pady=8)
        
        # Marca
        tk.Label(main_frame, 
                text="Marca:", 
                font=("Arial", 11),
                bg="#f5f5f5").grid(row=8, column=0, sticky="w", pady=8)
        
        self.marca_entry = tk.Entry(main_frame, font=("Arial", 11), width=30, bd=2, relief="groove")
        self.marca_entry.grid(row=8, column=1, sticky="w", pady=8)
        
        # Modelo
        tk.Label(main_frame, 
                text="Modelo:", 
                font=("Arial", 11),
                bg="#f5f5f5").grid(row=9, column=0, sticky="w", pady=8)
        
        self.modelo_entry = tk.Entry(main_frame, font=("Arial", 11), width=30, bd=2, relief="groove")
        self.modelo_entry.grid(row=9, column=1, sticky="w", pady=8)
        
        # Color
        tk.Label(main_frame, 
                text="Color:", 
                font=("Arial", 11),
                bg="#f5f5f5").grid(row=10, column=0, sticky="w", pady=8)
        
        self.color_entry = tk.Entry(main_frame, font=("Arial", 11), width=30, bd=2, relief="groove")
        self.color_entry.grid(row=10, column=1, sticky="w", pady=8)
        
        # Separador horizontal
        separador2 = ttk.Separator(main_frame, orient="horizontal")
        separador2.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(20, 20))
        
        # Frame para botones
        btn_frame = tk.Frame(main_frame, bg="#f5f5f5")
        btn_frame.grid(row=12, column=0, columnspan=2, pady=5)
        
        # Botones
        self.guardar_btn = tk.Button(
            btn_frame, 
            text="Guardar", 
            font=("Arial", 11, "bold"), 
            bg="#4CAF50", 
            fg="white",
            padx=15, 
            pady=8,
            bd=0,
            cursor="hand2",
            command=self.guardar_datos
        )
        self.guardar_btn.pack(side=tk.LEFT, padx=10)
        
        self.cancelar_btn = tk.Button(
            btn_frame, 
            text="Cancelar", 
            font=("Arial", 11), 
            bg="#f44336", 
            fg="white",
            padx=15, 
            pady=8,
            bd=0,
            cursor="hand2",
            command=self.window.destroy
        )
        self.cancelar_btn.pack(side=tk.LEFT, padx=10)
    
    def guardar_datos(self):
        # Obtener valores de los campos
        nombre = self.nombre_entry.get().strip()
        cargo = self.cargo_combo.get()
        tipo_vehiculo = self.vehiculo_combo.get()
        placa = self.numero_placa
        marca = self.marca_entry.get().strip()
        modelo = self.modelo_entry.get().strip()
        color = self.color_entry.get().strip()
        
        # Validar campos
        if not nombre:
            messagebox.showerror("Error", "El nombre de usuario es obligatorio")
            return
        
        if not marca:
            messagebox.showerror("Error", "La marca del vehículo es obligatoria")
            return
        
        if not modelo:
            messagebox.showerror("Error", "El modelo del vehículo es obligatorio")
            return
        
        if not color:
            messagebox.showerror("Error", "El color del vehículo es obligatorio")
            return
        
        # Guardar en la base de datos
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Insertar persona
                cursor.execute("""
                    INSERT INTO personas (nombre_completo, cargo, tipo_vehiculo) 
                    VALUES (%s, %s, %s) RETURNING id
                """, (nombre, cargo, tipo_vehiculo))
                
                persona_id = cursor.fetchone()[0]
                
                # Insertar placa
                cursor.execute("""
                    INSERT INTO placas (numero_placa, persona_id, tipo_vehiculo, marca, modelo, color, estado) 
                    VALUES (%s, %s, %s, %s, %s, %s, 'Activo')
                    RETURNING id
                """, (placa, persona_id, tipo_vehiculo, marca, modelo, color))
                
                placa_id = cursor.fetchone()[0]
                
                # Registrar acceso
                cursor.execute("""
                    INSERT INTO registros_acceso (placa_id, acceso, fecha_hora_entrada) 
                    VALUES (%s, 'Entrada', CURRENT_TIMESTAMP)
                """, (placa_id,))
                
                conn.commit()
                messagebox.showinfo("Éxito", "Usuario y vehículo registrados correctamente")
                self.window.destroy()
                
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
            finally:
                conn.close()

class AppDeteccionPlacas:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Reconocimiento de Placas")
        
        # Configurar estilo
        self.estilo = ttk.Style()
        self.estilo.configure('TButton', font=('Arial', 11))
        self.estilo.configure('TLabel', font=('Arial', 11))
        self.estilo.configure('TEntry', font=('Arial', 11))
        
        # Variables
        self.cap = None
        self.frame_actual = None
        self.placa_detectada = None
        self.deteccion_activa = False
        
        # Crear widgets
        self.crear_widgets()
        
        # Iniciar cámara
        self.iniciar_camara()
        
    def crear_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.ventana, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para la imagen
        self.frame_camara = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        self.frame_camara.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.lbl_video = ttk.Label(self.frame_camara)
        self.lbl_video.pack(fill=tk.BOTH, expand=True)
        
        # Frame información
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        # Mostrar placa detectada
        ttk.Label(info_frame, text="Placa detectada: ").pack(side=tk.LEFT)
        self.lbl_placa = ttk.Label(info_frame, text="", font=('Arial', 12, 'bold'))
        self.lbl_placa.pack(side=tk.LEFT)
        
        # Estado de acceso
        self.lbl_estado = ttk.Label(main_frame, text="", font=('Arial', 22, 'bold'), foreground="red")
        self.lbl_estado.pack(pady=5)
        
        # Frame botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_autorizar = ttk.Button(
            btn_frame, 
            text="Guardar placa como autorizada", 
            command=self.abrir_registro,
            state=tk.DISABLED
        )
        self.btn_autorizar.pack(side=tk.LEFT, padx=5)
        
        self.btn_escanear = ttk.Button(
            btn_frame, 
            text="Volver a escanear", 
            command=self.iniciar_camara
        )
        self.btn_escanear.pack(side=tk.LEFT, padx=5)
    
    def iniciar_camara(self):
        self.lbl_placa.config(text="")
        self.lbl_estado.config(text="")
        self.btn_autorizar.config(state=tk.DISABLED)
        
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            
        self.deteccion_activa = True
        self.actualizar_frame()
    
    def detener_camara(self):
        self.deteccion_activa = False
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
    
    def actualizar_frame(self):
        if not self.deteccion_activa:
            return
        
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_actual = frame.copy()
            
            # Detectar placas
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 11, 17, 17)
            edged = cv2.Canny(gray, 30, 200)
            
            cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
            
            placa_encontrada = None
            
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                
                if len(approx) == 4:
                    placa_encontrada = approx
                    break
            
            if placa_encontrada is not None:
                cv2.drawContours(frame, [placa_encontrada], -1, (0, 255, 0), 3)
                
                # Extraer región de la placa
                x, y, w, h = cv2.boundingRect(placa_encontrada)
                roi = frame[y:y+h, x:x+w]
                
                # Intentar extraer texto
                texto = self.extraer_texto(roi)
                
                if texto:
                    self.placa_detectada = texto
                    self.lbl_placa.config(text=texto)
                    cv2.putText(frame, texto, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    # Verificar si la placa está autorizada
                    self.verificar_placa(texto)
            
            # Mostrar frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.lbl_video.imgtk = imgtk
            self.lbl_video.config(image=imgtk)
        
        if self.deteccion_activa:
            self.ventana.after(10, self.actualizar_frame)
    
    def extraer_texto(self, imagen):
        # Preparar imagen para OCR
        gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # OCR con pytesseract
        config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        texto = pytesseract.image_to_string(thresh, config=config)
        
        # Limpiar texto
        texto = re.sub(r'[^A-Z0-9]', '', texto)
        
        if len(texto) >= 6:
            return texto
        return None
    
    def verificar_placa(self, placa):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.estado, per.nombre_completo
                    FROM placas p
                    JOIN personas per ON p.persona_id = per.id
                    WHERE p.numero_placa = %s
                """, (placa,))
                
                resultado = cursor.fetchone()
                
                if resultado:
                    placa_id, estado, usuario = resultado
                    
                    if estado == 'Activo':
                        # Registrar acceso
                        cursor.execute("""
                            INSERT INTO registros_acceso (placa_id, acceso, fecha_hora_entrada)
                            VALUES (%s, 'Entrada', CURRENT_TIMESTAMP)
                        """, (placa_id,))
                        conn.commit()
                        
                        self.lbl_estado.config(text="ACCESO AUTORIZADO", foreground="green")
                        self.btn_autorizar.config(state=tk.DISABLED)
                    else:
                        self.lbl_estado.config(text="ACCESO DENEGADO", foreground="red")
                        self.btn_autorizar.config(state=tk.DISABLED)
                else:
                    self.lbl_estado.config(text="ACCESO DENEGADO", foreground="red")
                    self.btn_autorizar.config(state=tk.NORMAL)
                    
            except Exception as e:
                print(f"Error al verificar placa: {e}")
            finally:
                conn.close()
    
    def abrir_registro(self):
        if not self.placa_detectada:
            messagebox.showerror("Error", "No hay placa detectada para registrar")
            return
        
        # Detener la detección temporalmente
        self.deteccion_activa = False
        
        # Crear ventana de registro usando la clase mejorada
        registro = RegistroUsuarioVehiculo(self.ventana, self.placa_detectada)
        
        # Esperar a que se cierre la ventana
        self.ventana.wait_window(registro.window)
        
        # Reactivar la detección
        self.deteccion_activa = True
        self.actualizar_frame()

def main():
    ventana = tk.Tk()
    ventana.geometry("900x650")
    app = AppDeteccionPlacas(ventana)
    ventana.mainloop()

if __name__ == "__main__":
    main() 