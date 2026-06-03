from utils import Gitlab

DEFAULT_SEPARATOR=":"

import argparse

def add_comment(args, message):
	# Replace values
	if args.message_replace is not None:
		for replace in args.message_replace:
			if separator in replace:
				split = replace.split(separator, 1)
				old_value = split[0].strip()
				new_value = split[1].strip()
				if old_value == "":
					print(f"[WARN!] Expression {replace} has an empty key. Skipping.")
				else:
					expr = f":{old_value}:"
					if expr in message:
						message = message.replace(f":{old_value}:", new_value)
						print(f"[INFO!] Message modified from ':{old_value}:' to '{new_value}' in the message")
					else:
						print(f"[WARN!] Expression {expr} not found in the message. Skipping.")
			else:
				print(f"[WARN!] Expression {replace} doesn't contain separator '{separator}'. Skipping.")
	else:
		print(f"[INFO!] No modifiers applied to message.")

	print(f"[INFO!] Adding the following comment in MR:\n{'=' * 40}\n{message}\n{'=' * 40}")

	gitlab = Gitlab(args.url, args.token)
	gitlab.post_comment(project_id=args.project_id, merge_request_id=args.merge_request_id, message=message)

if __name__ == "__main__":
	# -- Parsing Arguments --
	parser = argparse.ArgumentParser(description="Add comment in MR")

	# Gitlab required data
	parser.add_argument("-u", "--url", help = "Gitlab instance URL")
	parser.add_argument("-t", "--token", help = "Gitlab private token")
	parser.add_argument("-p", "--project-id",  dest="project_id", help ="Gitlab Project ID")
	parser.add_argument("-mr", "--merge-request-id", dest="merge_request_id", help="Gitlab Merge Request ID")
	# Message required data
	parser.add_argument("-m", "--message", help="MR comment content")
	parser.add_argument("-mf", "--message-file", dest="message_file", help = "Use file content as message. Dynamic values can be set using -ml flag, and the content must be set between colons (:value:)")
	parser.add_argument("-ml", "--message-replace", nargs='+', dest="message_replace", help = "If template file is used, set replacement dictionary as key:value (example: -ml 'title:Summary of text' 'id:456')")
	parser.add_argument("-ms", "--message-separator", dest="message_separator", default=DEFAULT_SEPARATOR, help = "Change default separator (:) of list to another value (example: -ms '@')")

	# Read arguments from command line
	args = parser.parse_args()

	separator = args.message_separator
	message = args.message

	if args.message_file is not None:
		try:
			with open(args.message_file, 'r') as f:
				message = f.read()
		except Exception as e:
			print(f"[ERROR!] File error: {e}")
			exit(1)

	if message is None or message == "":
		print(f"[WARN!] Empty Message. Please check if a message (-m) or a file (-mf) has been set correctly. Check -h or --help for more info.")
	elif args.url is None or args.url == "":
		print(f"[WARN!] No url provided. Check -h or --help for more info.")
	elif args.token is None or args.token == "":
		print(f"[WARN!] No tokens provided. Check -h or --help for more info.")
	elif args.project_id is None or args.project_id == "":
		print(f"[WARN!] No Project ID provided. Check -h or --help for more info.")
	elif args.merge_request_id is None or args.merge_request_id == "":
		print(f"[WARN!] No Merge Request ID provided. Check -h or --help for more info.")
	else:
		add_comment(args, message)