import json

# 10.4.2
# 如果以前存储了用户名, 就加载它, 否则, 提示输入用户名并存储;
filename = 'username.json'
try:
	with open(filename) as file_obj:
		username = json.load(file_obj)
except FileNotFoundError:
	username = input("What's your name?")
	with open(filename, 'w') as file_obj:
		json.dump(username, file_obj)
		print("We'll remember you when you come back, " + username + "!")
else:
	print("Welcome back, " + username + "!")