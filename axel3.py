import cv2 
from ultralytics import YOLO
import easyocr
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk
import time
import os
import threading
import csv
from datetime import datetime
import re
import numpy as np
import psycopg2
from psycopg2 import sql

# Configuración de la base de datos
DB_CONFIG = {
    'dbname': 'placas',
    'user': 'postgres',  # Cambia esto a tu usuario de PostgreSQL
    'password': 'ADMIN',  # Cambia esto a tu contraseña
    'host': 'localhost',
    'port': '5432'
}

# Función para conectar a la base de datos
def conectar_bd():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos: {e}")
        return None

# Función para verificar si una placa está autorizada
def verificar_placa_autorizada(numero_placa):
    conn = conectar_bd()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM placas WHERE numero_placa = %s", (numero_placa,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return resultado is not None
    except Exception as e:
        print(f"Error al verificar placa: {e}")
        if conn:
            conn.close()
        return False

# Función para obtener el ID de una placa
def obtener_id_placa(numero_placa):
    conn = conectar_bd()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM placas WHERE numero_placa = %s", (numero_placa,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return resultado[0] if resultado else None
    except Exception as e:
        print(f"Error al obtener ID de placa: {e}")
        if conn:
            conn.close()
        return None

# Función para verificar si hay un registro de entrada sin salida para una placa
def verificar_entrada_sin_salida(placa_id):
    conn = conectar_bd()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM registros_acceso WHERE placa_id = %s AND fecha_hora_salida IS NULL AND acceso = 'Permitido' ORDER BY fecha_hora_entrada DESC LIMIT 1",
            (placa_id,)
        )
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return resultado[0] if resultado else None
    except Exception as e:
        print(f"Error al verificar entrada sin salida: {e}")
        if conn:
            conn.close()
        return None

# Función para obtener todas las placas autorizadas
def obtener_placas_autorizadas():
    conn = conectar_bd()
    if not conn:
        return set()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT numero_placa FROM placas")
        placas = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        return placas
    except Exception as e:
        print(f"Error al obtener placas autorizadas: {e}")
        if conn:
            conn.close()
        return set()

# Función para registrar entrada en la base de datos
def registrar_entrada(placa_id):
    conn = conectar_bd()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO registros_acceso (placa_id, fecha_hora_entrada, acceso) VALUES (%s, %s, %s)",
            (placa_id, datetime.now(), "Permitido")
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al registrar entrada: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

