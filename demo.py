import pandas as pd
import matplotlib.pyplot as plt, mpld3
import seaborn as sns


def compare_categorical(df, target_col):
    html_string = ''
    # Find categorical column labels
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    # Compare performance between all options for each category
    for col in categorical_cols:
        html_string += '<h1>Comparison by {}</h1>\n'.format(col.lower())
        plt.figure()
        for option in df[col].unique():
            sns.kdeplot(df[df[col] == option][target_col], shade=True, label=option)
        html_string = html_string + mpld3.fig_to_html(plt.gcf()) + '\n'
    return html_string


df = pd.read_csv('data/Y1T3_exam_results.csv')
df = df.dropna()  # TODO: more data cleaning here to fill where possible and assert more cleanliness
df = df[df['Student Level'] != '0']

with open('reports/demo_report.html', 'w') as out_file:
    out_file.write(compare_categorical(df, 'Percentage'))
