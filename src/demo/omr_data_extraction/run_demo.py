from omr.preprocessing import preprocess_folder
from omr.processing import *

answers = answers_from_images('data/images','data/ext/omr_form_designs.json')

print(answers.to_string())

answers.to_csv('data/exam_results/demo_output.csv',index=False)