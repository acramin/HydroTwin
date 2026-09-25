import base64
import hashlib
import hmac
import secrets

from hydrotwin.db.conn import conectar_db
from hydrotwin.helpers.logger import logger

### Auxiliares ###
def _hash_password(password, salt=None):
    logger.debug("_hash_password(password, salt=None)")
    salt = salt or secrets.token_bytes(16)
    password_bytes = password.encode("utf-8")
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, 120_000)
    return f"{base64.b64encode(salt).decode('ascii')}${base64.b64encode(hash_bytes).decode('ascii')}"

def _verify_password(password, password_hash):
    logger.debug("_verify_password(password, password_hash)")
    try:
        salt_b64, hash_b64 = password_hash.split("$", 1)
        salt = base64.b64decode(salt_b64)
        expected_hash = base64.b64decode(hash_b64)
    except (ValueError, TypeError, base64.binascii.Error):
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120_000,
    )
    return hmac.compare_digest(candidate_hash, expected_hash)

def _generate_access_code():
    """Gera um código de acesso aleatório de 5 caracteres alfanuméricos."""
    logger.debug("_generate_access_code()")
    return secrets.token_urlsafe(4)[:5]


### Gestão de Admins ###
def ensure_default_admin():
    logger.debug("ensure_default_admin()")
    from hydrotwin.helpers.env import get_admin_credentials

    admin_username, admin_password = get_admin_credentials()
    # Assume que o admin padrão tem um email configurado ou padrão
    admin_email = "admin@hydrotwin.local"

    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM usuario WHERE role = 'admin' LIMIT 1"
        )

        if cursor.fetchone() is not None:
            return

        cursor.execute(
            """
            INSERT INTO usuario (username, password_hash, email, role)
            VALUES (?, ?, ?, 'admin')
            """,
            (admin_username, _hash_password(admin_password), admin_email),
        )
        conn.commit()
    finally:
        conn.close()


### Fluxo de Convites ###
def criar_convite(email, role="viewer", expires_in_hours=24):
    """Gera um convite com código temporário para o e-mail informado."""
    from hydrotwin.authentication.mailer import enviar_email_acesso

    logger.debug("criar_convite(email, role)")
    USER_ROLES = ("admin", "viewer")

    if role not in USER_ROLES:
        raise ValueError("Role inválida.")

    conn = conectar_db()
    try:
        cursor = conn.cursor()

        # 1. Verifica se já existe um usuário ativo cadastrado com este e-mail
        cursor.execute("SELECT id FROM usuario WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            raise ValueError("Este e-mail já possui uma conta ativa.")

        # 2. Invalida convites pendentes anteriores para o mesmo e-mail
        cursor.execute(
            """
            UPDATE convite 
            SET status = 'cancelado' 
            WHERE email = ? AND status = 'pendente'
            """,
            (email,),
        )

        # 3. Gera novo código e insere na tabela de convites
        code = _generate_access_code()
        
        cursor.execute(
            """
            INSERT INTO convite (email, code, role, expires_at)
            VALUES (?, ?, ?, datetime('now', '-3 hours', ?))
            """,
            (email, code, role, f"+{expires_in_hours} hours"),
        )
        conn.commit()

        # 4. Envia o e-mail APÓS persistir com sucesso no banco
        enviar_email_acesso(email, code)
        return code

    except Exception as e:
        logger.error(f"Erro ao criar convite: {e}")
        raise e
    finally:
        conn.close()


def obter_convite_valido(code):
    """Busca e retorna um convite pelo código, validando se está pendente e dentro do prazo."""
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, email, role 
            FROM convite 
            WHERE code = ? 
              AND status = 'pendente' 
              AND expires_at > datetime('now', '-3 hours')
            """,
            (code,),
        )
        linha = cursor.fetchone()
        if not linha:
            return None

        return {"id": linha[0], "email": linha[1], "role": linha[2]}
    finally:
        conn.close()


def finalizar_cadastro(code, username, password):
    """Converte um convite pendente em um usuário definitivo."""
    logger.debug("finalizar_cadastro(code, username, password)")

    convite = obter_convite_valido(code)
    if not convite:
        raise ValueError("Código inválido, expirado ou já utilizado.")

    username = username.strip()
    if not username:
        raise ValueError("Username não pode ser vazio.")

    conn = conectar_db()
    try:
        cursor = conn.cursor()

        # 1. Insere o novo usuário na tabela usuario
        cursor.execute(
            """
            INSERT INTO usuario (username, password_hash, email, role)
            VALUES (?, ?, ?, ?)
            """,
            (username, _hash_password(password), convite["email"], convite["role"]),
        )

        # 2. Marca o convite como usado
        cursor.execute(
            """
            UPDATE convite 
            SET status = 'usado' 
            WHERE id = ?
            """,
            (convite["id"],),
        )

        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao finalizar cadastro: {e}")
        raise e
    finally:
        conn.close()

### Consultas e Autenticação ###
def obter_todos_usuarios():
    logger.debug("obter_todos_usuarios()")
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, email FROM usuario")
        linhas = cursor.fetchall()
        return [
            {
                "id": linha[0],
                "username": linha[1],
                "role": linha[2],
                "email": linha[3],
            }
            for linha in linhas
        ]
    finally:
        conn.close()

def obter_usuario_por_username(username):
    logger.debug("obter_usuario_por_username(username)")
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, password_hash, role, email
            FROM usuario
            WHERE username = ?
            """,
            (username.strip(),),
        )
        linha = cursor.fetchone()
        if linha is None:
            return None

        return {
            "id": linha[0],
            "username": linha[1],
            "password_hash": linha[2],
            "role": linha[3],
            "email": linha[4],
        }
    finally:
        conn.close()

