import streamlit as st
from supabase import create_client, Client
import pandas as pd

st.set_page_config(page_title="Arqueo de Caja - Baños", page_icon="🚽", layout="wide")

# Obtener credenciales de los Secrets
url = st.secrets.get("SUPABASE_URL", "")
key = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_connection():
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_connection()

st.title("🚽 Arqueo de Caja - Baños")

if not supabase:
    st.error("⚠️ Faltan configurar las credenciales de Supabase en los Secrets.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["💵 Rendición / Cobro", "💸 Registrar Gasto", "📊 Dashboard y Reportes"])

# TAB 1: RENDICIÓN
with tab1:
    st.subheader("Ingreso Diario")
    fecha = st.date_input("Fecha", key="f_ing")
    efectivo = st.number_input("Monto Efectivo (S/)", min_value=0.0, step=0.50, value=0.0)
    yape = st.number_input("Monto Yape (S/)", min_value=0.0, step=0.50, value=0.0)
    total_ventas = efectivo + yape
    st.write(f"**Total Ventas:** S/ {total_ventas:.2f}")

    if st.button("Guardar Rendición", type="primary"):
        try:
            data = {
                "fecha": str(fecha),
                "monto_efectivo": efectivo,
                "monto_yape": yape,
                "total_ventas": total_ventas
            }
            supabase.table("rendicion_caja").insert(data).execute()
            st.success("¡Rendición guardada con éxito!")
        except Exception as e:
            st.error(f"Error al guardar: {e}")

# TAB 2: GASTOS
with tab2:
    st.subheader("Registro de Gasto")
    f_gasto = st.date_input("Fecha Gasto", key="f_gas")
    desc = st.text_input("Descripción / Producto")
    cant = st.number_input("Cantidad", min_value=1.0, step=1.0, value=1.0)
    costo_u = st.number_input("Costo Unitario (S/)", min_value=0.0, step=0.50, value=0.0)
    total_gasto = cant * costo_u
    st.write(f"**Total Gasto:** S/ {total_gasto:.2f}")
    metodo = st.selectbox("Método de Pago", ["EFECTIVO", "YAPE", "TRANSFERENCIA"])

    if st.button("Guardar Gasto"):
        try:
            data_g = {
                "fecha": str(f_gasto),
                "descripcion": desc,
                "cantidad": cant,
                "costo_unitario": costo_u,
                "total_gasto": total_gasto,
                "metodo_pago": metodo
            }
            supabase.table("gastos").insert(data_g).execute()
            st.success("¡Gasto guardado con éxito!")
        except Exception as e:
            st.error(f"Error al guardar: {e}")

# TAB 3: DASHBOARD
with tab3:
    st.subheader("Resumen General de Caja")
    
    try:
        res_rend = supabase.table("rendicion_caja").select("*").execute()
        res_gast = supabase.table("gastos").select("*").execute()
        
        df_rend = pd.DataFrame(res_rend.data) if res_rend.data else pd.DataFrame()
        df_gast = pd.DataFrame(res_gast.data) if res_gast.data else pd.DataFrame()
        
        tot_ingresos = df_rend["total_ventas"].sum() if not df_rend.empty and "total_ventas" in df_rend.columns else 0.0
        tot_gastos = df_gast["total_gasto"].sum() if not df_gast.empty and "total_gasto" in df_gast.columns else 0.0
        balance = tot_ingresos - tot_gastos
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Ingresos", f"S/ {tot_ingresos:.2f}")
        col2.metric("Total Gastos", f"S/ {tot_gastos:.2f}")
        col3.metric("Balance / Ganancia", f"S/ {balance:.2f}")
        
        st.divider()
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("### Historial de Rendiciones")
            if not df_rend.empty:
                st.dataframe(df_rend, use_container_width=True)
            else:
                st.info("No hay rendiciones registradas.")
                
        with col_b:
            st.write("### Historial de Gastos")
            if not df_gast.empty:
                st.dataframe(df_gast, use_container_width=True)
            else:
                st.info("No hay gastos registrados.")
    except Exception as e:
        st.warning(f"No se pudieron cargar las tablas del Dashboard. Verifica la conexión: {e}")
