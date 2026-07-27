import base64
import hashlib
import secrets
import hmac

from hydrotwin.db.conn import conectar_db

### Auxiliares ###
def _hash_password(password, salt=None):
    """_summary_

    Args:
        password (_type_): _description_
        salt (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    salt = salt or secrets.token_bytes(16)
    password_bytes = password.encode("utf-8")
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, 120_000)
    return f"{base64.b64encode(salt).decode('ascii')}${base64.b64encode(hash_bytes).decode('ascii')}"

def _verify_password(password, password_hash):
    """_summary_

    Args:
        password (_type_): _description_
        password_hash (_type_): _description_

    Returns:
        _type_: _description_
    """
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

### Principais ###
def ensure_default_admin():
    from hydrotwin.helpers.env import get_admin_credentials
    DEFAULT_ADMIN_USERNAME = get_admin_credentials()[0]
    DEFAULT_ADMIN_PASSWORD = get_admin_credentials()[1]
    
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id
            FROM usuario
            WHERE role = 'admin'
            LIMIT 1
            """
        )
        
        # Tem admin cadastrado
        if cursor.fetchone() is not None:
            return
        
        # Insere admin
        cursor.execute(
            """
            INSERT INTO usuario (username, password_hash, role)
            VALUES (?, ?, 'admin')
            """,
            (DEFAULT_ADMIN_USERNAME, _hash_password(DEFAULT_ADMIN_PASSWORD)),
        )
        conn.commit()
    finally:
        conn.close()
        
def criar_usuario(username, password, role="viewer"):
    USER_ROLES = ("admin", "viewer")

    if role not in USER_ROLES:
        raise ValueError("Role inválida.")

    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO usuario (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (username.strip(), _hash_password(password), role),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def obter_usuario_por_username(username):

    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, password_hash, role
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
        }
    finally:
        conn.close()

def autenticar_usuario(username, password):
    usuario = obter_usuario_por_username(username)
    if usuario is None:
        return None

    if not _verify_password(password, usuario["password_hash"]):
        return None

    return {
        "id": usuario["id"],
        "username": usuario["username"],
        "role": usuario["role"],
    }