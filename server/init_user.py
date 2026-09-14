import bcrypt
import pymysql

# 生成密码哈希
password = "123456"
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
print("生成的哈希:", password_hash.decode('utf-8'))

# 连接数据库
conn = pymysql.connect(
    host='10.80.188.187',
    port=3306,
    user='root',
    password='tyui8765TYUI*&^%',
    database='csol'
)
cursor = conn.cursor()

# 清空旧用户
cursor.execute("DELETE FROM ai_users")
print("已清空旧用户")

# 创建 admin 用户
cursor.execute("""
    INSERT INTO ai_users (username, email, password_hash, full_name, role, department)
    VALUES ('admin', 'admin@metallurgy.com', %s, '系统管理员', 'admin', '技术部')
""", (password_hash,))

conn.commit()
print("✅ admin 用户创建成功 (密码: 123456)")

# 验证
cursor.execute("SELECT id, username, full_name, role FROM ai_users")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()