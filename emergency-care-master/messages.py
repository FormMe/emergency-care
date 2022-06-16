
import json
from os import path


class PetEmergency:
    def __init__(self, id, name, problems):
        self.id = id
        self.name = name
        self.problems = problems
    
    def __eq__(self, o):
        return self.id == o

    def __getitem__(self, problem_id):
        try:
            i = self.problems.index(problem_id)
            return self.problems[i]
        except ValueError:
            return None

class Problem:
    def __init__(self, id, title, msg):
        self.id = id
        self.title = title
        self.msg = msg

    def __eq__(self, o):
        return self.id == o

class Messages:
    def __init__(self, path):
        with open(path) as f:
            meta = json.load(f)

        self.commands = self.read_commands(meta)
        self.emergency = self.read_emergency(meta)

    def read_commands(self, meta):
        commands = dict()
        for command, msg_path in meta["commands"].items():
            msg_path = path.join("data","commands", msg_path)
            with open(msg_path) as f:
                msg = f.read()
                commands[command] = msg
        return commands

    def read_emergency(self, meta):
        emergency = dict()
        for pet_id, pet_meta in meta["emergency"].items():
            pet_name = pet_meta["name"]
            problems = []
            for problem_id, problem_meta in pet_meta["problems"].items():
                title = problem_meta['title']
                msg_path = path.join("data", "emergency", pet_id, problem_meta["msg"])
                with open(msg_path) as f:
                    msg = f.read()
                problem = Problem(problem_id, title, msg)
                problems.append(problem)

            emergency[pet_id] = PetEmergency(pet_id, pet_name, problems)
        return emergency

