from datetime import datetime

from flask import Flask, jsonify, request
import pymysql

app = Flask(__name__)

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
    return 'Hello World!'

@app.route('/api/chapter/<chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT content FROM chapter_contents ORDER BY created_at DESC")
        novels = cursor.fetchall()
        return jsonify(novels)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/novel', methods=['POST'])
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


if __name__ == '__main__':
    app.run()
