class Message:
    def __init__(self, content, role, timestamp=None):
        self.content = content
        self.role = role
        self.timestamp = timestamp

    def as_dict(self):
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}


class Conversation:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.messages = []

    def add(self, content, role, timestamp=None):
        self.messages.append(Message(content, role, timestamp))

    def add_multiple(self, messages):
        self.messages.extend(messages)

    def reset(self):
        self.messages = []

    def last_timestamp(self):
        if len(self.messages) == 0:
            return None
        for message in reversed(self.messages):
            if message.timestamp is not None:
                return message.timestamp
        return None

    def get_history(self, with_system=False):
        if with_system:
            return [{"role": "system", "content": self.system_prompt, "timestamp": None}] + [message.as_dict() for message in self.messages]
        return [{"role": message.role, "content": message.content} for message in self.messages]

    def lines(self, with_system=False):
        rows = [message.as_dict() for message in self.messages]
        if with_system:
            rows = [{"role": "system", "content": self.system_prompt, "timestamp": None}] + rows
        return rows