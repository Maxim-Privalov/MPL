from parser import *
from tokenizer import *


class JSTranslator:
    LOGIC_OP = {
        "and" : "&&",
        "or" : "||"
    }
    INSTR = {"BlockIF" : "if",
             "BlockELSEIF" : "else if",
             "BlockELSE" : "else",
             "BlockWHILE" : "while"}

    def __init__(self, root : Node):
        self.root = root

    def __translate(self, root : Node, translated_code : str) -> str:

        if (isinstance(root, Block)):
            block_type = root.__class__.__name__
            if (block_type != "GLOBAL"):
                translated_code[0] += root.parent.indent * " " + self.INSTR[block_type] + " "
                if (isinstance(root, (BlockIF, BlockELSEIF, BlockWHILE))):
                    self.__translate(root.condition, translated_code)
                translated_code[0] += "{\n"

            for line in root.lines:
                translated_code[0] += root.indent * " "
                self.__translate(line, translated_code)
                if not(isinstance(line, Block)):
                    translated_code[0] += ";\n"

            if (block_type != "GLOBAL"):
                translated_code[0] += root.parent.indent * " " + "}\n"


        if (isinstance(root, LiteralNumber)):
            translated_code[0] += root.value

        if (isinstance(root, StringType)):
            translated_code[0] += root.content
        
        if (isinstance(root, BooleanType)):
            if root.value:
                translated_code[0] += "true"
            else:
                translated_code[0] += "false"

        if (isinstance(root, (Variable, Keyword))):
            translated_code[0] += root.name

        if (isinstance(root, BinaryOperator)):

            if (root.op in ["=", "+=", "-="] and isinstance(root.left, Variable)):
                if root.left.declaration:
                    translated_code[0] += "let "
                self.__translate(root.left, translated_code)
                translated_code[0] += " " + root.op + " "
                self.__translate(root.right, translated_code)
            
            else:
                translated_code[0] += "("
                self.__translate(root.left, translated_code)
                if (root.op in ["and", "or"]):
                    translated_code[0] += " " + self.LOGIC_OP[root.op] + " "
                else:
                    translated_code[0] += " " + root.op + " "
                self.__translate(root.right, translated_code)
                translated_code[0] += ")"

        if (isinstance(root, UnaryOperator)):
            if (root.op == "not"):
                translated_code[0] += "!("
            else:
                translated_code[0] += root.op + "("
            self.__translate(root.operand, translated_code)
            translated_code[0] += ")"

        if (isinstance(root, CallOperator)):
            if (root.name == "print"):
                translated_code[0] += "console.log("
            else:
                translated_code[0] += root.name + "("
            for index, arg in enumerate(root.arguments):
                self.__translate(arg, translated_code)
                if index != len(root.arguments) - 1:
                    translated_code[0] += ", "
            translated_code[0] += ")"

    
    def translate(self):
        translated_code = [""]
        self.__translate(self.root, translated_code)
        return translated_code[0]
    
def main():
    code = """
1 + print(print(1))
if 5 == 4:
    print("asass")
    if (True) or (12 == 98):
     ++print("1121")
     else:
            print("12122")
            if 4 == 1:
             print("2112")
print("В жопу не долбись")"""

    code1 = """
print("hello" + 1001, print("111", 101))
ima_star=11111
im_not_star=1000
print("Hello world")
if (True == 1):
    print("Hell Yeah")
    headda = "hello"
elif False == 0:
    im_not_star = 10.0
else:
    print("Oh, no!")
    ima_star=0

while ima_star > im_not_star or True:
    print("Hey Hey Hey!")
"""

    test_code = """
health = 100
mana = 70
level = 5
gold = 250
enemies = 3
potions = 2

print("=== Приключение началось ===")
print("Здоровье:", health, "| Мана:", mana)
print("Уровень:", level, "| Золото:", gold)

if health > 50:
    print("Ты в хорошей форме!")
    if mana >= 80:
        print("  Мана полная — можно колдовать мощные заклинания!")
    elif mana >= 40:
        print("  Маны достаточно для обычных заклинаний.")
        if level >= 5:
            print("    На твоём уровне доступны огненные шары!")
    else:
        print("  Мана на исходе — лучше экономить.")
else:
    print("Здоровье низкое — будь осторожен!")
    if potions > 0:
        print("  К счастью, у тебя есть зелья лечения.")
        potions = potions - 1
        health = health + 30
        print("  Выпито зелье. Здоровье теперь:", health)
    else:
        print("  Зелий нет — ситуация критическая.")

print("Впереди", enemies, "врага(-ов).")

counter = 0
total_gold_earned = 0

while enemies > 0 or counter < 4:
    print("--- Бой", counter + 1, "---")
    print("Осталось врагов:", enemies)
    
    if health <= 30:
        print("  Здоровье критически низкое!")
        if potions > 0:
            print("  Автоматически использовано зелье.")
            potions = potions - 1
            health = health + 40
        else:
            print("  Зелий больше нет — отступаем!")
            break
    else:
        print("  Бой продолжается нормально.")
    
    if mana > 20:
        print("  Использовано заклинание — урон врагам!")
        enemies = enemies - 1
        mana = mana - 15
    else:
        print("  Маны мало — атака мечом.")
        enemies = enemies - 1
    
    gold_drop = 45
    print("  Победа над врагом! Получено золота:", gold_drop)
    gold = gold + gold_drop
    total_gold_earned = total_gold_earned + gold_drop
    counter = counter + 1

print("=== Бои завершены ===")
print("Осталось врагов:", enemies)
print("Итоговое золото:", gold)
print("Потрачено зелий:", 2 - potions)
print("Здоровье в конце:", health)
print("Мана в конце:", mana)
print("Спасибо за игру!")
    """
    tk = Tokenizer(test_code)
    token_list = tk.tokenize()
    # for i in range(len(token_list)):
    #    print(i+1, token_list[i])
    p = Parser(token_list)
    root = p.parseBlock(GLOBAL)
    # print(root)
    # Parser.bypass(root, 0)



    t = JSTranslator(root)
    print(t.translate())

if __name__ == '__main__':

    main()
