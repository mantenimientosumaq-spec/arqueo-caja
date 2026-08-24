import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# Configuración principal de la aplicación
st.set_page_config(
    page_title="Arqueo de Caja - Baños",
    page_icon="🚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Conexión con Supabase desde Secrets
url = st.secrets.get("SUPABASE_URL", "")
key = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_connection():
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_connection()

st.title("🚽 Sistema de Arqueo de Caja - Baños")

if not supabase:
    st.error("⚠️ No se encontraron las credenciales de Supabase. Configúralas en st.secrets.")
    st.stop()

# Estructura principal en pestañas
tab1, tab2, tab3 = st.tabs(["💵 Rendición / Cobro", "💸 Registrar Gasto", "📊 Dashboard y Saldos"])

# ==========================================
# TAB 1: RENDICIÓN Y COBROS DIARIOS
# ==========================================
with tab1:
    st.subheader("Registrar Rendición Diaria")
    
    col_f, col_e, col_y = st.columns(3)
    with col_f:
        fecha_ing = st.date_input("Fecha de Registro", key="f_ing")
    with col_e:
        efectivo_ing = st.number_input("Monto Efectivo (S/)", min_value=0.0, step=0.50, value=0.0)
    with col_y:
        yape_ing = st.number_input("Monto Yape (S/)", min_value=0.0, step=0.50, value=0.0)
        
    total_ventas = efectivo_ing + yape_ing
    st.info(f"💰 **Total Ventas Calculado:** S/ {total_ventas:.2f}")

    if st.button("Guardar Rendición", type="primary", use_container_width=True):
        try:
            data = {
                "fecha": str(fecha_ing),
                "monto_efectivo": efectivo_ing,
                "monto_yape": yape_ing,
                "total_ventas": total_ventas
            }
            supabase.table("rendicion_caja").insert(data).execute()
            st.success("¡Rendición guardada correctamente!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al registrar la rendición: {e}")

# ==========================================
# TAB 2: REGISTRO DE GASTOS
# ==========================================
with tab2:
    st.subheader("Registrar Salida / Gasto")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_gas = st.date_input("Fecha del Gasto", key="f_gas")
        desc_gas = st.text_input("Descripción / Insumo / Servicio")
        metodo_pago = st.selectbox("Método de Pago", ["EFECTIVO", "YAPE", "TRANSFERENCIA"])
    
    with col2:
        cant_gas = st.number_input("Cantidad", min_value=1.0, step=1.0, value=1.0)
        costo_u_gas = st.number_input("Costo Unitario (S/)", min_value=0.0, step=0.50, value=0.0)
        total_gasto = cant_gas * costo_u_gas
        st.warning(f"💸 **Total Gasto:** S/ {total_gasto:.2f}")

    if st.button("Guardar Gasto", type="primary", use_container_width=True):
        if not desc_gas.strip():
            st.error("Por favor ingrese una descripción para el gasto.")
        else:
            try:
                data_gasto = {
                    "fecha": str(fecha_gas),
                    "descripcion": desc_gas,
                    "cantidad": cant_gas,
                    "costo_unitario": costo_u_gas,
                    "total_gasto": total_gasto,
                    "metodo_pago": metodo_pago
                }
                supabase.table("gastos").insert(data_gasto).execute()
                st.success("¡Gasto registrado correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar el gasto: {e}")

# ==========================================
# TAB 3: DASHBOARD Y CONTROL DE SALDOS
# ==========================================
with tab3:
    st.subheader("📊 Resumen Ejecutivo y Saldos Reales")
    
    try:
        res_rend = supabase.table("rendicion_caja").select("*").execute()
        res_gast = supabase.table("gastos").select("*").execute()
        
        df_rend = pd.DataFrame(res_rend.data) if res_rend.data else pd.DataFrame()
        df_gast = pd.DataFrame(res_gast.data) if res_gast.data else pd.DataFrame()
        
        # Filtro de registros inválidos/duplicados si existiesen
        if not df_gast.empty and "descripcion" in df_gast.columns:
            # Exclusión explícita del registro vacío duplicado del 27-mayo
            df_gast = df_gast[~((df_gast["fecha"] == "2025-05-27") & (df_gast["total_gasto"] == 100.0) & (df_gast["descripcion"].isna()))]

        # CALCULOS DE INGRESOS
        tot_efectivo_ing = df_rend["monto_efectivo"].sum() if not df_rend.empty and "monto_efectivo" in df_rend.columns else 0.0
        tot_yape_ing = df_rend["monto_yape"].sum() if not df_rend.empty and "monto_yape" in df_rend.columns else 0.0
        
        # CALCULOS DE GASTOS
        gastos_efec = 0.0
        gastos_yape = 0.0
        if not df_gast.empty and "total_gasto" in df_gast.columns:
            if "metodo_pago" in df_gast.columns:
                gastos_efec = df_gast[df_gast["metodo_pago"] == "EFECTIVO"]["total_gasto"].sum()
                gastos_yape = df_gast[df_gast["metodo_pago"] == "YAPE"]["total_gasto"].sum()
            else:
                gastos_efec = df_gast["total_gasto"].sum()

        # SALDOS REALES EN CAJA
        saldo_efectivo = tot_efectivo_ing - gastos_efec
        saldo_yape = tot_yape_ing - gastos_yape
        saldo_total = saldo_efectivo + saldo_yape
        
        # TARJETAS DE MÉTRICAS PRINCIPALES
        m1, m2, m3 = st.columns(3)
        m1.metric("💵 Saldo en EFECTIVO", f"S/ {saldo_efectivo:.2f}")
        m2.metric("📱 Saldo en YAPE", f"S/ {saldo_yape:.2f}")
        m3.metric("🏦 Saldo TOTAL Neto", f"S/ {saldo_total:.2f}")
        
        st.divider()
        
        # TARJETAS ADICIONALES DE HISTORIAL ACUMULADO
        sub1, sub2, sub3, sub4 = st.columns(4)
        sub1.metric("Ingresos Efectivo", f"S/ {tot_efectivo_ing:.2f}")
        sub2.metric("Ingresos Yape", f"S/ {tot_yape_ing:.2f}")
        sub3.metric("Gastos Efectivo", f"S/ {gastos_efec:.2f}")
        sub4.metric("Gastos Yape", f"S/ {gastos_yape:.2f}")

        st.divider()

        # GRÁFICOS DINÁMICOS
        st.subheader("📈 Visualización de Tendencias")
        if not df_rend.empty or not df_gast.empty:
            g1, g2 = st.columns(2)
            
            with g1:
                if not df_rend.empty and "fecha" in df_rend.columns:
                    fig_ing = px.bar(
                        df_rend, x="fecha", y=["monto_efectivo", "monto_yape"],
                        title="Ingresos Diarios (Efectivo vs Yape)",
                        labels={"value": "Monto (S/)", "fecha": "Fecha", "variable": "Canal"},
                        color_discrete_map={"monto_efectivo": "#2ecc71", "monto_yape": "#3498db"}
                    )
                    st.plotly_chart(fig_ing, use_container_width=True)
            
            with g2:
                if not df_gast.empty and "fecha" in df_gast.columns:
                    fig_gas = px.bar(
                        df_gast, x="fecha", y="total_gasto",
                        title="Gastos Registrados por Fecha",
                        labels={"total_gasto": "Monto (S/)", "fecha": "Fecha"},
                        color_discrete_sequence=["#e74c3c"]
                    )
                    st.plotly_chart(fig_gas, use_container_width=True)
        else:
            st.info("Aún no existen registros en la base de datos para generar visualizaciones.")

        st.divider()

        # TABLAS DE DATOS HISTÓRICOS
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.write("### 📋 Historial de Rendiciones")
            if not df_rend.empty:
                st.dataframe(df_rend.sort_values(by="fecha", ascending=False), use_container_width=True)
            else:
                st.write("Sin registros.")
                
        with col_t2:
            st.write("### 📋 Historial de Gastos")
            if not df_gast.empty:
                st.dataframe(df_gast.sort_values(by="fecha", ascending=False), use_container_width=True)
            else:
                st.write("Sin registros.")

    except Exception as e:
        st.error(f"Error al procesar el Dashboard: {e}")
