from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random
import re
from urllib.parse import urlparse
from pathlib import Path


def load_questions():
    if not Path("questions.json").exists():
        return []
    with open(Path("questions.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("questions", [])


def save_questions(questions):
    with open(Path("questions.json"), "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, indent=2)


def find_question(qid):
    questions = load_questions()
    for q in questions:
        if q["id"] == qid:
            return q
    return None

class Handler(BaseHTTPRequestHandler):

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_no_content(self):
        self.send_response(204)
        self.end_headers()

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except:
            return None

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/questions/random":
            questions = load_questions()
            if not questions:
                return self.send_json(404, {"error": "no questions"})
            return self.send_json(200, random.choice(questions))
        if path == "/questions":
            questions = load_questions()
            if not questions:
                return self.send_json(404, {"error": "no questions"})
            return self.send_json(200, questions)

        return self.send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/questions":
            return self.send_json(404, {"error": "not found"})

        data = self.read_json()
        if not data or not isinstance(data.get("question_text"), str) or not data["question_text"].strip():
            return self.send_json(400, {"error": "expected {question_text:str}"})

        questions = load_questions()

        next_id = (max((q.get("id", 0) for q in questions), default=0) + 1)

        new_q = {
            "id": next_id,
            "question_text": data["question_text"].strip()
        }

        questions.append(new_q)
        save_questions(questions)

        return self.send_json(201, new_q)

    def do_PUT(self):
        path = urlparse(self.path).path
        match = re.fullmatch(r"/questions/(\d+)", path)
        if not match:
            return self.send_json(404, {"error": "not found"})

        qid = int(match.group(1))
        data = self.read_json()
        if not data or "question_text" not in data:
            return self.send_json(400, {"error": "invalid body"})

        questions = load_questions()

        for q in questions:
            if q["id"] == qid:
                q["question_text"] = data["question_text"]
                save_questions(questions)
                return self.send_json(200, q)

        return self.send_json(404, {"error": "question not found"})

    def do_DELETE(self):
        path = urlparse(self.path).path
        match = re.fullmatch(r"/questions/(\d+)", path)
        if not match:
            return self.send_json(404, {"error": "not found"})

        qid = int(match.group(1))
        questions = load_questions()
        new_questions = [q for q in questions if q["id"] != qid]

        if len(new_questions) == len(questions):
            return self.send_json(404, {"error": "question not found"})

        save_questions(new_questions)
        return self.send_no_content()



def main():
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running at http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()