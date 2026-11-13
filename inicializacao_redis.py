"""Script de inicialização do Redis: testa a conexão e cria usuários de demonstração."""
import redis_service as rs

print("PING:", rs.r.ping())
for email, nome, senha in [
    ("ana@loja.com", "Ana Souza", "123456"),
    ("vinicius@loja.com", "Vinicius", "123456"),
    ("carlos@loja.com", "Carlos Lima", "123456"),
]:
    criado = rs.registrar_usuario(email, nome, senha)
    print(("criado:" if criado else "já existe:"), email)
