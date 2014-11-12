#!/usr/bin/python3

from flask import Flask, request, jsonify, render_template
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

@app.route('/blob/<sha>', methods=['GET'])
def blob_get(sha):
	# Get contents of a blob from sha
	return jsonify(github.get_blob(repo, sha))

@app.route('/commit', methods=['POST'])
def commit():
	j = request.get_json(silent=True, force=True)

	if not j or 'message' not in j:
		return '{"msg": "No commit message"}'

	if 'rm' not in j:
		j['rm'] = []

	if 'files' not in j:
		j['files'] = {}	

	if len(j['files']) == 0 and len(j['rm']) == 0:
		return '{"msg": "Nothing to commit"}'

	head = github.get_ref(repo, ref)
	commit = github.get_commit(repo, head['object']['sha'])

	newtree = github.post_tree(repo, commit['tree']['sha'], j)
	newcommit = github.post_commit(repo, j['message'], newtree['sha'], commit['sha'])
	newref = github.post_ref(repo, ref, newcommit['sha'])

	return jsonify(newref)


@app.route('/')
def index():
	return render_template('index.html')


if __name__ == '__main__':
	app.run(debug=True)