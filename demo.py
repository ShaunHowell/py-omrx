import pandas as pd
import matplotlib.pyplot as plt, mpld3
import seaborn as sns
import numpy as np


def compare_categorical(df, target_col):
    html_string = ''
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']
    # Find categorical column labels
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    # Compare performance between all options for each category
    for col in categorical_cols:
        html_string += '<h1>Comparison by {}</h1>\n'.format(col.lower())
        col_fig, (kde_axes, bar_axes) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})
        kde_axes.set_xlim(df[target_col].min(), df[target_col].max())
        bar_axes.set_xlim(df[target_col].min(), df[target_col].max())
        averages = []
        categories = df[col].unique()
        for i, option in enumerate(categories):
            sns.kdeplot(df[df[col] == option][target_col], shade=True, label=option, ax=kde_axes, color=colors[i])
            averages.append(df[df[col] == option][target_col].mean())
        bar_axes.barh(np.arange(len(categories)), averages, color=colors, tick_label=categories)
        html_string = html_string + mpld3.fig_to_html(col_fig) + '\n'
    return html_string


df = pd.read_csv('data/Y1T3_exam_results.csv')
df = df.dropna()  # TODO: more data cleaning here to fill where possible and assert more cleanliness
df = df[df['Student Level'] != '0']

with open('reports/demo_report.html', 'w') as out_file:
    out_file.write(compare_categorical(df, 'Percentage'))
