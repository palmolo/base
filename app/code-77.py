import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

# Configuración de la interfaz de la página
st.set_page_config(page_title="Gestor de Base de Datos", layout="wide", page_icon="📊")

FILENAME = "base_de_datos.xlsx"

# Función para cargar o inicializar la base de datos Excel
def cargar_base():
    if os.path.exists(FILENAME):
        try:
            return pd.read_excel(FILENAME)
        except Exception:
            pass
    # Si no existe, creamos la estructura limpia
    return pd.DataFrame(columns=[
        "Fecha/Hora", "Plataforma", "Sub-plataforma", "Estado", 
        "Nº de orden", "Motivo de consulta", "Descripción", 
        "¿Solucionado?", "Nombre Cliente", "Teléfono"
    ])

def guardar_base(df):
    df.to_excel(FILENAME, index=False)

# Inicializar estados de la aplicación en la sesión
if 'df' not in st.session_state:
    st.session_state.df = cargar_base()

if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

# Listas fijas de opciones según tus instrucciones
opciones_plataforma = ["web", "Mercado libre", "locales"]
opciones_sub = ["Mateu", "Aurelius"]
opciones_estado = ["preventa", "venta en proceso", "postventa"]
opciones_motivo = ["stock", "seguimiento", "reclamo", "garantia", "cambio", "devolución", "cotización", "otro"]
opciones_solucionado = ["si", "NO", "En proceso", "derivado"]

# Función para limpiar los campos del formulario (Acción BORRAR)
def limpiar_campos():
    st.session_state.plat_key = "web"
    st.session_state.sub_key = "Mateu"
    st.session_state.est_key = "preventa"
    st.session_state.ord_key = ""
    st.session_state.mot_key = "stock"
    st.session_state.desc_key = ""
    st.session_state.sol_key = "si"
    st.session_state.nom_key = ""
    st.session_state.tel_key = ""
    st.session_state.edit_index = None

# Inicializar las claves del formulario si no existen
if 'plat_key' not in st.session_state:
    limpiar_campos()

st.title("📊 Sistema de Carga Operativa y Control de Datos")
st.markdown("---")

# División de la pantalla en dos columnas principales (Izquierda: Carga | Derecha: Control y Gráficos)
col_formulario, col_control = st.columns([1, 1.2])

with col_formulario:
    st.header("📝 Entrada de Datos")
    
    # Alerta visual si se está editando un registro existente
    if st.session_state.edit_index is not None:
        st.warning(f"⚠️ **MODO EDICIÓN ACTIVO** — Modificando fila índice: {st.session_state.edit_index}")
    
    # --- FORMULARIO DE CAMPOS ---
    plat = st.selectbox("Campo 1 > Plataforma", opciones_plataforma, key="plat_key")
    
    # Campo 1.1 condicional si elige "web"
    sub_plat = "-"
    if plat == "web":
        sub_plat = st.selectbox("Campo 1.1 > Sub-plataforma", opciones_sub, key="sub_key")
        
    est = st.selectbox("Campo 2 > Estado", opciones_estado, key="est_key")
    
    ord_num = st.text_input("Campo 3 > Nº de orden (Opcional - Máx. 20 números)", key="ord_key", max_chars=20)
    
    mot = st.selectbox("Campo 4 > Motivo de consulta", opciones_motivo, key="mot_key")
    
    desc = st.text_area("Campo 5 > Descripción breve (Máx. 800 caracteres)", key="desc_key", max_chars=800)
    
    sol = st.selectbox("Campo 6 > ¿El problema se solucionó?", opciones_solucionado, key="sol_key")
    
    nom = st.text_input("Campo 7 > Nombre del cliente", key="nom_key")
    
    tel = st.text_input("Campo 8 > Teléfono del cliente", key="tel_key")
    
    st.markdown("### Acciones de Formulario")
    c1, c2 = st.columns(2)
    
    with c1:
        # BOTÓN GUARDAR
        if st.button("💾 GUARDAR", use_container_width=True, type="primary"):
            # Validar que el campo 3 contenga solo números si fue rellenado
            if ord_num and not ord_num.isdigit():
                st.error("❌ Error: El Nº de orden debe contener únicamente caracteres numéricos.")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nuevo_registro = {
                    "Fecha/Hora": timestamp,
                    "Plataforma": plat,
                    "Sub-plataforma": sub_plat,
                    "Estado": est,
                    "Nº de orden": ord_num,
                    "Motivo de consulta": mot,
                    "Descripción": desc,
                    "¿Solucionado?": sol,
                    "Nombre Cliente": nom,
                    "Teléfono": tel
                }
                
                if st.session_state.edit_index is not None:
                    # Modo edición: Superponer la información en la fila correspondiente
                    st.session_state.df.iloc[st.session_state.edit_index] = nuevo_registro
                    st.success("¡Registro modificado y actualizado con éxito!")
                else:
                    # Modo creación: Agregar nueva fila
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nuevo_registro])], ignore_index=True)
                    st.success("¡Datos registrados exitosamente!")
                
                guardar_base(st.session_state.df)
                limpiar_campos()
                st.invalidate_pages() # Forzar actualización visual
                st.rerun()
                
    with c2:
        # BOTÓN BORRAR
        if st.button("🗑️ BORRAR", use_container_width=True):
            limpiar_campos()
            st.info("Campos en proceso limpiados correctamente.")
            st.rerun()

