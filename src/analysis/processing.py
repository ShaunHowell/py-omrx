

# def categorial_p_test(df, independant_col, dependant_col):
#     target_data = df[dependant_col]
#     averages = []
#     options_target_data = []
#     options = df[independant_col].unique()
#     # create kde plot (~smooth frequency distribution) and bar chart of means
#     for i, option in enumerate(options):
#         option_target_data = df[df[independant_col] == option][dependant_col]
#         try:
#             sns.kdeplot(option_target_data, shade=True, label=option, ax=kde_axes, color=colors[i])
#         except np.linalg.linalg.LinAlgError:
#             print('ERROR: only {} students with {}: {}, and all had the same {}: not plotting'.format(
#                 len(options_target_data), independant_col, option, dependant_col))
#         averages.append(option_target_data.mean())
#         options_target_data.append(option_target_data)
#     bar_axes.barh(np.arange(len(options)), averages, color=colors, tick_label=options)
#     # t-test for each option: is the difference of its mean to the mean of the other data statistically significant?
#     ttest_results = []
#     for i, option_target_data in enumerate(options_target_data):
#         comparison_data = options_target_data[:i] + options_target_data[i + 1:]
#         option_ttest_results = [
#             convert_pvalue_to_symbol(
#                 stats.ttest_ind(option_target_data, alt, equal_var=False, nan_policy='raise')[1])
#             for alt in comparison_data]
#         option_ttest_results.insert(i, '-')
#         ttest_results.append(option_ttest_results)
#     ttest_df = pd.DataFrame(ttest_results, index=options, columns=options)

