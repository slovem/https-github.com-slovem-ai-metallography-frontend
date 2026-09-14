from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import bcrypt
import jwt
import datetime
import os
import json
import uuid
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)

# ====== 就用这个最简单的 CORS 配置 ======
CORS(app, supports_credentials=True, origins='*')

JWT_SECRET = os.getenv('JWT_SECRET', 'ai_metallography_secret_key_2026')
JWT_EXPIRATION = 7

DB_CONFIG = {
    'host': '10.80.188.187',
    'port': 3306,
    'user': 'root',
    'password': 'tyui8765TYUI*&^%',
    'database': 'csol',
    'charset': 'utf8mb4'
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def get_current_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'code': 401, 'message': '未提供Token'}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user_id = payload['id']
            request.username = payload['username']
            request.role = payload.get('role', '')
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'message': 'Token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'message': 'Token无效'}), 401
        return f(*args, **kwargs)
    return decorated

def log_operation(user_id, username, module, action, operation, **kwargs):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ai_operation_logs 
                (user_id, username, module, action, operation, ip, user_agent, request_url, request_method, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, username, module, action, operation,
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                request.path,
                request.method,
                get_current_time()
            ))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f'日志记录失败: {e}')

# ============ 认证 API ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    real_name = data.get('realName')  # 前端传的是 realName
    phone = data.get('phone')
    department = data.get('department')
    
    if not all([username, email, password]):
        return jsonify({'code': 400, 'message': '用户名、邮箱和密码不能为空'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute('SELECT id FROM ai_users WHERE username = %s OR email = %s', (username, email))
            if cursor.fetchone():
                return jsonify({'code': 400, 'message': '用户名或邮箱已存在'}), 400
            
            # 加密密码
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            # 插入用户 - 注意字段名 real_name
            cursor.execute("""
                INSERT INTO ai_users 
                (username, email, password_hash, real_name, phone, department, role, audit_status, register_ip, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'inspector', 'pending', %s, %s)
            """, (
                username, email, password_hash, real_name, phone, department,
                request.remote_addr,
                get_current_time()
            ))
            conn.commit()
            
            log_operation(None, username, 'auth', 'REGISTER', f'用户注册: {username}')
            
            return jsonify({
                'code': 0,
                'message': '注册成功，请等待管理员审核',
                'data': {'id': cursor.lastrowid}
            })
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM ai_users WHERE username = %s OR email = %s', (username, username))
            user = cursor.fetchone()
            if not user:
                return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401
            
            # ✅ 检查审核状态
            audit_status = user.get('audit_status', 'pending')
            if audit_status == 'pending':
                return jsonify({'code': 403, 'message': '账号正在审核中，请等待管理员审核'}), 403
            if audit_status == 'rejected':
                return jsonify({'code': 403, 'message': '账号已被拒绝，请联系管理员'}), 403
            
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401
            
            # 更新最后登录时间
            cursor.execute('UPDATE ai_users SET last_login = NOW() WHERE id = %s', (user['id'],))
            
            # 获取用户权限版本
            cursor.execute("""
                SELECT version FROM ai_permission_version WHERE user_id = %s
            """, (user['id'],))
            version_result = cursor.fetchone()
            permission_version = version_result['version'] if version_result else 0
            
            conn.commit()
            
            payload = {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'permission_version': permission_version,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRATION)
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
            
            log_operation(user['id'], user['username'], 'auth', 'LOGIN', f'用户登录: {username}')
            
            return jsonify({
                'code': 0,
                'message': '登录成功',
                'data': {
                    'token': token,
                    'permission_version': permission_version,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'fullName': user['full_name'],
                        'role': user['role'],
                        'department': user['department'],
                        'avatar': user.get('avatar')
                    }
                }
            })
    finally:
        conn.close()
@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT id, username, email, full_name, role, department, avatar FROM ai_users WHERE id = %s', (request.user_id,))
            user = cursor.fetchone()
            return jsonify({'code': 0, 'data': user})
    finally:
        conn.close()

@app.route('/api/auth/permissions', methods=['GET'])
@token_required
def get_user_permissions():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 确保用户有版本记录
            cursor.execute("""
                INSERT INTO ai_permission_version (user_id, version, updated_at)
                VALUES (%s, 0, NOW())
                ON DUPLICATE KEY UPDATE updated_at = NOW()
            """, (request.user_id,))
            conn.commit()
            
            # 获取用户权限版本
            cursor.execute("""
                SELECT version FROM ai_permission_version WHERE user_id = %s
            """, (request.user_id,))
            version_result = cursor.fetchone()
            permission_version = version_result['version'] if version_result else 0
            
            # 获取用户的角色
            cursor.execute("""
                SELECT r.id, r.role_code
                FROM ai_user_roles ur
                JOIN ai_roles r ON ur.role_id = r.id
                WHERE ur.user_id = %s AND r.is_active = 1
            """, (request.user_id,))
            roles = cursor.fetchall()
            
            if not roles:
                return jsonify({
                    'code': 0,
                    'data': {
                        'permissions': [],
                        'codes': [],
                        'version': permission_version
                    }
                })
            
            role_ids = [r['id'] for r in roles]
            placeholders = ','.join(['%s'] * len(role_ids))
            
            # 获取用户的所有权限
            cursor.execute(f"""
                SELECT DISTINCT p.*
                FROM ai_role_permissions rp
                JOIN ai_permissions p ON rp.permission_id = p.id
                WHERE rp.role_id IN ({placeholders}) AND p.is_visible = 1
                ORDER BY p.parent_id, p.sort_order
            """, role_ids)
            permissions = cursor.fetchall()
            
            return jsonify({
                'code': 0,
                'data': {
                    'permissions': permissions,
                    'codes': [p['permission_code'] for p in permissions] if permissions else [],
                    'version': permission_version
                }
            })
    except Exception as e:
        print(f'❌ 获取用户权限失败: {e}')
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        conn.close()
		
@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password():
    data = request.get_json()
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')
    if not old_password or not new_password:
        return jsonify({'code': 400, 'message': '请输入原密码和新密码'}), 400
    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '新密码至少6位'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT password_hash FROM ai_users WHERE id = %s', (request.user_id,))
            user = cursor.fetchone()
            if not bcrypt.checkpw(old_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return jsonify({'code': 400, 'message': '原密码错误'}), 400
            salt = bcrypt.gensalt()
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
            cursor.execute('UPDATE ai_users SET password_hash = %s WHERE id = %s', (new_hash, request.user_id))
            conn.commit()
            log_operation(request.user_id, request.username, 'auth', 'UPDATE', '修改密码')
            return jsonify({'code': 0, 'message': '密码修改成功'})
    finally:
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    log_operation(request.user_id, request.username, 'auth', 'LOGOUT', '用户退出登录')
    return jsonify({'code': 0, 'message': '退出成功'})

# ============ 任务管理 API ============

@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            status = request.args.get('status')
            grade = request.args.get('grade')
            keyword = request.args.get('keyword')
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))
            offset = (page - 1) * page_size
            
            sql = "SELECT * FROM ai_tasks WHERE 1=1"
            params = []
            
            if status:
                sql += " AND status = %s"
                params.append(status)
            if grade:
                sql += " AND grade LIKE %s"
                params.append(f'%{grade}%')
            if keyword:
                sql += " AND (task_code LIKE %s OR sample_id LIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            count_sql = sql.replace("SELECT *", "SELECT COUNT(*) as total")
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])
            cursor.execute(sql, params)
            tasks = cursor.fetchall()
            
            return jsonify({'code': 0, 'data': tasks, 'total': total})
    finally:
        conn.close()

