from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2 import sql
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

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

def verificar_y_actualizar_tablas():
    """Verifica y actualiza la estructura de las tablas sin perder datos"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si las tablas existen
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'personas'
            );
        """)
        existe_personas = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'placas'
            );
        """)
        existe_placas = cursor.fetchone()[0]
        
        # Crear tabla personas si no existe
        if not existe_personas:
            print("Creando tabla personas...")
            cursor.execute("""
                CREATE TABLE personas (
                    id SERIAL PRIMARY KEY,
                    nombre_completo VARCHAR(100) NOT NULL,
                    cargo VARCHAR(50),
                    tipo_vehiculo VARCHAR(50),
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Verificar y añadir columnas faltantes en personas
            print("Verificando columnas de tabla personas...")
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'personas';
            """)
            columnas_existentes = [row[0] for row in cursor.fetchall()]
            
            if 'cargo' not in columnas_existentes:
                cursor.execute("ALTER TABLE personas ADD COLUMN cargo VARCHAR(50);")
                print("Añadida columna cargo a personas")
            
            if 'tipo_vehiculo' not in columnas_existentes:
                cursor.execute("ALTER TABLE personas ADD COLUMN tipo_vehiculo VARCHAR(50);")
                print("Añadida columna tipo_vehiculo a personas")
            
            if 'fecha_registro' not in columnas_existentes:
                cursor.execute("ALTER TABLE personas ADD COLUMN fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                print("Añadida columna fecha_registro a personas")
        
        # Crear o actualizar tabla placas
        if not existe_placas:
            print("Creando tabla placas...")
            cursor.execute("""
                CREATE TABLE placas (
                    id SERIAL PRIMARY KEY,
                    numero_placa VARCHAR(20) NOT NULL,
                    persona_id INTEGER REFERENCES personas(id),
                    tipo_vehiculo VARCHAR(50),
                    marca VARCHAR(100),
                    modelo VARCHAR(100),
                    color VARCHAR(50),
                    estado VARCHAR(20) DEFAULT 'Activo',
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Verificar y añadir columnas faltantes en placas
            print("Verificando columnas de tabla placas...")
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'placas';
            """)
            columnas_existentes = [row[0] for row in cursor.fetchall()]
            
            if 'marca' not in columnas_existentes:
                cursor.execute("ALTER TABLE placas ADD COLUMN marca VARCHAR(100);")
                print("Añadida columna marca a placas")
            
            if 'modelo' not in columnas_existentes:
                cursor.execute("ALTER TABLE placas ADD COLUMN modelo VARCHAR(100);")
                print("Añadida columna modelo a placas")
            
            if 'color' not in columnas_existentes:
                cursor.execute("ALTER TABLE placas ADD COLUMN color VARCHAR(50);")
                print("Añadida columna color a placas")
            
            if 'estado' not in columnas_existentes:
                cursor.execute("ALTER TABLE placas ADD COLUMN estado VARCHAR(20) DEFAULT 'Activo';")
                print("Añadida columna estado a placas")
            
            if 'fecha_registro' not in columnas_existentes:
                cursor.execute("ALTER TABLE placas ADD COLUMN fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                print("Añadida columna fecha_registro a placas")
        
        # Verificar tabla registros_acceso
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'registros_acceso'
            );
        """)
        existe_registros = cursor.fetchone()[0]
        
        if not existe_registros:
            print("Creando tabla registros_acceso...")
            cursor.execute("""
                CREATE TABLE registros_acceso (
                    id SERIAL PRIMARY KEY,
                    placa_id INTEGER REFERENCES placas(id),
                    fecha_hora_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_hora_salida TIMESTAMP,
                    acceso VARCHAR(20)
                )
            """)
        
        conn.commit()
        print("Verificación y actualización de tablas completada exitosamente")
        return True
    except Exception as e:
        print(f"Error al verificar/actualizar tablas: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Verificar y actualizar tablas al arrancar
verificar_y_actualizar_tablas()

def get_user_id_by_name(cursor, nombre_completo):
    """Obtiene el ID de un usuario por su nombre completo"""
    cursor.execute("""
        SELECT id FROM personas 
        WHERE nombre_completo = %s
    """, (nombre_completo,))
    result = cursor.fetchone()
    return result[0] if result else None

# Rutas para el Dashboard
@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener estadísticas del día
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Total de accesos hoy
        cursor.execute("""
            SELECT COUNT(*) FROM registros_acceso 
            WHERE DATE(fecha_hora_entrada) = %s
        """, (today,))
        total_accesos = cursor.fetchone()[0]
        
        # Total de entradas hoy
        cursor.execute("""
            SELECT COUNT(*) FROM registros_acceso 
            WHERE DATE(fecha_hora_entrada) = %s AND acceso = 'Entrada'
        """, (today,))
        total_entradas = cursor.fetchone()[0]
        
        # Total de salidas hoy
        cursor.execute("""
            SELECT COUNT(*) FROM registros_acceso 
            WHERE DATE(fecha_hora_salida) = %s AND acceso = 'Permitido'
        """, (today,))
        total_salidas = cursor.fetchone()[0]
        
        # Total de denegados hoy
        cursor.execute("""
            SELECT COUNT(*) FROM registros_acceso 
            WHERE DATE(fecha_hora_entrada) = %s 
            AND acceso = 'Denegado'
            AND fecha_hora_salida IS NULL
        """, (today,))
        total_denegados = cursor.fetchone()[0]

        # Accesos por tipo de usuario
        cursor.execute("""
            SELECT p.cargo, COUNT(*) as total
            FROM registros_acceso ra
            JOIN placas pl ON ra.placa_id = pl.id
            JOIN personas p ON pl.persona_id = p.id
            WHERE DATE(ra.fecha_hora_entrada) = %s
            GROUP BY p.cargo
        """, (today,))
        accesos_por_tipo = cursor.fetchall()

        # Inicializar contadores
        total_estudiantes = 0
        total_docentes = 0
        total_administrativos = 0
        total_visitantes = 0

        # Procesar resultados
        for tipo, total in accesos_por_tipo:
            if tipo == 'Estudiante':
                total_estudiantes = total
            elif tipo == 'Docente':
                total_docentes = total
            elif tipo == 'Administrativo':
                total_administrativos = total
            elif tipo == 'Visitante':
                total_visitantes = total
        
        return jsonify({
            'total_accesos': total_accesos,
            'total_entradas': total_entradas,
            'total_salidas': total_salidas,
            'total_denegados': total_denegados,
            'total_estudiantes': total_estudiantes,
            'total_docentes': total_docentes,
            'total_administrativos': total_administrativos,
            'total_visitantes': total_visitantes
        })
        
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rutas para Usuarios
@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Consulta modificada para manejar casos donde no hay placa asociada
        cursor.execute("""
            SELECT 
                p.nombre_completo,
                p.cargo,
                p.tipo_vehiculo,
                COALESCE(pl.numero_placa, '') as placa,
                COALESCE(pl.estado, 'Sin placa') as estado,
                p.fecha_registro
            FROM personas p
            LEFT JOIN placas pl ON p.id = pl.persona_id
            ORDER BY p.fecha_registro DESC
        """)
        
        usuarios = [
            {
                'nombre': row[0],
                'tipo': row[1] or 'No especificado',
                'vehiculo': row[2] or 'No especificado',
                'placa': row[3],
                'estado': row[4],
                'fecha_registro': row[5].strftime('%d/%m/%Y') if row[5] else ''
            }
            for row in cursor.fetchall()
        ]
        
        return jsonify(usuarios)
        
    except Exception as e:
        print(f"Error al obtener usuarios: {str(e)}")
        return jsonify({'error': f'Error al obtener usuarios: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# Rutas para Placas
@app.route('/api/placas', methods=['GET', 'POST'])
def placas():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            data = request.json
            
            # Validación de campos requeridos
            campos_requeridos = ['placa', 'usuario', 'tipoVehiculo', 'marca', 'modelo', 'color']
            for campo in campos_requeridos:
                if not data.get(campo):
                    return jsonify({'error': f'El campo {campo} es requerido'}), 400
            
            # Obtener el ID del usuario o crear uno nuevo
            usuario_id = get_user_id_by_name(cursor, data['usuario'])
            
            if not usuario_id:
                try:
                    # Crear nuevo usuario
                    cursor.execute("""
                        INSERT INTO personas (
                            nombre_completo,
                            cargo,
                            tipo_vehiculo
                        ) VALUES (%s, %s, %s)
                        RETURNING id
                    """, (
                        data['usuario'],
                        data.get('cargo', 'Visitante'),
                        data['tipoVehiculo']
                    ))
                    usuario_id = cursor.fetchone()[0]
                except Exception as e:
                    print(f"Error al crear usuario: {str(e)}")
                    return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500
            
            try:
                # Insertar la nueva placa con todos los campos
                cursor.execute("""
                    INSERT INTO placas (
                        numero_placa, 
                        persona_id, 
                        tipo_vehiculo, 
                        marca,
                        modelo,
                        color,
                        estado,
                        fecha_registro
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'Activo', CURRENT_TIMESTAMP)
                    RETURNING id
                """, (
                    data['placa'],
                    usuario_id,
                    data['tipoVehiculo'],
                    data['marca'],
                    data['modelo'],
                    data['color']
                ))
                
                placa_id = cursor.fetchone()[0]
                conn.commit()
                
                # Registrar el acceso automáticamente
                cursor.execute("""
                    INSERT INTO registros_acceso (
                        placa_id,
                        acceso,
                        fecha_hora_entrada
                    ) VALUES (%s, 'Entrada', CURRENT_TIMESTAMP)
                    RETURNING id
                """, (placa_id,))
                
                acceso_id = cursor.fetchone()[0]
                conn.commit()
                
                return jsonify({
                    'message': 'Placa y acceso registrados exitosamente',
                    'placa_id': placa_id,
                    'acceso_id': acceso_id,
                    'usuario_id': usuario_id
                }), 201
            except Exception as e:
                print(f"Error al crear placa: {str(e)}")
                return jsonify({'error': f'Error al crear placa: {str(e)}'}), 500
        
        else:  # GET
            try:
                cursor.execute("""
                    SELECT 
                        pl.id,
                        pl.numero_placa,
                        p.nombre_completo,
                        pl.tipo_vehiculo,
                        pl.marca,
                        pl.modelo,
                        pl.color,
                        pl.estado,
                        pl.fecha_registro,
                        p.cargo
                    FROM placas pl
                    JOIN personas p ON pl.persona_id = p.id
                    ORDER BY pl.fecha_registro DESC
                """)
                
                placas = [
                    {
                        'id': row[0],
                        'placa': row[1],
                        'usuario': row[2],
                        'tipo_vehiculo': row[3],
                        'marca': row[4],
                        'modelo': row[5],
                        'color': row[6],
                        'estado': row[7],
                        'fecha_registro': row[8].strftime('%d/%m/%Y %H:%M') if row[8] else '',
                        'cargo': row[9]
                    }
                    for row in cursor.fetchall()
                ]
                
                return jsonify(placas)
            except Exception as e:
                print(f"Error al obtener placas: {str(e)}")
                return jsonify({'error': f'Error al obtener placas: {str(e)}'}), 500
        
    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/placas/<int:placa_id>', methods=['PUT', 'DELETE'])
def placa_individual(placa_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        if request.method == 'PUT':
            data = request.json
            
            # Validación de campos requeridos
            campos_requeridos = ['placa', 'usuario', 'tipoVehiculo', 'marca', 'modelo', 'color']
            for campo in campos_requeridos:
                if not data.get(campo):
                    return jsonify({'error': f'El campo {campo} es requerido'}), 400
            
            # Obtener el ID del usuario o crear uno nuevo
            usuario_id = get_user_id_by_name(cursor, data['usuario'])
            
            if not usuario_id:
                try:
                    # Crear nuevo usuario
                    cursor.execute("""
                        INSERT INTO personas (
                            nombre_completo,
                            cargo,
                            tipo_vehiculo
                        ) VALUES (%s, %s, %s)
                        RETURNING id
                    """, (
                        data['usuario'],
                        data.get('cargo', 'Visitante'),
                        data['tipoVehiculo']
                    ))
                    usuario_id = cursor.fetchone()[0]
                except Exception as e:
                    print(f"Error al crear usuario: {str(e)}")
                    return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500
            
            try:
                # Actualizar la placa
                cursor.execute("""
                    UPDATE placas SET
                        numero_placa = %s,
                        persona_id = %s,
                        tipo_vehiculo = %s,
                        marca = %s,
                        modelo = %s,
                        color = %s
                    WHERE id = %s
                    RETURNING id
                """, (
                    data['placa'],
                    usuario_id,
                    data['tipoVehiculo'],
                    data['marca'],
                    data['modelo'],
                    data['color'],
                    placa_id
                ))
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'Placa no encontrada'}), 404
                
                conn.commit()
                return jsonify({'message': 'Placa actualizada exitosamente'}), 200
                
            except Exception as e:
                print(f"Error al actualizar placa: {str(e)}")
                return jsonify({'error': f'Error al actualizar placa: {str(e)}'}), 500
        
        elif request.method == 'DELETE':
            try:
                # Verificar si la placa existe
                cursor.execute("SELECT id FROM placas WHERE id = %s", (placa_id,))
                if not cursor.fetchone():
                    return jsonify({'error': 'Placa no encontrada'}), 404
                
                # Primero eliminar los registros de acceso relacionados
                cursor.execute("DELETE FROM registros_acceso WHERE placa_id = %s", (placa_id,))
                
                # Luego eliminar la placa
                cursor.execute("DELETE FROM placas WHERE id = %s", (placa_id,))
                conn.commit()
                
                return jsonify({'message': 'Placa eliminada exitosamente'}), 200
                
            except Exception as e:
                print(f"Error al eliminar placa: {str(e)}")
                return jsonify({'error': f'Error al eliminar placa: {str(e)}'}), 500
    
    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rutas para Accesos
@app.route('/api/accesos', methods=['GET', 'POST'])
def get_accesos():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            data = request.json
            placa_id = data.get('placa_id')
            tipo_acceso = data.get('acceso', 'Entrada')
            
            # Verificar si la placa existe y está activa
            cursor.execute("""
                SELECT estado FROM placas WHERE id = %s
            """, (placa_id,))
            resultado = cursor.fetchone()
            
            if not resultado:
                return jsonify({'error': 'Placa no encontrada'}), 404
            
            if resultado[0] != 'Activo':
                return jsonify({'error': 'La placa no está activa'}), 400
            
            # Registrar el acceso
            cursor.execute("""
                INSERT INTO registros_acceso (
                    placa_id, 
                    acceso,
                    fecha_hora_entrada
                ) VALUES (%s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (placa_id, tipo_acceso))
            
            acceso_id = cursor.fetchone()[0]
            conn.commit()
            
            return jsonify({
                'message': 'Acceso registrado exitosamente',
                'id': acceso_id
            }), 201
        
        # GET - Obtener lista de accesos con información detallada
        cursor.execute("""
            SELECT 
                p.nombre_completo,
                pl.numero_placa,
                p.cargo,
                pl.marca,
                pl.modelo,
                pl.color,
                r.fecha_hora_entrada,
                r.fecha_hora_salida,
                r.acceso
            FROM registros_acceso r
            JOIN placas pl ON r.placa_id = pl.id
            JOIN personas p ON pl.persona_id = p.id
            ORDER BY r.fecha_hora_entrada DESC
        """)
        
        accesos = [
            {
                'usuario': row[0],
                'placa': row[1],
                'tipo': row[2],
                'marca': row[3],
                'modelo': row[4],
                'color': row[5],
                'entrada': row[6].strftime('%d/%m/%Y, %H:%M'),
                'salida': row[7].strftime('%d/%m/%Y, %H:%M') if row[7] else None,
                'estado': row[8]
            }
            for row in cursor.fetchall()
        ]
        
        return jsonify(accesos)
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Ruta para estadísticas detalladas
@app.route('/api/estadisticas/detalladas')
def get_estadisticas_detalladas():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Estadísticas por tipo de vehículo
        cursor.execute("""
            SELECT tipo_vehiculo, COUNT(*) as total
            FROM placas
            WHERE estado = 'Activo'
            GROUP BY tipo_vehiculo
            ORDER BY total DESC
        """)
        vehiculos_por_tipo = [
            {
                'tipo': row[0] or 'No especificado',
                'total': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        # Accesos por mes (últimos 6 meses)
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', fecha_hora_entrada) as mes,
                COUNT(*) as total
            FROM registros_acceso
            WHERE fecha_hora_entrada >= NOW() - INTERVAL '6 months'
            GROUP BY mes
            ORDER BY mes ASC
        """)
        accesos_por_mes = [
            {
                'mes': row[0].strftime('%B %Y'),
                'total': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        # Distribución de accesos por hora del día
        cursor.execute("""
            SELECT 
                EXTRACT(HOUR FROM fecha_hora_entrada) as hora,
                COUNT(*) as total
            FROM registros_acceso
            WHERE fecha_hora_entrada >= NOW() - INTERVAL '30 days'
            GROUP BY hora
            ORDER BY hora ASC
        """)
        accesos_por_hora = [
            {
                'hora': f"{int(row[0]):02d}:00",
                'total': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        # Estadísticas de accesos por tipo
        cursor.execute("""
            SELECT 
                acceso,
                COUNT(*) as total
            FROM registros_acceso
            WHERE fecha_hora_entrada >= NOW() - INTERVAL '30 days'
            GROUP BY acceso
        """)
        distribucion_accesos = [
            {
                'tipo': row[0],
                'total': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        # Top 5 usuarios con más accesos
        cursor.execute("""
            SELECT 
                p.nombre_completo,
                COUNT(*) as total_accesos
            FROM registros_acceso r
            JOIN placas pl ON r.placa_id = pl.id
            JOIN personas p ON pl.persona_id = p.id
            WHERE r.fecha_hora_entrada >= NOW() - INTERVAL '30 days'
            GROUP BY p.nombre_completo
            ORDER BY total_accesos DESC
            LIMIT 5
        """)
        top_usuarios = [
            {
                'usuario': row[0],
                'total': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        return jsonify({
            'vehiculos_por_tipo': vehiculos_por_tipo,
            'accesos_por_mes': accesos_por_mes,
            'accesos_por_hora': accesos_por_hora,
            'distribucion_accesos': distribucion_accesos,
            'top_usuarios': top_usuarios
        })
        
    except Exception as e:
        print(f"Error al obtener estadísticas detalladas: {e}")
        return jsonify({'error': 'Error al obtener estadísticas detalladas'}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000) 