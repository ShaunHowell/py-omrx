from omr.exam_marksheet.processing import *

answers = process_exam_marksheet_folder('data/images', 'data/ext/omr_form_designs.json', 'data/exam_results')

print(answers.to_string())
print('output csv should be in data/exam_results.csv')