@app.route('/api/tasks', methods=['POST'])
@token_required
def create_task():
    data = request.get_json()
    task_code = f"T{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ai_tasks 
                (task_code, grade, heat_treatment, standard, sample_id, remark, image_count, status, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            """, (
                task_code,
                data.get('grade'),
                data.get('heatTreatment'),
                data.get('standard'),
                data.get('sampleId'),
                data.get('remark'),
                data.get('imageCount', 0),
                request.user_id,
                get_current_time()
            ))
            conn.commit()
            task_id = cursor.lastrowid
            log_operation(request.user_id, request.username, 'task', 'CREATE', f'创建任务: {task_code}')
            return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': task_id, 'task_code': task_code}})
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM ai_tasks WHERE id = %s", (task_id,))
            task = cursor.fetchone()
            if not task:
                return jsonify({'code': 404, 'message': '任务不存在'}), 404
            return jsonify({'code': 0, 'data': task})
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE ai_tasks SET 
                grade = %s, heat_treatment = %s, standard = %s, sample_id = %s, remark = %s, updated_at = %s
                WHERE id = %s
            """, (
                data.get('grade'),
                data.get('heatTreatment'),
                data.get('standard'),
                data.get('sampleId'),
                data.get('remark'),
                get_current_time(),
                task_id
            ))
            conn.commit()
            log_operation(request.user_id, request.username, 'task', 'UPDATE', f'更新任务: {task_id}')
            return jsonify({'code': 0, 'message': '更新成功'})
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>/status', methods=['PUT'])
@token_required
def update_task_status(task_id):
    data = request.get_json()
    status = data.get('status')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE ai_tasks SET status = %s, updated_at = %s"
            params = [status, get_current_time()]
            if status == 'completed':
                sql += ", completed_at = %s"
                params.append(get_current_time())
            sql += " WHERE id = %s"
            params.append(task_id)
            cursor.execute(sql, params)
            conn.commit()
            log_operation(request.user_id, request.username, 'task', 'UPDATE', f'更新任务状态: {task_id} -> {status}')
            return jsonify({'code': 0, 'message': '状态更新成功'})
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM ai_tasks WHERE id = %s", (task_id,))
            conn.commit()
            log_operation(request.user_id, request.username, 'task', 'DELETE', f'删除任务: {task_id}')
            return jsonify({'code': 0, 'message': '删除成功'})
    finally:
        conn.close()

