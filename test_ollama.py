import requests, time
start = time.time()
r = requests.post('http://localhost:11434/api/generate', json={'model':'llama3.2','prompt':'Generate a 3 question MCQ quiz about OS as JSON','stream':False,'format':'json'}, timeout=90)
print(f'Time: {time.time()-start:.1f}s')
print(r.json().get('response','')[:300])
