import os
TESTS_OUTPUT_PATH = 'tests/out'
for file_name in os.listdir(TESTS_OUTPUT_PATH):
    if file_name == '.gitignore':
        continue
    os.remove('{}/{}'.format(TESTS_OUTPUT_PATH,file_name))