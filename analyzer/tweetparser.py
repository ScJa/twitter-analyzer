import re

AT_RE = re.compile(r"\@([\w]+)")

def extract_ats(text):
    matches = AT_RE.findall(text)
    return [match for match in matches]

if __name__ == '__main__':
    import sys
    arg = sys.argv[1]
    print(arg)
    print(extract_ats(arg))
