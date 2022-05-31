
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import seaborn as sns
import os, inspect

"""
- csv based on data scraped from: http://johnstoniatexts.x10host.com/homer/iliaddeaths.htm 
(cf. https://www.thoughtco.com/deaths-in-the-iliad-121298)
- cleaned (mostly typos in names); extracted weapons used based on comments + 
    supplied some missing (still definitily incomplete, though)
- N.B. "line numbers refer to the on-line translation by Ian Johnston"
"""
 
csv_file = 'iliad_killings.csv'

# get current dir
path = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

df = pd.read_csv(f'{path}\{csv_file}', dtype={'book_line': str})

# number of books Iliad
book_range = np.arange(1,25,1)

# func to split data on agent_type and add cumsums
def split_df_on_agent(df, book_range):
    
    # group killings/woundings by book, agent
    actions = df.groupby(['book','agent_type','action'])['action'].count()
    
    # unstack multilevel index, and reset
    actions = actions.unstack(len(actions.index.levels)-1).reset_index()
    
    # add cumsum
    actions['cumsum_kills'] = actions.groupby('agent_type')['kills'].cumsum()

    # empty df to merge
    empty = pd.DataFrame(index=book_range)

    list_dfs = list()

    # create dfs for Greeks/Trojans only
    for agent in df.agent_type.unique():
        df_temp = actions.loc[actions.agent_type == agent,['book','kills',
                                 'cumsum_kills']].set_index('book', drop=True)
        df_temp = df_temp.merge(empty, how='outer', left_index=True, right_index=True)
        
        df_temp['cumsum_kills'].ffill(inplace=True)
        df_temp.replace(np.nan, 0, inplace=True)
        df_temp.name = agent
        list_dfs.append(df_temp)
    
    return list_dfs

# call func to create df 'Greeks', 'Trojans'
list_dfs = split_df_on_agent(df, book_range)

# =============================================================================
# # create plots
# =============================================================================

# set use of seaborn
sns.set()

# assign books to x-axis
x = book_range

# set up plot
fig, (ax2, ax1) = plt.subplots(2, sharex=True, sharey=False, figsize=(10, 6))

# define lims for x-axis, y-axes:

# counts per books
ax1.set_ylim([0, 45])

# cumsum plots
ax2.set_ylim([0, 250])
plt.xlim(1, 24)

# create list var for lin regressoins params
store_popt = list()

# helper func for trendlines
def func(x, a):
    return a * x

# loop to create subplots
for df in list_dfs:
    
    # select colors for both sides
    if df.name == 'Greek':
        my_color = 'darkorange'
    else:
        my_color = 'darkblue'
        
    # create bar for count
    ax1.bar(x, df['kills'], label = f'kills_by_{df.name}s', color=my_color)
    
    # create plot for cumsum
    ax2.plot(x, df['cumsum_kills'], label = f'cs_kills_by_{df.name}s', color=my_color)
    
    # add trend line
    popt, pcov = curve_fit(func, x, df['cumsum_kills'])
    
    # capture params for defining ratio
    store_popt.append(popt)
    
    # add plot trend line
    ax2.plot(x, func(x, popt), 'r--', label = f'({df.name[0:2]}) y = {popt[0]:.2f}x')

# finishing touches
ax1.legend()
ax2.legend()

quote = \
"""
Δηΐφοβ’ ἦ ἄρα δή τι ἐΐσκομεν ἄξιον εἶναι
τρεῖς ἑνὸς ἀντὶ πεφάσθαι; ἐπεὶ σύ περ εὔχεαι οὕτω.

"Deiphobos, do we now suppose perhaps that fair requital has been made
—killing three men in exchange for one—since you boast in this way?" — Idomeneus (Il. 13.446-7)
"""

# plt.text(0,-10, teststr, fontsize=14)
plt.gcf().text(0.1, 1, quote, fontsize=13)

plt.xticks(book_range)
plt.xlabel('books Iliad')
plt.suptitle(f'killings in the Iliad (ratio {(store_popt[0] / store_popt[1])[0]:.2f}:1)')
plt.show()