with col_control:
    st.header("🔍 Consultas y Reportes")
    
    # --- SECCIÓN BUSCADOR ---
    with st.expander("🔎 Herramienta de Búsqueda y Edición", expanded=True):
        search_query = st.text_input("Buscar por Nº de Orden, Nombre o Teléfono:")
        
        if 'search_df' not in st.session_state:
            st.session_state.search_df = None
            
        if st.button("🔍 BUSCAR", use_container_width=True):
            if search_query:
                df_s = st.session_state.df
                # Filtro flexible que busca coincidencia en cualquiera de los tres campos requeridos
                mask = (
                    df_s['Nº de orden'].astype(str).str.contains(search_query, case=False, na=False) |
                    df_s['Nombre Cliente'].astype(str).str.contains(search_query, case=False, na=False) |
                    df_s['Teléfono'].astype(str).str.contains(search_query, case=False, na=False)
                )
                st.session_state.search_df = df_s[mask]
            else:
                st.session_state.search_df = None
        
        # Si hay resultados de búsqueda, habilitar la edición
        if st.session_state.search_df is not None:
            if not st.session_state.search_df.empty:
                st.dataframe(st.session_state.search_df, use_container_width=True)
                
                # Mapeo de opciones para que el usuario elija cuál registro exacto editar
                opciones_edicion = {f"Fila {idx} | {row['Nombre Cliente']} - {row['Motivo de consulta']}": idx for idx, row in st.session_state.search_df.iterrows()}
                registro_sel = st.selectbox("Seleccionar el registro para EDITAR:", list(opciones_edicion.keys()))
                
                if st.button("✏️ HABILITAR EDICIÓN", use_container_width=True):
                    idx_target = opciones_edicion[registro_sel]
                    r = st.session_state.df.loc[idx_target]
                    
                    # Cargar los datos directo en los estados de los inputs del formulario
                    st.session_state.edit_index = idx_target
                    st.session_state.plat_key = r['Plataforma']
                    st.session_state.sub_key = r['Sub-plataforma'] if r['Sub-plataforma'] != "-" else "Mateu"
                    st.session_state.est_key = r['Estado']
                    st.session_state.ord_key = str(r['Nº de orden']) if pd.notna(r['Nº de orden']) else ""
                    st.session_state.mot_key = r['Motivo de consulta']
                    st.session_state.desc_key = r['Descripción']
                    st.session_state.sol_key = r['¿Solucionado?']
                    st.session_state.nom_key = r['Nombre Cliente']
                    st.session_state.tel_key = str(r['Teléfono'])
                    st.rerun()
            else:
                st.warning("No se encontraron registros que coincidan con los parámetros.")

    # --- BOTÓN DESCARGAR ---
    st.markdown("### 📥 Descarga de Archivos")
    if not st.session_state.df.empty:
        # Generar el archivo Excel en memoria para su descarga directa (.xlsx moderno compatible con Excel)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            st.session_state.df.to_excel(writer, index=False, sheet_name='Base_de_Datos')
        
        st.download_button(
            label="📥 DESCARGAR BASE DE DATOS (Excel)",
            data=buffer.getvalue(),
            file_name=f"base_datos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("La base de datos está vacía. Registrá información para habilitar la descarga.")

    # --- GRÁFICOS AL MOMENTO ---
    st.markdown("### 📊 Gráficos en Tiempo Real")
    if not st.session_state.df.empty:
        # Gráfica de motivos de consulta
        st.write("**Métricas por Motivo de Consulta:**")
        st.bar_chart(st.session_state.df['Motivo de consulta'].value_counts())
        
        # Gráfica de estado de resoluciones
        st.write("**Estado de Resoluciones generales:**")
        st.bar_chart(st.session_state.df['¿Solucionado?'].value_counts())
    else:
        st.caption("Los gráficos dinámicos se renderizarán solos a medida que incorpores registros a la base.")