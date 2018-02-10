import os
TESTS_OUTPUT_PATH = 'tests/out'
if not os.path.exists(TESTS_OUTPUT_PATH):
    os.mkdir(TESTS_OUTPUT_PATH)
for file_name in os.listdir(TESTS_OUTPUT_PATH):
    if file_name == '.gitignore':
        continue
    os.remove('{}/{}'.format(TESTS_OUTPUT_PATH,file_name))
