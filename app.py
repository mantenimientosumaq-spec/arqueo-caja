import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Arqueo de Caja - Baños", page_icon="🚽", layout="centered")

# Conexión a Supabase
url = st.secrets.get("SUPABASE_URL", "")
key = st.secrets.get("SUPABASE_KEY", "")

if url and key:
    supabase: Client = create_client(url, key)
else:
    st.error("Configura las credenciales SUPABASE_URL y SUPABASE_KEY en los Secrets de Streamlit.")

st.title("🚽 Arqueo de Caja - Baños")

tab1, tab2 = st.tabs(["💵 Rendición / Cobro", "💸 Registrar Gasto"])

with tab1:
    st.subheader("Ingreso Diario")
    fecha = st.date_input("Fecha", key="f_ing")
    efectivo = st.number_input("Monto Efectivo (S/)", min_value=0.0, step=0.50, value=0.0)
    yape = st.number_input("Monto Yape (S/)", min_value=0.0, step=0.50, value=0.0)
    total = efectivo + yape
    st.markdown(f"**Total Ventas:** S/ {total:.2f}")
    
    if st.button("Guardar Rendición", type="primary"):
        data = {
            "fecha": str(fecha),
            "piso": 1,
            "rubro": "SERVICIO",
            "tipo_ingreso": "ING",
            "monto_efectivo": efectivo,
            "monto_yape": yape,
            "total_ventas": total
        }
        supabase.table("rendicion_caja").insert(data).execute()
        st.success("¡Rendición guardada con éxito!")

with tab2:
    st.subheader("Registro de Gasto")
    fecha_g = st.date_input("Fecha Gasto", key="f_gast")
    producto = st.text_input("Descripción / Producto")
    cantidad = st.number_input("Cantidad", min_value=1.0, value=1.0)
    costo_unitario = st.number_input("Costo Unitario (S/)", min_value=0.0, step=1.0, value=0.0)
    costo_total = cantidad * costo_unitario
    st.markdown(f"**Total Gasto:** S/ {costo_total:.2f}")
    metodo = st.selectbox("Método de Pago", ["EFECTIVO", "YAPE"])
    
    if st.button("Guardar Gasto"):
        data_gasto = {
            "fecha": str(fecha_g),
            "tienda": "BAÑO",
            "tipo_gasto": "GG",
            "concepto": "SERVICIO",
            "producto": producto,
            "cantidad": cantidad,
            "und_medida": "UNIDAD",
            "costo_unitario": costo_unitario,
            "costo_total": costo_total,
            "metodo_pago": metodo
        }
        supabase.table("gastos").insert(data_gasto).execute()
        st.success("¡Gasto registrado exitosamente!")
