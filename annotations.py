import sqlite3
from flask import Flask, send_from_directory, g, request, current_app
import json
from flask.ext.jsonpify import jsonify
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

app = Flask(__name__, static_url_path='')

DATABASE = 'db/database.db'

def connect_db():
	return sqlite3.connect(DATABASE)

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	if hasattr(g, 'db'):
		g.db.close()

@app.route("/")
def hello():
	return "Hello World!"

@app.route('/post_annotation', methods=['POST', 'GET'])
def post_annotation():
	annotation = request.args.get('annotation', '')
	line = request.args.get('line', '')
	step = request.args.get('step', '')
	session = request.args.get('session', '')
	mg_user_id = request.args.get('mg_user_id', '')
	pg_user_id = request.args.get('pg_user_id', '')
	time = request.args.get('time', '')

	g.db.execute('insert into annotations(session, step, line, annotation, mg_user_id, pg_user_id, time) values (?, ?, ?, ?, ?, ?, ?);', [session, step, line, annotation, mg_user_id, pg_user_id, time])
	g.db.commit()
	# for row in query_db('select * from annotations;'):
	#   app.logger.info(row)
	insert_id = query_db('SELECT last_insert_rowid()')
	return jsonify(id=insert_id[0])

@app.route('/get_annotations', methods=['POST', 'GET'])
def get_annotations():
	step = request.args.get('step', '')
	session = request.args.get('session', '')
	result = query_db('select annotation, votes, id, line from annotations where session = ? AND step = ? order by votes desc;', [session, step])
	# app.logger.info(row[3])
	return jsonify(result)

@app.route('/post_session', methods=['POST', 'GET'])
def post_app_state():
	code = request.args.get('code', '')
	session = request.args.get('session', '')
	params = request.args.get('params', '')

	g.db.execute('insert into sessions(session, code, params) values (?, ?, ?);', [session, code, params])
	g.db.commit()
	return jsonify(result="success")

@app.route('/log_comparison_vote', methods=['POST', 'GET'])
def log_comparison_vote():
	# annotation 2 is x than annotation 1
	annotation_id_1 = request.args.get('annotation_id_1', '')
	annotation_id_2 = request.args.get('annotation_id_2', '')
	vote = request.args.get('vote', '')
	mg_user_id = request.args.get('mg_user_id', '')
	pg_user_id = request.args.get('pg_user_id', '')
	time = request.args.get('time', '')

	g.db.execute('insert into comparison_votes(annotation_id_1, annotation_id_2, vote, mg_user_id, pg_user_id, time) values (?, ?, ?, ?, ?, ?);', [annotation_id_1, annotation_id_2, vote, mg_user_id, pg_user_id, time])
	g.db.commit()
	return jsonify(result="success")

@app.route('/add_questions_to_db', methods=['POST', 'GET'])
def add_questions_to_db():
	session = "jo8ymq48yse89f6r"
	num_steps = 20

	for x in range(0, num_steps):
		g.db.execute('insert into questions(session, step) values (?, ?);', [session, x])
		g.db.commit()
	return jsonify(result="success")

@app.route('/get_session', methods=['POST', 'GET'])
def get_session():
	session = request.args.get('session', '')
	row = query_db('select * from sessions where session = ?;', [session], one=True)
	# app.logger.info(row)
	return jsonify(code=row[1], params=row[2])

@app.route('/get_questions', methods=['POST', 'GET'])
def get_question():
	session = request.args.get('session', '')
	step = request.args.get('step', '')

	result = query_db('select question, line from questions where session = ? and step = ?;', [session, step])
	# app.logger.info(row)
	return jsonify(result)

@app.route('/log_event', methods=['POST', 'GET'])
def log_event():
	session = request.args.get('session', '')
	mg_user_id = request.args.get('mg_user_id', '')
	pg_user_id = request.args.get('pg_user_id', '')
	time = request.args.get('time', '')
	step = request.args.get('step', '')
	line = request.args.get('line', '')
	event = request.args.get('event', '')

	g.db.execute('insert into log(session, mg_user_id, pg_user_id, time, step, line, event) values (?, ?, ?, ?, ?, ?, ?);', [session, mg_user_id, pg_user_id, time, step, line, event])
	g.db.commit()
	return jsonify(result="success")

@app.route('/get_lines_with_annotations', methods=['POST', 'GET'])
def get_lines_with_annotations():
	session = request.args.get('session', '')
	row = query_db('select distinct line from annotations where session = ?;', [session])
	app.logger.info(row)
	return jsonify(lines=row)

@app.route('/upvote_annotation', methods=['POST', 'GET'])
def upvote_annotation():
	annotation_id = request.args.get('annotation_id', '')

	g.db.execute('update annotations set votes = votes + 1 where id = ?;', [annotation_id])
	g.db.commit()
	return jsonify(result="success")

def query_db(query, args=(), one=False):
	cur = g.db.execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv


if __name__ == "__main__":
	app.debug = True
	handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
	handler.setLevel(logging.INFO)
	app.logger.addHandler(handler)
	app.run(host='45.56.123.166')