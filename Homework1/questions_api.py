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

def load_answers():
    if not Path("answers.json").exists():
        return []
    with open(Path("answers.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("answers", [])

def save_answers(answers):
    with open(Path("answers.json"), "w", encoding="utf-8") as f:
        json.dump({"answers": answers}, f, ensure_ascii=False, indent=2)

def find_answer(aid):
    answers = load_answers()
    for a in answers:
        if a["id"] == aid:
            return a
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
        if path == "/answers/random":
            answers = load_answers()
            if not answers:
                return self.send_json(404, {"error": "no answers"})
            return self.send_json(200, random.choice(answers))

        return self.send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/questions":
            data = self.read_json()
            if not data or not isinstance(data.get("question_text"), str) or not data["question_text"].strip():
                return self.send_json(400, {"error": "expected {question_text:str}"})

            questions = load_questions()
            next_id = max((q.get("id", 0) for q in questions), default=0) + 1

            new_q = {"id": next_id, "question_text": data["question_text"].strip()}
            questions.append(new_q)
            save_questions(questions)
            return self.send_json(201, new_q)

        if path == "/answers":
            data = self.read_json()
            if not data:
                return self.send_json(400, {"error": "invalid json"})

            qid = data.get("question_id")
            text = data.get("answer_text")

            if not isinstance(qid, int) or not isinstance(text, str) or not text.strip():
                return self.send_json(400, {"error": "expected {question_id:int, answer_text:str}"})

            if find_question(qid) is None:
                return self.send_json(404, {"error": "question_id not found"})

            answers = load_answers()
            next_id = max((a.get("id", 0) for a in answers), default=0) + 1

            new_a = {"id": next_id, "question_id": qid, "answer_text": text.strip()}
            answers.append(new_a)
            save_answers(answers)
            return self.send_json(201, new_a)

        return self.send_json(404, {"error": "not found"})

    def do_PUT(self):
        path = urlparse(self.path).path

        match = re.fullmatch(r"/questions/(\d+)", path)
        if match:
            qid = int(match.group(1))
            data = self.read_json()
            if not data or not isinstance(data.get("question_text"), str) or not data["question_text"].strip():
                return self.send_json(400, {"error": "expected {question_text:str}"})

            questions = load_questions()
            for q in questions:
                if q["id"] == qid:
                    q["question_text"] = data["question_text"].strip()
                    save_questions(questions)
                    return self.send_json(200, q)

            return self.send_json(404, {"error": "question not found"})

        match = re.fullmatch(r"/answers/(\d+)", path)
        if match:
            aid = int(match.group(1))
            data = self.read_json()
            if not data or not isinstance(data.get("answer_text"), str) or not data["answer_text"].strip():
                return self.send_json(400, {"error": "expected {answer_text:str}"})

            answers = load_answers()
            for a in answers:
                if a["id"] == aid:
                    a["answer_text"] = data["answer_text"].strip()
                    save_answers(answers)
                    return self.send_json(200, a)

            return self.send_json(404, {"error": "answer not found"})

        return self.send_json(404, {"error": "not found"})

    def do_DELETE(self):
        path = urlparse(self.path).path

        match = re.fullmatch(r"/questions/(\d+)", path)
        if match:
            qid = int(match.group(1))
            questions = load_questions()
            new_questions = [q for q in questions if q["id"] != qid]

            if len(new_questions) == len(questions):
                return self.send_json(404, {"error": "question not found"})

            save_questions(new_questions)
            return self.send_no_content()

        match = re.fullmatch(r"/answers/(\d+)", path)
        if match:
            aid = int(match.group(1))
            answers = load_answers()
            new_answers = [a for a in answers if a["id"] != aid]

            if len(new_answers) == len(answers):
                return self.send_json(404, {"error": "answer not found"})

            save_answers(new_answers)
            return self.send_no_content()

        return self.send_json(404, {"error": "not found"})


def main():
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running at http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()