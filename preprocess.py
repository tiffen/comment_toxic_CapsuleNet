import os
import re
import numpy as np
import pandas as pd
import config
from tqdm import tqdm
from multiprocessing import Pool
from keras.preprocessing import text, sequence
from bad_dict import get_bad_word_dict
from rake_parse import rake_parse

def get_raw_data(path):
    data = pd.read_csv(path)
    process_data = get_data(data)
    data['comment_text'] = process_data
    return data

def get_data(raw_data):
    raw_value = raw_data['comment_text'].fillna("_na_").values
    pool = Pool()
    processed_data = list(tqdm(pool.imap(text_parse, raw_value),total=raw_value.shape[0]))
    '''
    with open('debug.txt', 'w') as f:
       for l in processed_data:
           f.write(l+'\n')
    '''
    return processed_data 

def text_parse(text, remove_stopwords=False, stem_words=False):
    wiki_reg=r'https?://en.wikipedia.org/[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'
    url_reg=r'https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'
    url_reg2=r'www.[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'
    ip_reg='\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    WIKI_LINK=' WIKILINKREPLACER '
    URL_LINK=' URLLINKREPLACER '
    IP_LINK=' IPLINKREPLACER '
    #clear link
    # replace endline with '. '
    endline = re.compile(r'.?\n', re.IGNORECASE)
    text = endline.sub('. ', text)

    c = re.findall(wiki_reg, text)
    for u in c:
        text = text.replace(u, WIKI_LINK)
    c = re.findall(url_reg, text)
    for u in c:
        text = text.replace(u, URL_LINK)
    c = re.findall(url_reg2, text)
    for u in c:
        text = text.replace(u, URL_LINK)
    c = re.findall(ip_reg, text)
    for u in c:
        text = text.replace(u, IP_LINK)

    bad_word_dict = get_bad_word_dict()
    # Regex to remove all Non-Alpha Numeric and space
    special_character_removal = re.compile(r'[^A-Za-z\d!?*\'.,; ]', re.IGNORECASE)
    # regex to replace all numerics
    replace_numbers = re.compile(r'\b\d+\b', re.IGNORECASE)
    text = text.lower().split()
    # Optionally, remove stop words
    if remove_stopwords:
        stops = set(stopwords.words("english"))
        text = [w for w in text if not w in stops]
    text = " ".join(text)
    # Remove Special Characters
    text = special_character_removal.sub(' ', text)
    for k,v in bad_word_dict.items():
        # bad_reg = re.compile('[!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n ]'+ re.escape(k) +'[!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n ]')
        bad_reg = re.compile('[\W]?'+ re.escape(k) +'[\W]|[\W]' + re.escape(k) + '[\W]?') 
        text = bad_reg.sub(' '+ v +' ', text)
        '''
        bad_reg = re.compile('[\W]'+ re.escape(k) +'[\W]?')
        text = bad_reg.sub(' '+ v, text)
        bad_reg = re.compile('[\W]?'+ re.escape(k) +'[\W]')
        text = bad_reg.sub(v + ' ', text)
        '''

    # Replace Numbers
    text = replace_numbers.sub('NUMBERREPLACER', text)
    text =text.split()
    text = " ".join(text)

    if stem_words:
        text = text.split()
        stemmer = SnowballStemmer('english')
        stemmed_words = [stemmer.stem(word) for word in text]
        text = " ".join(stemmed_words)
    # rake parsing
    text = rake_parse(text)
    return text

def text_to_wordlist(text, remove_stopwords=False, stem_words=False):
    # Clean the text, with the option to remove stopwords and to stem words.
    # Convert words to lower case and split them
    wiki_reg=r'https?://en.wikipedia.org/[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'
    url_reg=r'https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'
    ip_reg='\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    WIKI_LINK=' WIKI_LINK '
    URL_LINK=' URL_LINK '
    IP_LINK=' IP_LINK '
    #clear link
    c = re.findall(wiki_reg, text)
    for u in c:
        text = text.replace(u, WIKI_LINK)
    c = re.findall(url_reg, text)
    for u in c:
        text = text.replace(u, WIKI_LINK)
    c = re.findall(wiki_reg, text)
    for u in c:
        text = text.replace(u, URL_LINK)
    c = re.findall(ip_reg, text)

    # Regex to remove all Non-Alpha Numeric and space
    special_character_removal = re.compile(r'[^A-Za-z\d!?*\' ]', re.IGNORECASE)
    # regex to replace all numerics
    replace_numbers = re.compile(r'\d+', re.IGNORECASE)

    # text = text.lower().split()
    text = text.split()
    # Optionally, remove stop words
    if remove_stopwords:
        stops = set(stopwords.words("english"))
        text = [w for w in text if not w in stops]

    text = " ".join(text)
    # Remove Special Characters
    text = special_character_removal.sub('', text)
    # Replace Numbers
    text = replace_numbers.sub('NUMBERREPLACER', text)
    # Optionally, shorten words to their stems
    if stem_words:
        text = text.split()
        stemmer = SnowballStemmer('english')
        stemmed_words = [stemmer.stem(word) for word in text]
        text = " ".join(stemmed_words)
    # Return a list of words
    return (text)


def get_label(raw_data):
    labels = ['toxic', 'severe_toxic',
              'obscene', 'threat',
              'insult', 'identity_hate']
    return raw_data[labels].values

def get_id(raw_data):
    return raw_data['id'].values