# ============ 标注任务 API ============

@app.route('/api/annotation/tasks', methods=['GET'])
@token_required
def get_annotation_tasks():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            status = request.args.get('status')
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))
            offset = (page - 1) * page_size
            
            sql = "SELECT * FROM ai_annotation_tasks WHERE 1=1"
            params = []
            if status:
                sql += " AND status = %s"
                params.append(status)
            
            count_sql = sql.replace("SELECT *", "SELECT COUNT(*) as total")
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])
            cursor.execute(sql, params)
            tasks = cursor.fetchall()
            return jsonify({'code': 0, 'data': tasks, 'total': total})
    finally:
        conn.close()

@app.route('/api/annotation/tasks', methods=['POST'])
@token_required
def create_annotation_task():
    data = request.get_json()
    task_code = f"A{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ai_annotation_tasks 
                (task_code, dataset_name, image_count, status, progress, created_by, created_at)
                VALUES (%s, %s, %s, 'pending', 0, %s, %s)
            """, (
                task_code,
                data.get('datasetName'),
                data.get('imageCount', 0),
                request.user_id,
                get_current_time()
            ))
            conn.commit()
            log_operation(request.user_id, request.username, 'annotation', 'CREATE', f'创建标注任务: {task_code}')
            return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': cursor.lastrowid, 'task_code': task_code}})
    finally:
        conn.close()

# ============ 模型训练 API ============

@app.route('/api/training/tasks', methods=['GET'])
@token_required
def get_training_tasks():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            status = request.args.get('status')
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))
            offset = (page - 1) * page_size
            
            sql = "SELECT * FROM ai_model_training WHERE 1=1"
            params = []
            if status:
                sql += " AND status = %s"
                params.append(status)
            
            count_sql = sql.replace("SELECT *", "SELECT COUNT(*) as total")
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])
            cursor.execute(sql, params)
            tasks = cursor.fetchall()
            return jsonify({'code': 0, 'data': tasks, 'total': total})
    finally:
        conn.close()

@app.route('/api/training/tasks', methods=['POST'])
@token_required
def create_training_task():
    data = request.get_json()
    task_code = f"M{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ai_model_training 
                (task_code, model_name, dataset_name, model_type, status, config, created_by, created_at)
                VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s)
            """, (
                task_code,
                data.get('modelName'),
                data.get('datasetName'),
                data.get('modelType'),
                json.dumps(data.get('config', {})),
                request.user_id,
                get_current_time()
            ))
            conn.commit()
            log_operation(request.user_id, request.username, 'training', 'CREATE', f'创建训练任务: {task_code}')
            return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': cursor.lastrowid, 'task_code': task_code}})
    finally:
        conn.close()

# ============ 数据集管理 API ============

@app.route('/api/datasets', methods=['GET'])
@token_required
def get_datasets():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM ai_datasets ORDER BY created_at DESC")
            datasets = cursor.fetchall()
            return jsonify({'code': 0, 'data': datasets})
    finally:
        conn.close()

