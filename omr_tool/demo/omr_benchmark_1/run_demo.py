from core.exam_marksheet.processing import process_exam_marksheet_folder

# if Path('data/images').exists():
#     for file_path in Path('data/images').iterdir():
#         os.remove(str(file_path))
#
# preprocess_folder('data/scans', 'data/images')

answers = process_exam_marksheet_folder('data/images', 'data/ext/omr_form_designs.json', 'data/exam_results')

print(answers.to_string())
print('output csv should be in data/exam_results.csv')
find_omr_accuracy('data/exam_results/omr_output.csv',
                  'data/exam_results/human_processed_exam_results.csv',
                  'data/ext/omr_form_designs.json')
