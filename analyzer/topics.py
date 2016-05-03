import re, logging
#from nltk.stem.snowball import SnowballStemmer

TOPICS = None
WORD_RE = re.compile(r"[^\w]")
#STEMMER = SnowballStemmer('english')

def load_topics(mongo):
    global TOPICS
    TOPICS = []
    for ad in mongo.get_all_advertisements():
        TOPICS.append({
            'name': ad['name'].strip(),
            'keywords': [word.strip().lower() for word in ad['keywords']]
        })

def mine_topics(text):
    #words = stem_list(split_words(text.lower()))
    text = text.lower()
    topics = set()

    for topic in TOPICS:
        for word in topic['keywords']:
            if word in text:
                topics.add(topic['name'])

    return topics

def stem_list(strings):
    #return [STEMMER.stem(s) for s in strings]
    raise Exception('Uncomment stemmer in topics.py!')

def split_words(string):
    return WORD_RE.sub(" ", string).split()