@app.route('/api/datasets', methods=['POST'])
@token_required
def create_dataset():
    data = request.get_json()
    dataset_code = f"D{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ai_datasets 
                (dataset_code, dataset_name, dataset_type, image_count, annotation_count, version, description, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dataset_code,
                data.get('datasetName'),
                data.get('datasetType'),
                data.get('imageCount', 0),
                data.get('annotationCount', 0),
                data.get('version', 'v1.0'),
                data.get('description'),
                request.user_id,
                get_current_time()
            ))
            conn.commit()
            log_operation(request.user_id, request.username, 'dataset', 'CREATE', f'创建数据集: {dataset_code}')
            return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': cursor.lastrowid, 'dataset_code': dataset_code}})
    finally:
        conn.close()

# ============ 操作日志 API ============

@app.route('/api/logs', methods=['GET'])
@token_required
def get_logs():
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            module = request.args.get('module')
            action = request.args.get('action')
            keyword = request.args.get('keyword')
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 20))
            offset = (page - 1) * page_size
            
            sql = "SELECT * FROM ai_operation_logs WHERE 1=1"
            params = []
            if module:
                sql += " AND module = %s"
                params.append(module)
            if action:
                sql += " AND action = %s"
                params.append(action)
            if keyword:
                sql += " AND (username LIKE %s OR operation LIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            count_sql = sql.replace("SELECT *", "SELECT COUNT(*) as total")
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])
            cursor.execute(sql, params)
            logs = cursor.fetchall()
            return jsonify({'code': 0, 'data': logs, 'total': total})
    finally:
        conn.close()

# ============ 用户管理 API ============


@app.route('/api/admin/users/<int:user_id>/status', methods=['PUT'])
@token_required
def admin_update_user_status(user_id):
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE ai_users SET is_active = %s WHERE id = %s", (data.get('is_active', 1), user_id))
            conn.commit()
            log_operation(request.user_id, request.username, 'user', 'UPDATE', f'更新用户状态: {user_id}')
            return jsonify({'code': 0, 'message': '更新成功'})
    finally:
        conn.close()

# ============ 角色管理 API ============

@app.route('/api/admin/roles', methods=['GET'])
@token_required
def admin_get_roles():
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM ai_roles ORDER BY id")
            return jsonify({'code': 0, 'data': cursor.fetchall()})
    finally:
        conn.close()

@app.route('/api/admin/roles', methods=['POST'])
@token_required
def admin_create_role():
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    data = request.get_json()
    if not data.get('role_code') or not data.get('role_name'):
        return jsonify({'code': 400, 'message': '角色编码和名称不能为空'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ai_roles (role_code, role_name, description, is_active) VALUES (%s, %s, %s, %s)",
                (data['role_code'], data['role_name'], data.get('description'), data.get('is_active', 1))
            )
            conn.commit()
            log_operation(request.user_id, request.username, 'role', 'CREATE', f'创建角色: {data["role_code"]}')
            return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': cursor.lastrowid}})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 400, 'message': '角色编码已存在'}), 400
    finally:
        conn.close()

@app.route('/api/admin/roles/<int:role_id>/menus', methods=['GET'])
@token_required
def admin_get_role_menus(role_id):
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT menu_id FROM ai_role_menus WHERE role_id = %s", (role_id,))
            return jsonify({'code': 0, 'data': [row[0] for row in cursor.fetchall()]})
    finally:
        conn.close()

# 获取角色的权限（返回权限ID列表）
# 获取角色的权限（返回权限ID列表）
@app.route('/api/admin/roles/<int:role_id>/permissions', methods=['GET'])
@token_required
def admin_get_role_permissions(role_id):
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT permission_id FROM ai_role_permissions WHERE role_id = %s",
                (role_id,)
            )
            result = cursor.fetchall()
            permission_ids = [row[0] for row in result]
            return jsonify({'code': 0, 'data': permission_ids})
    except Exception as e:
        print(f'获取角色权限失败: {e}')
        return jsonify({'code': 500, 'message': '获取失败'}), 500
    finally:
        conn.close()
