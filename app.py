#!/usr/bin/python3

from flask import Flask, request, jsonify
from github import GitHub
import os

app = Flask(__name__)

github = None
repo = 'dcrn/test-repo'
ref = 'heads/master'

@app.before_first_request
def before_first_request(*args, **kwargs):
	global github

	token = os.environ.get('OAUTH_TOKEN')
	if not token:
		request.environ.get('werkzeug.server.shutdown')()
		print('No OAuth token supplied')

	github = GitHub(token)

@app.route('/blob', methods=['GET', 'POST'])
def blob():
	global github, repo, ref
	if request.method == 'GET':
		head = github.get_ref(repo, ref)
		commit = github.get_commit(repo, head['object']['sha'])
		tree = github.get_tree(repo, commit['tree']['sha'])

		out = {}
		for i in tree['tree']:
			out[i['path']] = i['sha']

		return jsonify(out)

	elif request.method == 'POST':
		j = request.get_json(silent=True, force=True)
		if j and 'content' in j:
			return jsonify(github.post_blob(repo, j['content']))
		else:
			return '{}'

@app.route('/file/<sha>', methods=['GET'])
def file_get(sha):
	# Get contents of a blob from sha

	pass

@app.route('/commit', methods=['POST'])
def commit():
	# Commit files and removes
	pass

@app.route('/')
def index():
	pass


if __name__ == '__main__':
	app.run(debug=True)