def process_data(train_data, test_data):
    # tokenizer = text.Tokenizer(num_words=config.MAX_WORDS,
    #     filters='!"#$%&()*+,-./:;<=>?@[\\]^`{|}~\t\n')
    tokenizer = text.Tokenizer(num_words=config.MAX_WORDS)
    tokenizer.fit_on_texts(train_data+test_data)
    train_tokenized = tokenizer.texts_to_sequences(train_data)
    test_tokenized = tokenizer.texts_to_sequences(test_data)
    train_data = sequence.pad_sequences(train_tokenized, maxlen = config.MAX_LENGTH)
    test_data = sequence.pad_sequences(test_tokenized, maxlen = config.MAX_LENGTH)
    return train_data, test_data, tokenizer.word_index

def get_word_embedding():
    data_path = 'data'
    # raw_embed = 'crawl-300d-2M.vec'
    raw_embed = 'glove.840B.300d.txt'
    EMBEDDING_FILE = os.path.join(data_path, raw_embed)
    embeddings_index = {}
    for line in open(EMBEDDING_FILE, "rb"):
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs
    print (len(embeddings_index))
    return embeddings_index

def get_embed_matrix(embeddings_index, word_index):
    nb_words = min(config.MAX_WORDS, len(word_index))
    embedding_matrix = np.empty((nb_words, config.EMBEDDING_DIM))
    # embedding_matrix = np.random.rand(nb_words, config.EMBEDDING_DIM)
    for word, i in word_index.items():
        if i >= config.MAX_WORDS:
            continue
        word_parts = word.split('_')
        embedding_vectors = [embeddings_index.get(w) for w in word_parts]
        embedding_vectors = np.array([v if v is not None else np.random.rand(config.EMBEDDING_DIM) for v in embedding_vectors])
        # embedding_matrix[i] = np.sum(embedding_vectors, axis=0)/np.linalg.norm(np.sum(embedding_vectors, axis=0))
        embedding_matrix[i] = np.sum(embedding_vectors, axis=0)/embedding_vectors.shape[0]

    return embedding_matrix

def fetch_data(aug=False):
    data_path = 'data'
    train = 'train.csv'
    test = 'test.csv'
    train_raw = get_raw_data(os.path.join(data_path, train))
    test_raw = get_raw_data(os.path.join(data_path, test))

    if aug:
        train_de = 'train_de.csv'
        train_fr = 'train_fr.csv'
        train_es = 'train_es.csv'
        train_de_raw = get_raw_data(os.path.join(data_path, train_de))
        train_es_raw = get_raw_data(os.path.join(data_path, train_es))
        train_fr_raw = get_raw_data(os.path.join(data_path, train_fr))
        train_raw = pd.concat([train_raw, train_de_raw, train_es_raw, train_fr_raw]).drop_duplicates('comment_text')
    train_data = list(train_raw['comment_text'].fillna("_na_").values)
    test_data = list(test_raw['comment_text'].fillna("_na_").values)
    train_label = get_label(train_raw)
        # print train_raw
        # train_de_data = get_data(train_de_raw)
        # train_de_label = get_label(train_de_raw)
        #train_es_data = get_data(train_es_raw)
        # train_es_label = get_label(train_es_raw)
        # train_fr_data = get_data(train_fr_raw)
        # train_fr_label = get_label(train_fr_raw)
        # train_data = train_data + train_de_data + train_fr_data + train_es_data
        # train_label = np.vstack((train_label, train_de_label, train_fr_label, train_es_label))

    train_data, test_data, word_index = process_data(train_data, test_data)
    return train_data, train_label, word_index

def fetch_test_data(aug=False):
    data_path = 'data'
    train = 'train.csv'
    test = 'test.csv'
    train_raw = get_raw_data(os.path.join(data_path, train))
    test_raw = get_raw_data(os.path.join(data_path, test))
    if aug:
        train_de = 'train_de.csv'
        train_fr = 'train_fr.csv'
        train_es = 'train_es.csv'
        train_de_raw = get_raw_data(os.path.join(data_path, train_de))
        train_es_raw = get_raw_data(os.path.join(data_path, train_es))
        train_fr_raw = get_raw_data(os.path.join(data_path, train_fr))
        train_raw = pd.concat([train_raw, train_de_raw, train_es_raw, train_fr_raw]).drop_duplicates('comment_text')
    train_data = list(train_raw['comment_text'].fillna("_na_").values)
    test_data = list(test_raw['comment_text'].fillna("_na_").values)
    train_data, test_data, word_index = process_data(train_data, test_data)
    test_id = get_id(test_raw)
    return test_data, test_id

if __name__ == '__main__':
    # embedding_dict = get_word_embedding()
    # data, label, word_index = fetch_data()
    # print(np.sum(label, axis=0).astype(float) / label.shape[0])
    # em = get_embed_matrix(embedding_dict, word_index)
    # print(em.shape)
    # reverse_idx = {v:k for k,v in word_index.items()}
    # reverse_idx[0] = 'NOTHING'
    # for i in range(100):
    #     print [reverse_idx[v] for v in data[i] if v!=0]

    data_path = 'data'
    train = 'train.csv'
    test = 'test.csv'
    train_raw = pd.read_csv(os.path.join(data_path, train))
    raw_value = train_raw['comment_text'].fillna("_na_").values
    # processed_data = []
    # for i, v in enumerate(raw_value):
    #     text_parse(v)
    a = raw_value[8306]
    word_index = {k:i+1 for i,k in enumerate(text_parse(a))}
    embedding_dict = get_word_embedding()
    em = get_embed_matrix(embedding_dict, word_index)

    '''
    r = Rake()
    r.extract_keywords_from_text(text_parse(a))
    print r.get_ranked_phrases()
    '''
