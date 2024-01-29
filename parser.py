import os, enum

Token = enum.Enum("Token", ['LETTER', 'DIGIT', 'ADD_OP', 'SUB_OP',
				  'MULT_OP', 'DIV_OP', 'MOD_OP', 'ASSIGN_OP',
				  'NUM_LIT', 'IDENT', 'DECIMAL', 'EOL', 'UNKNOWN'])

def isalpha(char):
	return char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def isdigit(num):
	return num in "0123456789"

class LexicalAnalyzer:
	def __init__(self, line):
		self.charClass = 0
		self.lexeme = ''
		self.nextChar = ''
		self.nextToken = 0
		self.line = line
		self.errorPos = 0
		self.output = []
		self.getChar()

	def operators(self):
		return {'+':Token.ADD_OP, '–':Token.SUB_OP,'-':Token.SUB_OP, '*':Token.MULT_OP, '/':Token.DIV_OP, '%':Token.MOD_OP}

	def lookup(self, ch):
		self.lexeme += self.nextChar # addChar
		if ch in self.operators():
			self.nextToken = self.operators().get(ch)
		elif ch == '=':
			self.nextToken = Token.ASSIGN_OP
		else:
			self.nextToken = Token.UNKNOWN
		return self.nextToken

	def getChar(self):
		# Checks each character of the sentence individually
		# Uses string splicing to remove the first character
		if len(self.line) > 0:
			self.nextChar, self.line = self.line[0], self.line[1:]
		else:
			self.nextChar = ''

		if self.nextChar == '':
			self.charClass = Token.EOL
		elif isalpha(self.nextChar):
			self.charClass = Token.LETTER
		elif isdigit(self.nextChar):
			self.charClass = Token.DIGIT
		elif self.nextChar == '.':
			self.charClass = Token.DECIMAL
		else:
			self.charClass = Token.UNKNOWN

	def getNonBlank(self):
		while self.nextChar == " " and self.nextChar:
			self.errorPos += 1
			self.getChar()

	def lex(self):
		self.lexeme = ''
		self.getNonBlank()

		match self.charClass:

			case Token.LETTER:
				self.lexeme += self.nextChar # addChar
				self.getChar()
				while self.charClass in [Token.LETTER, Token.DIGIT]:
					self.lexeme += self.nextChar # addChar
					self.getChar()
				self.nextToken = Token.IDENT

			case Token.DIGIT:
				self.lexeme += self.nextChar # addChar
				self.getChar()
				while self.charClass in [Token.DIGIT]:
					self.lexeme += self.nextChar # addChar
					self.getChar()
				if self.charClass == Token.DECIMAL:
					self.lexeme += self.nextChar # addChar
					self.getChar()
					while self.charClass in [Token.DIGIT]:
						self.lexeme += self.nextChar # addChar
						self.getChar()
				self.nextToken = Token.NUM_LIT

			case Token.EOL:
				self.nextToken = Token.EOL
				self.lexeme = "EOL"

			case _:
				self.lookup(self.nextChar)
				self.getChar()

		if self.nextToken is not Token.EOL:
			self.output.append((self.nextToken.name, self.lexeme))
		return self.nextToken

class SyntaxAnalyzer:
	def __init__(self, lex):
		self.lex = lex
		self.lex.lex()
		self.errorsFound = []		# [(msg, errLine), ...]
		self.errorLinePerErrorFound = []
		self.assignment_statement()

	def assignment_statement(self):
		# <assignment-statement> ->
		# <identifier> = (<identifier> | <numerical-literal>) {<operator> (<identifier> | <numerical-literal>)}
		self.identifier()

		if not self.lex.nextToken == Token.ASSIGN_OP:
			self.addError("expected an assignment operator")
		else:
			self.lex.errorPos += 1

		while True:
			self.lex.lex()

			if self.lex.nextToken == Token.IDENT:
				self.identifier()
			elif self.lex.nextToken in [Token.NUM_LIT, Token.ADD_OP, Token.SUB_OP]:
				self.numerical_literal()
			else:
				self.addError("expected an identifier or numerical-literal")
				self.lex.lex()

			if not self.operators() and self.lex.nextToken == Token.EOL:
				break

	def identifier(self): # <identifier> -> <letter> {<letter> | <digit>}

		for i, char in enumerate(self.lex.lexeme):
			if (i == 0 and not isalpha(char)) or not char.isalnum():
				self.addError("invalid identifier")
				self.lex.lex()
				return

		self.lex.errorPos += len(self.lex.lexeme)
		self.lex.lex()

	def numerical_literal(self): # <numerical-literal> -> [+|-] <digit> {<digit>} [. <digit> {<digit>}]
		if self.lex.nextToken in [Token.ADD_OP, Token.SUB_OP]:
			self.lex.lex()
			self.lex.errorPos += 1

		for digit in self.lex.lexeme:
			if (not isdigit(digit) and not digit == '.') or not isdigit(self.lex.lexeme[-1]):
				self.addError("invalid numerical literal")
				self.lex.lex()
				return

		self.lex.errorPos += len(self.lex.lexeme)
		self.lex.lex()

	def operators(self): # <operator> -> + | - | * | / | %
		if self.lex.nextToken in self.lex.operators().values():
			self.lex.errorPos += 1
			return True
		if not self.lex.nextToken == Token.EOL:
			self.addError("expected an operator")
		else:
			self.lex.errorPos += 1
		return False

	def addError(self, errorMsg):
		length = 1
		position = self.lex.errorPos
		if self.lex.nextToken != Token.EOL:
			length = len(self.lex.lexeme)

		errorLine = " "*position + "^"*length
		self.lex.errorPos += length
		self.errorsFound.append((f"Syntax error: {errorMsg} at position {position} (got: {self.lex.lexeme})\n", errorLine))

def main():
	fileNumber = 1
	output = open(f"parser_output.txt", "w")
	while f"{fileNumber}.txt" in os.listdir():

		print(f"\n{'#' * 20} {fileNumber}.txt {'#' * 20}")
		output.write(f"{'#' * 20} {fileNumber}.txt {'#' * 20}\n")

		with open(f"{fileNumber}.txt", 'r') as in_fp:
			lines = in_fp.read().split('\n')

		sentenceNumber = 1
		for line in lines:
			if not line:
				continue
			print("  Now parsing: ", line)
			output.write(f"{'=' * 10} Sentence {sentenceNumber}:\n")

			lexi = LexicalAnalyzer(line)
			synt = SyntaxAnalyzer(lexi)

			output.write(f" Sentence: {line}\n\n")

			if not synt.errorsFound:
				output.write(" --syntactically correct sentence--\n")
			else:
				print("    ERRORS FOUND")

			for error, errorLine in synt.errorsFound:
				output.write(f" {error}")
				output.write(f" Parsed: {line}\n")
				output.write(f" Error:  {errorLine}\n")

			output.write('\n')

			sentenceNumber += 1
			# output.write(f"\n Lexical analyzer output: {lexi.output}\n\n")

		output.write('\n')
		fileNumber += 1

	print("\nPlease check parser_output.txt for full details on the errors found.\n")
	output.close()

if __name__ == "__main__":
    main()