# Función para registrar salida en la base de datos
def registrar_salida(registro_id):
    conn = conectar_bd()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE registros_acceso SET fecha_hora_salida = %s WHERE id = %s",
            (datetime.now(), registro_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al registrar salida: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

# Función para registrar acceso denegado
def registrar_acceso_denegado(numero_placa, es_entrada=True):
    conn = conectar_bd()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        # Intentar obtener el ID de la placa (podría no existir)
        cursor.execute("SELECT id FROM placas WHERE numero_placa = %s", (numero_placa,))
        resultado = cursor.fetchone()
        
        if resultado:
            placa_id = resultado[0]
            # Registrar el acceso denegado
            cursor.execute(
                "INSERT INTO registros_acceso (placa_id, fecha_hora_entrada, acceso) VALUES (%s, %s, %s)",
                (placa_id, datetime.now(), "Denegado")
            )
            conn.commit()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al registrar acceso denegado: {e}")
        if conn:
            conn.close()

# Crear carpetas necesarias
os.makedirs("resultados", exist_ok=True)

# Crear lector EasyOCR
reader = easyocr.Reader(['en', 'es'])

# Cargar modelo YOLO personalizado
model = YOLO('modelo/LP-detection.pt')

# Variables globales
frame_actual = None
frame_dibujado = None
deteccion_activa = True
placa_detectada = None
placa_texto = None
placa_img = None
placas_permitidas = obtener_placas_autorizadas()
es_entrada = True  # Variable para controlar si es entrada o salida
cap = None

def limpiar_texto_placa(texto):
    """
    Limpia y corrige el texto de la placa con manejo específico para placas hondureñas
    """
    if not texto:
        return texto

    # Eliminar espacios y caracteres no deseados
    texto = texto.strip().upper().replace(" ", "")
    
    # Eliminar caracteres especiales y puntuación
    texto = re.sub(r'[^\w]', '', texto)
    
    # Si el texto no tiene al menos 6 caracteres, no es una placa válida
    if len(texto) < 6:
        return texto
    
    # Separar la parte de letras y números
    parte_letras = texto[:3]
    parte_numeros = texto[3:]
    
    # Correcciones específicas para la parte de letras
    correcciones_letras = {
        '0': 'O',  # En la parte de letras, 0 siempre debe ser O
        '1': 'I',
        '2': 'Z',
        '8': 'B'
    }
    
    # Correcciones específicas para la parte numérica
    correcciones_numeros = {
        'O': '0',  # En la parte numérica, O siempre debe ser 0
        'I': '1',
        'Z': '2',
        'S': '5',
        'G': '6',
        'T': '7',
        'B': '8',
        'D': '0',
        'Q': '0',
        'U': '0'
    }
    
    # Aplicar correcciones a cada parte
    for original, correccion in correcciones_letras.items():
        parte_letras = parte_letras.replace(original, correccion)
    
    for original, correccion in correcciones_numeros.items():
        parte_numeros = parte_numeros.replace(original, correccion)
    
    # Verificar que la parte de letras solo contenga letras
    if not parte_letras.isalpha():
        return texto
    
    # Verificar que la parte numérica solo contenga números
    if not parte_numeros.isdigit():
        return texto
    
    return parte_letras + parte_numeros

def validar_formato_placa(texto):
    """
    Verifica si el texto tiene formato de placa de Honduras (3 letras + 4 números)
    """
    # Verificar longitud exacta (7 caracteres)
    if len(texto) != 7:
        return False
    
    # Verificar que los primeros 3 caracteres sean letras
    if not texto[:3].isalpha():
        return False
    
    # Verificar que los últimos 4 caracteres sean números
    if not texto[3:].isdigit():
        return False
    
    # Verificar formato completo
    patron_placa = r'^[A-Z]{3}\d{4}$'
    return re.match(patron_placa, texto) is not None

class FormularioRegistro(tk.Toplevel):
    def __init__(self, parent, numero_placa):
        super().__init__(parent)
        self.title("Registro de Usuario")
        self.geometry("500x580")
        self.configure(bg="#f5f5f5")
        self.numero_placa = numero_placa
        
        # Hacer que esta ventana sea modal
        self.transient(parent)
        self.grab_set()
        
        self.crear_widgets()
        
        # Centrar la ventana
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def crear_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self, padx=25, pady=20, bg="#f5f5f5")
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
            command=self.destroy
        )
        self.cancelar_btn.pack(side=tk.LEFT, padx=10)
    
    def guardar_datos(self):
        # Obtener valores de los campos
        nombre = self.nombre_entry.get().strip()
        cargo = self.cargo_combo.get()
        tipo_vehiculo = self.vehiculo_combo.get()
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
        conn = conectar_bd()
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
                """, (self.numero_placa, persona_id, tipo_vehiculo, marca, modelo, color))
                
                placa_id = cursor.fetchone()[0]
                
                # Registrar acceso
                cursor.execute("""
                    INSERT INTO registros_acceso (placa_id, acceso, fecha_hora_entrada) 
                    VALUES (%s, 'Entrada', CURRENT_TIMESTAMP)
                """, (placa_id,))
            
            conn.commit()
                messagebox.showinfo("Éxito", "Usuario y vehículo registrados correctamente")
            self.destroy()
            
        except Exception as e:
            conn.rollback()
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
            finally:
            conn.close()

def procesar_deteccion_placa(numero_placa):
    """
    Procesa la detección de una placa, determinando si es entrada o salida
    y registrando el acceso correspondiente
    """
    global es_entrada
    
    # Verificar si la placa está autorizada
    if numero_placa in placas_permitidas:
        placa_id = obtener_id_placa(numero_placa)
        if not placa_id:
            return "No", "Error al obtener ID de placa"
        
        # Verificar si hay una entrada sin salida (para determinar si es entrada o salida)
        registro_id = verificar_entrada_sin_salida(placa_id)
        
        if registro_id:
            # Es una salida
            es_entrada = False
            if registrar_salida(registro_id):
                return "Sí", "salir"
            else:
                return "No", "Error al registrar salida"
        else:
            # Es una entrada
            es_entrada = True
            if registrar_entrada(placa_id):
                return "Sí", "entrar"
            else:
                return "No", "Error al registrar entrada"
    else:
        # Placa no autorizada
        registrar_acceso_denegado(numero_placa)
        return "No", "Placa no autorizada"

def reiniciar_deteccion():
    """Reinicia la detección de placas"""
    global deteccion_activa, placa_detectada, placa_texto, placa_img, cap
    deteccion_activa = True
    placa_detectada = None
    placa_texto = None
    placa_img = None
    etiqueta_placa.config(text="")
    etiqueta_estado.config(text="Esperando detección...", fg="black")
    frame_botones.pack_forget()
    frame_boton_continuar.pack_forget()
    
    # Iniciar nuevo hilo de detección
    hilo_deteccion = threading.Thread(target=detectar_placas, daemon=True)
    hilo_deteccion.start()

def liberar_camara():
    """Libera los recursos de la cámara"""
    global cap
    if cap is not None:
        cap.release()
        cap = None

def abrir_formulario_registro():
    """Abre el formulario para registrar un nuevo usuario con la placa detectada"""
    if placa_texto and validar_formato_placa(placa_texto):
        FormularioRegistro(ventana, placa_texto)
    else:
        messagebox.showerror("Error", "No hay una placa válida para registrar")

def detectar_placas():
    """Función principal para detectar placas en el video"""
    global frame_dibujado, deteccion_activa, placa_detectada, placa_texto, placa_img, frame_actual, cap
    
    cap = cv2.VideoCapture(0)
    
    while True:
        if not deteccion_activa:
            # Si la detección está inactiva, liberar la cámara y salir del bucle
            liberar_camara()
            break
            
        ret, frame = cap.read()
        if not ret:
            continue
            
        frame_actual = frame.copy()
        frame_dibujado = frame.copy()
        
        if deteccion_activa:
            results = model(frame)
            
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    if conf < 0.5:
                        continue
                    
                    # Dibujar rectángulo
                    cv2.rectangle(frame_dibujado, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Recorte de la placa
                    placa_img_temp = frame[y1:y2, x1:x2]
                    
                    if placa_img_temp.size == 0:
                        continue
                    
                    # OCR
                    resultado_ocr = reader.readtext(placa_img_temp)
                    for (_, texto_detectado, prob) in resultado_ocr:
                        if prob > 0.4:
                            texto = texto_detectado.strip().upper().replace(" ", "")
                            # Ignorar si el texto es HONDURAS o CENTROAMÉRICA
                            if "HONDURAS" not in texto and "CENTROAM" not in texto:
                                # Limpiar y validar el texto detectado
                                texto_limpio = limpiar_texto_placa(texto)
                                if validar_formato_placa(texto_limpio):
                                    print("Texto detectado:", texto_limpio)
                                    
                                    # Guardar la información de la placa detectada
                                    placa_detectada = True
                                    placa_texto = texto_limpio
                                    placa_img = placa_img_temp.copy()
                                    
                                    # Procesar la detección (determinar si es entrada o salida)
                                    acceso, accion = procesar_deteccion_placa(texto_limpio)
                                    
                                    # Detener la detección y la cámara
                                    deteccion_activa = False
                                    liberar_camara()
                                    
                                    # Actualizar la interfaz en el hilo principal
                                    ventana.after(0, lambda t=texto_limpio, a=acceso, ac=accion: 
                                                 mostrar_resultado_deteccion(t, a, ac))
                                    
                                    # Guardar imagen de la placa
                                    if placa_img is not None:
                                        nombre_archivo = f"resultados/placa_{int(time.time())}.jpg"
                                        cv2.imwrite(nombre_archivo, placa_img)
                                    
                                    break
        
        time.sleep(0.03)  # Pequeña pausa para reducir uso de CPU

def mostrar_resultado_deteccion(texto, acceso, accion):
    """Muestra el resultado de la detección en la interfaz"""
    etiqueta_placa.config(text=f"Placa detectada: {texto}")
    
    if acceso == "Sí":
        if accion == "entrar":
            etiqueta_estado.config(text="ACCESO PERMITIDO PARA ENTRAR", fg="green")
        else:
            etiqueta_estado.config(text="ACCESO PERMITIDO PARA SALIR", fg="green")
        
        # Mostrar botón para continuar
        frame_boton_continuar.pack(pady=10)
        frame_botones.pack_forget()
    else:
        if accion == "Placa no autorizada":
            etiqueta_estado.config(text="ACCESO DENEGADO", fg="red")
            # Mostrar botones de opciones para registrar o volver a escanear
            frame_botones.pack(pady=10)
            frame_boton_continuar.pack_forget()
        else:
            etiqueta_estado.config(text=f"ERROR: {accion}", fg="red")
            # Mostrar botón para continuar
            frame_boton_continuar.pack(pady=10)
            frame_botones.pack_forget()

def mostrar_video():
    """Actualiza la imagen de video en la interfaz"""
    if frame_dibujado is not None:
        # Redimensionar el frame para que se ajuste a la ventana
        altura, ancho = frame_dibujado.shape[:2]
        max_ancho = 640
        if ancho > max_ancho:
            escala = max_ancho / ancho
            nuevo_ancho = int(ancho * escala)
            nueva_altura = int(altura * escala)
            frame_redimensionado = cv2.resize(frame_dibujado, (nuevo_ancho, nueva_altura))
        else:
            frame_redimensionado = frame_dibujado
            
        frame_rgb = cv2.cvtColor(frame_redimensionado, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        etiqueta_video.imgtk = imgtk
        etiqueta_video.configure(image=imgtk)
    ventana.after(30, mostrar_video)

# Interfaz Tkinter
ventana = tk.Tk()
ventana.title("Reconocimiento de Placas")
ventana.geometry("800x700")

# Frame para el video
frame_video = tk.Frame(ventana)
frame_video.pack(pady=10)

etiqueta_video = tk.Label(frame_video)
etiqueta_video.pack()

# Etiqueta para mostrar la placa detectada
etiqueta_placa = tk.Label(ventana, text="", font=("Arial", 16))
etiqueta_placa.pack(pady=10)

# Etiqueta para mostrar el estado de acceso
etiqueta_estado = tk.Label(ventana, text="Esperando detección...", font=("Arial", 24))
etiqueta_estado.pack(pady=10)

# Frame para los botones de opciones (cuando se deniega el acceso)
frame_botones = tk.Frame(ventana)
# No empaquetamos el frame aquí, se mostrará solo cuando sea necesario

# Botones de opciones
btn_guardar = tk.Button(frame_botones, text="Guardar placa como autorizada", 
                        font=("Arial", 14), bg="#4CAF50", fg="white",
                        command=abrir_formulario_registro)
btn_guardar.pack(side=tk.LEFT, padx=10)

btn_escanear = tk.Button(frame_botones, text="Volver a escanear", 
                         font=("Arial", 14), bg="#2196F3", fg="white",
                         command=reiniciar_deteccion)
btn_escanear.pack(side=tk.LEFT, padx=10)

# Frame para el botón de continuar (cuando se permite el acceso)
frame_boton_continuar = tk.Frame(ventana)
# No empaquetamos el frame aquí, se mostrará solo cuando sea necesario

# Botón para continuar después de un acceso permitido
btn_continuar = tk.Button(frame_boton_continuar, text="Continuar", 
                         font=("Arial", 14), bg="#2196F3", fg="white",
                         command=reiniciar_deteccion)
btn_continuar.pack()

# Iniciar hilo de detección
hilo_deteccion = threading.Thread(target=detectar_placas, daemon=True)
hilo_deteccion.start()

# Mostrar GUI
mostrar_video()
ventana.mainloop()