def autenticar_usuario(username, password):
    logger.debug("autenticar_usuario(username, password)")
    usuario = obter_usuario_por_username(username)
    if usuario is None:
        return None

    if not _verify_password(password, usuario["password_hash"]):
        return None

    return {
        "id": usuario["id"],
        "username": usuario["username"],
        "role": usuario["role"],
        "email": usuario["email"],
    }
    
import uuid

### Gestão de Sessões / Tokens ###
def criar_sessao_usuario(usuario_id, expires_in_days=7):
    """Gera um token UUID único e salva no banco de dados."""
    token = str(uuid.uuid4())
    logger.debug(f"criar_sessao_usuario(usuario_id={usuario_id})")
    
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessao_usuario (token, usuario_id, expires_at)
            VALUES (?, ?, datetime('now', '-3 hours', ?))
            """,
            (token, usuario_id, f"+{expires_in_days} days"),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def obter_usuario_por_token_sessao(token):
    """Verifica se o token de sessão existe e se ainda é válido."""
    if not token:
        return None

    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id, u.username, u.role, u.email 
            FROM usuario u
            JOIN sessao_usuario s ON u.id = s.usuario_id
            WHERE s.token = ? AND s.expires_at > datetime('now', '-3 hours')
            """,
            (token,),
        )
        linha = cursor.fetchone()
        if not linha:
            return None

        return {
            "id": linha[0],
            "username": linha[1],
            "role": linha[2],
            "email": linha[3],
        }
    finally:
        conn.close()


def revogar_sessao_usuario(token):
    """Deleta a sessão no logout."""
    if not token:
        return

    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessao_usuario WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()
        
def limpar_sessoes_expiradas():
    """Remove todas as sessões que já ultrapassaram a data/hora de expiração."""
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM sessao_usuario 
            WHERE expires_at <= datetime('now', '-3 hours')
            """
        )
        conn.commit()
        logger.debug(f"Sessões expiradas removidas: {cursor.rowcount}")
    finally:
        conn.close()