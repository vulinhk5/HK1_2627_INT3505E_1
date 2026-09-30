
from flask import Flask, jsonify, request
from data import posts, new_id
 
app = Flask(__name__)
 
@app.get("/api/posts")
def list_posts():
    result = list(posts.values())
    author_id = request.args.get("author_id", type=int)
    if author_id:
        result = [p for p in result if p["author_id"] == author_id]
    return jsonify(result), 200
 
@app.post("/api/posts")
def create_post():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title required"}), 400
    post_id = new_id()
    post = {
        "id": post_id,
        "title": data["title"],
        "content": data.get("content", ""),
        "author_id": data.get("author_id"),
    }
    posts[post_id] = post
    return jsonify(post), 201
 
@app.get("/api/posts/<int:post_id>")
def get_post(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "post not found"}), 404
    return jsonify(post), 200
 
@app.put("/api/posts/<int:post_id>")
def update_post(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "post not found"}), 404
    data = request.get_json()
    post["title"] = data.get("title", post["title"])
    post["content"] = data.get("content", post["content"])
    return jsonify(post), 200
 
@app.delete("/api/posts/<int:post_id>")
def delete_post(post_id):
    if post_id not in posts:
        return jsonify({"error": "post not found"}), 404
    del posts[post_id]
    return "", 204
 
 
if __name__ == "__main__":
    app.run(debug=True)