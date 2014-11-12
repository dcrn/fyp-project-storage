#!/usr/bin/python3
import os, urllib.request, json, base64

apiaddr = 'https://api.github.com/'

class GitHub:
	apiaddr = 'https://api.github.com/'

	def __init__(self, oauth_token):
		self.auth_str = base64.encodebytes(
				bytes(oauth_token + ':x-oauth-basic', 'utf-8')
			)[:-1].decode('utf-8')

	def api_call(self, path, post_json=None):
		req = urllib.request.Request(apiaddr + path)
		req.add_header('Authorization', 'Basic ' + self.auth_str)

		if post_json is not None:
			req.add_data(bytes(json.dumps(post_json), 'utf-8'))

		response = urllib.request.urlopen(req)
		data = response.readall().decode('utf-8')
		return json.loads(data)

	def rate_limit(self):
		return self.api_call('rate_limit')

	def get_ref(self, repo, ref):
		return self.api_call(('repos/{repo}/git/refs/{ref}').format(repo=repo, ref=ref))

	def post_ref(self, repo, ref, sha):
		return self.api_call(
				('repos/{repo}/git/refs/{ref}').format(repo=repo, ref=ref),
				{'sha': sha, 'force': True}
			)

	def get_commit(self, repo, commit_sha):
		return self.api_call(('repos/{repo}/git/commits/{commit_sha}').format(repo=repo, commit_sha=commit_sha))

	def post_commit(self, repo, msg, tree_sha, parent_sha):
		return self.api_call(
				('repos/{repo}/git/commits').format(repo=repo),
				{'message': msg, 'tree': tree_sha, 'parents':[parent_sha]}
			)

	def get_tree(self, repo, tree_sha):
		return self.api_call(('repos/{repo}/git/trees/{tree}').format(repo=repo, tree=tree_sha))

	def post_tree(self, repo, base_tree_sha, data):
		'''Input:

			{
				'rm': ['path/to/file.py', 'helloworld.txt'],
				'files':
				{
					'path/to/file.py': '1fac2fe2c6dcb9e78027984a7ab120d068701c9d'
					'helloworld.txt': '0e6d979142198a09b9bb9ebfc3e4989703303bcb'
				}
			}
		'''

		tree = {'tree': [], 'base_tree': base_tree_sha}

		if 'rm' in data:
			# Get existing tree
			tree = self.get_tree(repo, base_tree_sha)

			# Delete response data from the tree
			del tree['sha'], tree['url'], tree['truncated']

			# Update or remove existing tree objects
			for obj in tree['tree'][:]:

				# If path is in the rm list, delete this from the tree
				if obj['path'] in data['rm']:
					tree['tree'].remove(obj)

				# If path is in data, update sha, then delete from data
				elif obj['path'] in data['files']:
					obj['sha'] = data['files'][obj['path']]
					del data['files'][obj['path']]

		# Add new objects in the tree
		for path in data['files']:
			tree['tree'].append(
				{
					'path': path,
					'mode': '100644',
					'type': 'blob',
					'sha': data['files'][path]
				})

		# Push tree to GitHub
		return self.api_call(
				('repos/{repo}/git/trees').format(repo=repo),
				tree
			)


	def get_blob(self, repo, blob_sha):
		return self.api_call(('repos/{repo}/git/blobs/{blob_sha}').format(repo=repo, blob_sha=blob_sha))

	def post_blob(self, repo, content):
		return self.api_call(
				('repos/{repo}/git/blobs').format(repo=repo),
				{'content': content, 'encoding': 'utf-8'}
			)

def main():
	token = os.environ.get('OAUTH_TOKEN')
	if not token:
		print('No OAuth token supplied')
		return

	g = GitHub(token)

	repo = 'dcrn/test-repo'
	ref = 'heads/master'

	head = g.get_ref(repo, ref)
	head_sha = head['object']['sha']

	commit = g.get_commit(repo, head_sha)
	base_tree_sha = commit['tree']['sha']

	blob = g.post_blob(repo, 'hello world\nfoo\nbar\n')

	tree = g.post_tree(repo, base_tree_sha, 
			{
				'rm': [],
				'files':
				{
					'new_text.txt': blob['sha']
				}
			}
		)

	new_commit = g.post_commit(repo, 'Updated text file', tree['sha'], commit['sha'])
	new_ref = g.post_ref(repo, ref, new_commit['sha'])

	print('\nNew ref: ')
	print(json.dumps(new_ref, indent=4))


if __name__ == '__main__':
	main()

