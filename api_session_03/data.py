posts = {
    1: {"id": 1, "title": "Euphoria", "content": "a feeling of extreme happiness or confidence:", "author_id": 1},
    2: {"id": 2, "title": "Singularity", "content": "the quality of being strange", "author_id": 2},
    3: {"id": 3, "title": "Epiphany", "content": "a moment when you suddenly feel that you understand, or suddenly become conscious of, something that is very important to you", "author_id": 3},
    4: {"id": 4, "title": "Stigma", "content":"a strong feeling of disapproval that most people in a society have about something, especially when this is unfair", "author_id": 4}, 
}
 
_next_id = 5
 
 
def new_id():
    global _next_id
    current = _next_id
    _next_id += 1
    return current