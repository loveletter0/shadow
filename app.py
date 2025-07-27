from datetime import datetime
from flask_cors import CORS
from flask import Flask, jsonify, request
import pymysql

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'rm-bp1m9214w950bb601mo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'lingyan',
    'password': 'denglingyan123!',
    'database': 'shadow_of_lingyan',
    'charset': 'utf8mb4'
}


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


@app.route('/')
def hello_world():  # put application's code here
    return 'Lingyan Shadows'


@app.before_request
def handle_options_request():
    """处理OPTIONS预检请求"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response


@app.route('/api/novels', methods=['GET'])
def get_novels():
    """获取所有小说列表"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT novel_id, title FROM novels ORDER BY created_at DESC")
        novels = cursor.fetchall()
        return jsonify(novels)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/chapter/<novel_id>', methods=['GET'])
def get_novel_chapters(novel_id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT chapter_id, title FROM chapters where novel_id = %s", (novel_id,))
        chapters = cursor.fetchall()
        return jsonify(chapters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/chapter_detail/<chapter_id>', methods=['GET'])
def get_chapter_content(chapter_id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT content FROM chapter_contents WHere chapter_id = %s", (chapter_id,))
        novels = cursor.fetchone()
        return jsonify(novels)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/create_novel', methods=['POST'])
def create_novel():
    """创建新小说"""
    data = request.json
    title = data.get('title')
    author = data.get('author')

    if not title or not author:
        return jsonify({'error': '小说标题和作者不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 插入小说信息
        sql = """
              INSERT INTO novels (title, author, created_at)
              VALUES (%s, %s, %s) \
              """
        cursor.execute(sql, (title, author, datetime.now()))
        novel_id = cursor.lastrowid
        conn.commit()
        return jsonify({'novel_id': novel_id, 'title': title})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/add-chapter/<novel_id>', methods=['POST'])
def add_chapter(novel_id):
    """添加新章节"""
    if not request.is_json:
        print("not json")
        return jsonify({
            "error": "无效请求",
            "message": "请求必须是JSON格式"
        }), 400
    data = request.json
    title = data.get('title')
    content = data.get('content')
    print("接收到的数据:", data)
    if not title or not content:
        return jsonify({'error': '缺少必要参数'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 获取当前最大章节号
        cursor.execute("SELECT MAX(chapter_number) AS max_num FROM chapters WHERE novel_id = %s", (novel_id,))
        result = cursor.fetchone()
        chapter_number = result[0] + 1 if result[0] else 1

        # 插入章节基本信息
        chapter_sql = """
                      INSERT INTO chapters (novel_id, chapter_number, title, created_at)
                      VALUES (%s, %s, %s, %s) \
                      """
        cursor.execute(chapter_sql, (novel_id, chapter_number, title, datetime.now()))
        chapter_id = cursor.lastrowid

        # 插入章节内容
        content_sql = "INSERT INTO chapter_contents (chapter_id, content) VALUES (%s, %s)"
        cursor.execute(content_sql, (chapter_id, content))

        conn.commit()
        return jsonify({
            'chapter_id': chapter_id,
            'chapter_number': chapter_number,
            'title': title
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run()
