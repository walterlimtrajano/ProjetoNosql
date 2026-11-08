"""Login/logout na barra lateral (compartilhado entre o Catálogo e o Carrinho)."""
import streamlit as st
import redis_service as rs


def render_sidebar_auth():
    """Desenha o bloco de conta e devolve a sessão ativa (dict) ou None."""
    token = st.session_state.get("token")
    sessao = rs.validar_sessao(token) if token else None

    if token and not sessao:  # token expirou no Redis
        st.session_state.pop("token", None)
        st.sidebar.warning("Sua sessão expirou. Faça login novamente.")

    st.sidebar.header("Conta")

    if sessao:
        st.sidebar.success(f"Olá, {sessao['nome']}!")
        st.sidebar.caption(f"Sessão expira em {rs.ttl_sessao(token) // 60} min (renova a cada uso)")
        st.sidebar.caption(f"Carrinho: {rs.contar_itens(sessao['user_id'])} item(ns)")
        if st.sidebar.button("Sair"):
            rs.logout(token)
            st.session_state.pop("token", None)
            st.rerun()
        return sessao

    with st.sidebar.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            novo = rs.autenticar(email, senha)
            if novo:
                st.session_state["token"] = novo
                st.rerun()
            st.error("E-mail ou senha inválidos.")

    with st.sidebar.expander("Criar conta"):
        with st.form("form_registro"):
            n = st.text_input("Nome")
            e = st.text_input("E-mail ", key="reg_email")
            s = st.text_input("Senha ", type="password", key="reg_senha")
            if st.form_submit_button("Cadastrar"):
                if not (n.strip() and e.strip() and s):
                    st.error("Preencha todos os campos.")
                elif rs.registrar_usuario(e, n, s):
                    st.success("Conta criada! Agora faça login.")
                else:
                    st.error("Este e-mail já está cadastrado.")
    return None
