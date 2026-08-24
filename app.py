import streamlit as st
from supabase import create_client, Client
import pandas as pd

st.set_page_config(page_title="Arqueo de Caja - Baños", page_icon="🚽", layout="wide")

# Conexión a Supabase
url = st.secrets.get("SUPABASE_URL", "")
key = st.secrets.get("SUPABASE_KEY", "")

if url and key:
    supabase: Client = create_client(url, key)
else:
    st.error("Configura las credenciales SUPABASE_URL y SUPABASE_KEY en los Secrets de Streamlit.")
    st.stop()

st.title("🚽 Arqueo de Caja - Baños")

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
        data = {
            "fecha": str(fecha),
            "monto_efectivo": efectivo,
            "monto_yape": yape,
            "total_ventas": total_ventas
        }
        res = supabase.table("rendiciones").insert(data).execute()
        st.success("¡Rendición guardada con éxito!")

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
        data_g = {
            "fecha": str(f_gasto),
            "descripcion": desc,
            "cantidad": cant,
            "costo_unitario": costo_u,
            "total_gasto": total_gasto,
            "metodo_pago": metodo
        }
        res = supabase.table("gastos").insert(data_g).execute()
        st.success("¡Gasto guardado con éxito!")

# TAB 3: DASHBOARD
with tab3:
    st.subheader("Resumen General de Caja")
    
    # Cargar datos desde Supabase
    res_rend = supabase.table("rendiciones").select("*").execute()
    res_gast = supabase.table("gastos").select("*").execute()
    
    df_rend = pd.DataFrame(res_rend.data)
    df_gast = pd.DataFrame(res_gast.data)
    
    tot_ingresos = df_rend["total_ventas"].sum() if not df_rend.empty else 0.0
    tot_gastos = df_gast["total_gasto"].sum() if not df_gast.empty else 0.0
    balance = tot_ingresos - tot_gastos
    
    # Tarjetas de Resumen Métrico
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
