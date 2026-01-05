class Tokenizer:

    OPERATORS = ["==", "!=", "+=", "-=", "*=", "/=", "++", "--", "<=", ">=", "+", "-", "*", "/", "%", "=", "<", ">", "(", ")"]
    KEYWORDS = ["print", "if", "else", "elif", "while", "or", "not", "and", "True", "False", "break", "continue", ":", ","]
    
    def __init__(self, raw):
        self.raw = raw
    
    def tokenize(self) -> list[str]:
        token_lines = []
        raw_lines = self.raw.splitlines()
        for li, raw_line in enumerate(raw_lines):
            
            if (raw_line.strip() == ""): 
                continue

            token_list  = []
            cp = 0

            indent_level = 0
            print(raw_line)
            while (indent_level < len(raw_line) and (raw_line[indent_level] == " " or raw_line[indent_level] == "\t")):
                indent_level += 1

            while cp < len(raw_line):
                is_unexpected = True

                # spaces
                if raw_line[cp] == " ":
                    cp += 1
                    continue

                # names
                if not(raw_line[cp].isdigit() or raw_line[cp] in [" ", "\"", ")", ":", ","]):
                    token = ""
                    iskeyword = False
                    isvar = False
                    for op in self.OPERATORS + self.KEYWORDS:
                        control_length = len(op)
                        if (cp + control_length + 1 <= len(raw_line)) and (raw_line[cp:cp + control_length + 1] in [op + " ", op + ":", op + "("]):
                            iskeyword = True
                            break

                    while cp < len(raw_line) and not(iskeyword) and not(raw_line[cp] in [" ", "\"", ")", ",", ":"] + self.OPERATORS):
                        isvar = True
                        token += raw_line[cp]
                        cp += 1
                    

                    if isvar:
                        token_list.append(token)
                        continue
                        



                # digits
                if raw_line[cp].isdigit():
                    token = ""
                    while cp < len(raw_line) and (
                            raw_line[cp].isdigit() or (
                            raw_line[cp] == "." and raw_line[cp+1].isdigit()
                            )
                        ):

                        token += raw_line[cp]
                        cp += 1
                    token_list.append(token)
                    continue
                
                #strings
                if raw_line[cp] == '"':
                    token = raw_line[cp]
                    cp += 1
                    while cp < len(raw_line) and raw_line[cp] != '"':
                        token += raw_line[cp]
                        cp += 1
                    
                    if cp >= len(raw_line):
                        raise SyntaxError(f'expected " in line {li}')
                    
                    else:
                        token += raw_line[cp]
                        cp += 1
                        token_list.append(token)
                    continue

                # operators and keywords
                for op in self.OPERATORS + self.KEYWORDS:
                    control_length = len(op)
                    if (raw_line[cp:cp + control_length] == op):
                        is_unexpected = False
                        token_list.append(op)
                        cp += control_length - 1
                        break

                if is_unexpected:
                    print("unexpected symbol: " + raw_line[cp])
                    break
                cp += 1

            token_lines.append((token_list, indent_level))

        return token_lines