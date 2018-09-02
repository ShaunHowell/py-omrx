def convert_pvalue_to_symbol(pvalue, legend=None):
    legend = {'*': 0.05, '**': 0.01, '***': 0.001} if legend == None else legend
    for symbol, val in sorted(legend.items(), key=lambda item: item[1]):
        if pvalue < val:
            return symbol
    return ''