# 更新角色的权限
@app.route('/api/admin/roles/<int:role_id>/permissions', methods=['PUT'])
@token_required
def admin_update_role_permissions(role_id):
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    # 防止管理员取消自己的所有权限
    if request.user_id == role_id:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT role FROM ai_users WHERE id = %s", (request.user_id,))
                user = cursor.fetchone()
                if user and user[0] == 'admin':
                    data = request.get_json()
                    permission_ids = data.get('permissionIds', [])
                    if not permission_ids or len(permission_ids) == 0:
                        return jsonify({'code': 400, 'message': '不能取消自己的所有权限'}), 400
        finally:
            conn.close()
    
    data = request.get_json()
    permission_ids = data.get('permissionIds', [])
    
    if not isinstance(permission_ids, list):
        permission_ids = []
    
    permission_ids = list(set(permission_ids))
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 删除该角色的所有权限
            cursor.execute("DELETE FROM ai_role_permissions WHERE role_id = %s", (role_id,))
            
            # 2. 重新插入选中的权限
            if permission_ids:
                for pid in permission_ids:
                    cursor.execute("SELECT id FROM ai_permissions WHERE id = %s", (pid,))
                    if cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO ai_role_permissions (role_id, permission_id) VALUES (%s, %s)",
                            (role_id, pid)
                        )
            
            # 3. 获取该角色关联的所有用户
            cursor.execute("""
                SELECT DISTINCT user_id FROM ai_user_roles WHERE role_id = %s
            """, (role_id,))
            user_rows = cursor.fetchall()
            
            # 4. 更新这些用户的权限版本号（版本号 +1）
            for row in user_rows:
                user_id = row[0]
                cursor.execute("""
                    INSERT INTO ai_permission_version (user_id, version, updated_at)
                    VALUES (%s, 1, NOW())
                    ON DUPLICATE KEY UPDATE version = version + 1, updated_at = NOW()
                """, (user_id,))
            
            # 5. 如果当前用户也在更新列表中，也更新当前用户的版本
            # 但当前用户已经在上面更新了
            
            conn.commit()
            
            # 获取更新的用户数量
            affected_users = len(user_rows)
            log_operation(request.user_id, request.username, 'role', 'UPDATE', 
                         f'更新角色权限: {role_id}, 权限数: {len(permission_ids)}, 影响用户: {affected_users}')
            
            return jsonify({
                'code': 0, 
                'message': '更新成功',
                'data': {
                    'affected_users': affected_users
                }
            })
    except Exception as e:
        print(f'❌ 更新角色权限失败: {e}')
        conn.rollback()
        return jsonify({'code': 500, 'message': f'更新失败: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/admin/roles/<int:role_id>/menus', methods=['PUT'])
@token_required
def admin_update_role_menus(role_id):
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    data = request.get_json()
    menu_ids = data.get('menuIds', [])
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 先删除该角色的所有菜单权限
            cursor.execute("DELETE FROM ai_role_menus WHERE role_id = %s", (role_id,))
            # 重新插入选中的菜单权限
            for mid in menu_ids:
                cursor.execute(
                    "INSERT INTO ai_role_menus (role_id, menu_id) VALUES (%s, %s)",
                    (role_id, mid)
                )
            conn.commit()
            log_operation(request.user_id, request.username, 'role', 'UPDATE', f'更新角色菜单: {role_id}')
            return jsonify({'code': 0, 'message': '更新成功'})
    except Exception as e:
        print(f'更新角色菜单失败: {e}')
        return jsonify({'code': 500, 'message': '更新失败'}), 500
    finally:
        conn.close()

# ============ 权限管理 API ============

@app.route('/api/admin/permissions', methods=['GET'])
@token_required
def admin_get_permissions():
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询所有权限
            cursor.execute("""
                SELECT p.*, r.role_code
                FROM ai_permissions p
                LEFT JOIN ai_role_permissions rp ON p.id = rp.permission_id
                LEFT JOIN ai_roles r ON rp.role_id = r.id
                ORDER BY p.parent_id, p.sort_order
            """)
            permissions = cursor.fetchall()
            return jsonify({'code': 0, 'data': permissions})
    except Exception as e:
        print(f'❌ 获取权限列表失败: {e}')
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        conn.close()

# ============ 角色权限请求 ============
@app.route('/api/admin/menus', methods=['GET'])
@token_required
def admin_get_menus():
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM ai_menus ORDER BY sort_order")
            return jsonify({'code': 0, 'data': cursor.fetchall()})
    finally:
        conn.close()


# ============ 检测标准 API ============

@app.route('/api/standards', methods=['GET'])
@token_required
def get_standards():
    standards = [
        {'code': 'GB/T 6394', 'name': '晶粒度评级', 'description': '金属平均晶粒度测定方法'},
        {'code': 'GB/T 10561', 'name': '非金属夹杂物', 'description': '钢中非金属夹杂物含量的测定'},
        {'code': 'GB/T 224', 'name': '脱碳层检测', 'description': '钢的脱碳层深度测定法'},
        {'code': 'GB/T 13299', 'name': '带状组织评级', 'description': '钢的带状组织评级方法'},
        {'code': 'GB/T 1979', 'name': '低倍组织评级', 'description': '结构钢低倍组织缺陷评级图'},
        {'code': 'ASTM E112', 'name': '晶粒度评级(ASTM)', 'description': 'Standard Test Methods for Determining Average Grain Size'}
    ]
    return jsonify({'code': 0, 'data': standards})
# ============ 用户审核管理 API ============

# 1. 获取待审核用户列表
@app.route('/api/admin/users/pending', methods=['GET'])
@token_required
def admin_get_pending_users():
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, username, email, real_name, phone, department, register_ip, created_at
                FROM ai_users 
                WHERE audit_status = 'pending'
                ORDER BY created_at ASC
            """)
            users = cursor.fetchall()
            return jsonify({'code': 0, 'data': users})
    finally:
        conn.close()

# 2. 审核用户
@app.route('/api/admin/users/<int:user_id>/audit', methods=['PUT'])
@token_required
def admin_audit_user(user_id):
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    data = request.get_json()
    status = data.get('status')  # approved 或 rejected
    remark = data.get('remark', '')
    role_ids = data.get('roleIds', [])  # 选中的角色ID列表
    
    if status not in ['approved', 'rejected']:
        return jsonify({'code': 400, 'message': '审核状态不正确'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查用户是否存在且待审核
            cursor.execute("SELECT username FROM ai_users WHERE id = %s AND audit_status = 'pending'", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'code': 404, 'message': '用户不存在或已审核'}), 404
            
            # 更新审核状态
            cursor.execute("""
                UPDATE ai_users 
                SET audit_status = %s, audit_remark = %s, audit_at = %s, audit_by = %s
                WHERE id = %s
            """, (status, remark, get_current_time(), request.user_id, user_id))
            conn.commit()
            
            # 审核通过，分配角色
            if status == 'approved':
                # 如果没传角色，默认分配 inspector
                if not role_ids:
                    cursor.execute("SELECT id FROM ai_roles WHERE role_code = 'inspector'")
                    default_role = cursor.fetchone()
                    if default_role:
                        role_ids = [default_role[0]]
                
                # 删除已有角色
                cursor.execute("DELETE FROM ai_user_roles WHERE user_id = %s", (user_id,))
                # 分配新角色
                for rid in role_ids:
                    cursor.execute(
                        "INSERT INTO ai_user_roles (user_id, role_id) VALUES (%s, %s)",
                        (user_id, rid)
                    )
                conn.commit()
            
            log_operation(request.user_id, request.username, 'user', 'AUDIT', 
                         f'审核用户: {user[0]} -> {status}, 角色: {role_ids}, 备注: {remark}')
            
            return jsonify({'code': 0, 'message': f'审核完成'})
    finally:
        conn.close()
# 3. 获取所有用户（含审核状态）
@app.route('/api/admin/users', methods=['GET'])
@token_required
def admin_get_users():
    if request.role != 'admin':
        return jsonify({'code': 403, 'message': '无权限'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    u.id, 
                    u.username, 
                    u.email, 
                    u.real_name, 
                    u.phone,
                    u.role, 
                    u.department, 
                    u.audit_status,
                    u.is_active, 
                    u.last_login, 
                    u.created_at,
                    GROUP_CONCAT(r.role_name) as role_names
                FROM ai_users u
                LEFT JOIN ai_user_roles ur ON u.id = ur.user_id
                LEFT JOIN ai_roles r ON ur.role_id = r.id
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """)
            users = cursor.fetchall()
            return jsonify({'code': 0, 'data': users})
    finally:
        conn.close()
# ============ 健康检查 ============

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'AI金相识别系统后端运行中'})

if __name__ == '__main__':
    print('🚀 AI金相识别系统后端启动中...')
    print(f'📡 数据库: {DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}')
    app.run(host='0.0.0.0', port=3001, debug=True)