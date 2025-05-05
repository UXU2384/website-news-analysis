import pandas as pd
from collections import Counter


df = pd.read_csv('app_top_person\dataset\ithome_news_preprocessed.csv',sep='|')
news_categories=['AI','雲端','資安']
allowedNE=['PERSON']

def NerToken(word, ner, idx):
    # print(ner,word)
    return ner,word

for ner,key in eval(df.entities[0]):
    print(ner,key)

def ne_word_frequency( a_news_ne ):
    filtered_words =[]
    for ner,word in a_news_ne:
        if (len(word) >= 2) & (ner in allowedNE):
            filtered_words.append(word)
    counter = Counter( filtered_words )
    return counter.most_common( 200 )

def get_top_ner_words():
    top_cate_ner_words={}
    words_all=[]
    for category in news_categories:
        df_group = df[df.category==category]
        words_group=[]
        for row in df_group.entities:
            words_group += eval(row)

        words_all += words_group
        topwords = ne_word_frequency( words_group )
        top_cate_ner_words[category] = topwords
    
    topwords_all = ne_word_frequency(words_all)
    top_cate_ner_words['全部'] = topwords_all
    return list(top_cate_ner_words.items())

hotPersons = get_top_ner_words()
df_hotPersons = pd.DataFrame(hotPersons, columns = ['category','top_keys'])
df_hotPersons.to_csv('app_top_person\dataset\itnews_top_person_by_category_via_ner.csv')