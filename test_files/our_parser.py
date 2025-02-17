from scanner import lex_analyze

class Parser:
    """Implementation of a class with methods to parse the token string returned by the scanner.
    Each method corresponds to a non-terminal in the refactored BNF. The token string generated by the scanner
    is taken as input in the constructor.
    """

    def __init__(self, input_string):
        """Class constructor.

        Args:
            input_string (List<Tuple<str, *>>): Token string returned by the scanner.
        """
        self.tokens = lex_analyze(input_string)  # Token string returned from the scanner as a List object (token, lexeme)
        self.current_token = None  # Current token being consumed
        self.index = 0  # Index of the current token in the list of tokens
        self.errors = []  # List of syntactical errors encountered by the parser

    def parse(self):
        """Starts the parsing process.

        Returns:
            (Node): Head node of the parse tree that has been built, otherwise None.
        """
        self.consume_token()
        parse_tree = self.program()
        if not self.errors:
            return parse_tree
        else:
            return None

    def consume_token(self):
        """Advances the 'current_token' pointer to the next token in the token string.
        """
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]  # Set the current token as the tuple in the current index of the token string
            self.index += 1
        else:
            self.current_token = None

    def program(self):
        """Starts off the parsing process from the start symbol, by calling `statement_list()`.

        Returns:
            (Node): A node representing all tokens from the start symbol.
        """
        program_node = Node("program")
        statement_list_node = self.statement_list()
        if statement_list_node:
            program_node.add_child(statement_list_node)
        else:
            self.errors.append(f"Expected a statement_list, found {self.current_token[0] if self.current_token else 'end of input'}")
        return program_node

    def statement_list(self):
        """Parses a list of statements by iteratively calling `statement()` until there are no more tokens.

        Returns:
            (Node): A node representing all tokens under a `statement_list` non-terminal.
        """
        statement_list_node = Node("statement_list")
        while self.current_token:
            statement_node = self.statement()
            if statement_node:
                statement_list_node.add_child(statement_node)
            else:
                break
        return statement_list_node

    def statement(self):
        """Parses a single statement. This can be an assignment_statement, conditional_statement, or loop_statement.

        Returns:
            (Node): A node representing all tokens from the `statement` non-terminal.
        """
        statement_node = None
        if self.match_token('IDENTIFIER'):
            statement_node = self.assignment_statement()
        elif self.match_token('CONDITIONAL_KEYWORD'):
            statement_node = self.conditional_statement()
        elif self.match_token('LOOP_KEYWORD'):
            statement_node = self.loop_statement()
        else:
            self.errors.append(f"Expected a statement type, found {self.current_token[0]}: {self.current_token[1]}")
            self.consume_token()  # Advance token index if no statement matches
        self.newline()  # Consume newline after each statement
        return statement_node

    
    def skip_whitespace(self):
        """Skips whitespace tokens."""
        while self.match_token('WHITESPACE'):
            self.consume_token()

    def assignment_statement(self):
        """Parses an assignment statement.

        Returns:
            (Node): A node representing all tokens under the `assignment_statement` non-terminal.
        """
        assignment_node = None
        if self.match_token('IDENTIFIER'):
            identifier_node = Node("identifier", self.current_token[1])
            self.consume_token()
            self.skip_whitespace()  # Skip any whitespace before the assignment operator
            self.expect_token('ASSIGNMENT_OPERATOR')
            assignment_operator_node = Node("assignment_operator", self.current_token[1])
            self.consume_token()
            self.skip_whitespace()  # Skip any whitespace after the assignment operator
            expression_node = self.expression()
            if expression_node:
                assignment_node = Node("assignment_statement")
                assignment_node.add_child(identifier_node)
                assignment_node.add_child(assignment_operator_node)
                assignment_node.add_child(expression_node)
            else:
                self.errors.append(f"Expected an expression, found {self.current_token[0]}: {self.current_token[1]}")
        else:
            self.errors.append(f"Expected an identifier, found {self.current_token[0]}: {self.current_token[1]}")
        return assignment_node

    def conditional_statement(self):
        """Parses a conditional statement.

        Returns:
            (Node): A node representing all tokens under the `conditional_statement` non-terminal.
        """
        conditional_node = None
        self.skip_whitespace()
        if self.match_token('CONDITIONAL_KEYWORD'):
            conditional_node = Node("conditional_statement", self.current_token[1])
            self.consume_token()
            logical_expression_node = self.logical_expression()
            if logical_expression_node:
                conditional_node.add_child(logical_expression_node)
                block_node = self.block()
                if block_node:
                    conditional_node.add_child(block_node)
                    if self.match_token('CONDITIONAL_KEYWORD'):
                        self.consume_token()
                        else_block_node = self.block()
                        if else_block_node:
                            conditional_node.add_child(else_block_node)
        return conditional_node

    def loop_statement(self):
        """Parses a loop statement.

        Returns:
            (Node): A node representing all tokens under the `loop_statement` non-terminal.
        """
        loop_node = None
        self.skip_whitespace()
        if self.match_token('LOOP_KEYWORD'):
            loop_node = Node("loop_statement", self.current_token[1])
            self.consume_token()
            if self.match_token('IDENTIFIER'):
                identifier_node = Node("identifier", self.current_token[1])
                loop_node.add_child(identifier_node)
                self.consume_token()
                self.expect_token('COLON')
                self.newline()
                self.indent()
                statement_list_node = self.statement_list()
                if statement_list_node:
                    loop_node.add_child(statement_list_node)
            else:
                self.errors.append(f"Expected an identifier, found {self.current_token[0]}: {self.current_token[1]}")
        return loop_node

    def block(self):
        """Parses a block.

        Returns:
            (Node): A node representing all tokens under the `block` non-terminal.
        """
        block_node = Node("block")
        self.indent()
        statement_list_node = self.statement_list()
        if statement_list_node:
            block_node.add_child(statement_list_node)
        return block_node

    
    def expression(self):
        """Parses an expression.

        Returns:
            (Node): A node representing all tokens under the `expression` non-terminal.
        """
        expression_node = None
        self.skip_whitespace()  # Skips preceeding whitespaces
        term_node = self.term()
        if term_node:
            expression_node = Node("expression")
            expression_node.add_child(term_node)
            while self.match_token('ARITHMETIC_OPERATOR'):
                arithmetic_operator_node = Node("arithmetic_operator", self.current_token[1])
                self.consume_token()
                term_node = self.term()
                if term_node:
                    expression_node.add_child(arithmetic_operator_node)
                    expression_node.add_child(term_node)
                else:
                    self.errors.append(f"Expected a term, found {self.current_token[0]}: {self.current_token[1]}")
        else:
            self.errors.append(f"Expected a term, found {self.current_token[0]}: {self.current_token[1]}")
        return expression_node
    
    def term(self):
        """Parses a term.

        Returns:
            (Node): A node representing all tokens under the `term` non-terminal.
        """
        term_node = Node("term")
        self.skip_whitespace()  # Skips preceeding whitespaces
        factor_node = self.factor()
        if factor_node:
            term_node.add_child(factor_node)
            while self.match_token('ARITHMETIC_OPERATOR'):
                arithmetic_operator_node = Node("arithmetic_operator", self.current_token[1])
                self.consume_token()
                factor_node = self.factor()
                if factor_node:
                    term_node.add_child(arithmetic_operator_node)
                    term_node.add_child(factor_node)
                else:
                    self.errors.append(f"Expected a factor, found {self.current_token[0]}: {self.current_token[1]}")
        else:
            self.errors.append(f"Expected a factor, found {self.current_token[0]}: {self.current_token[1]}")
        return term_node
    
    def factor(self):
        """Parses a factor.

        Returns:
            (Node): A node representing all tokens under the `factor` non-terminal.
        """
        factor_node = None
        self.skip_whitespace()  # Skips preceeding whitespaces
        if self.match_token('NUMBER'):
            factor_node = Node("number", self.current_token[1])
            self.consume_token()
        elif self.match_token('IDENTIFIER'):
            factor_node = Node("identifier", self.current_token[1])
            self.consume_token()
        elif self.match_token('STRING_LITERAL'):
            factor_node = Node("string_literal", self.current_token[1])
            self.consume_token()
        elif self.match_token('OPENING_PARENTHESIS'):
            self.consume_token()
            expression_node = self.expression()
            if expression_node:
                factor_node = expression_node
                self.expect_token('CLOSING_PARENTHESIS')
                self.consume_token()
        elif self.match_token('LOGICAL_EXPRESSION'):
            factor_node = self.logical_expression()
        else:
            self.errors.append(f"Invalid token {self.current_token[0]}")
            self.consume_token()
        return factor_node

    def logical_expression(self):
        """Parses a logical expression.

        Returns:
            (Node): A node representing all tokens under the `logical_expression` non-terminal.
        """
        logical_expression_node = None
        # Implement logical expression parsing logic here
        return logical_expression_node

    def match_token(self, expected_token):
        """Compares the expected token with the current token.

        Args:
            expected_token (str): The token pattern to match.

        Returns:
            (bool): True if the current token matches the expected token, otherwise False.
        """
        if self.current_token and self.current_token[0] == expected_token:
            return True
        else:
            return False

    def expect_token(self, expected_token):
        """Compares the expected token with the current token. If they match, advances to the next token.
        If they don't match, adds an error to the error list.

        Args:
            expected_token (str): The token pattern to match.
        """
        if self.match_token(expected_token):
            self.consume_token()
        else:
            self.errors.append(f"Expected '{expected_token}', found {self.current_token[0]}: {self.current_token[1]}")

    def newline(self):
        """Checks for a newline token and consumes it."""
        self.expect_token('NEWLINE')

    def indent(self):
        """Checks for an indent token and consumes it."""
        self.expect_token('INDENT')
        

class Node:
    """Node class for representing nodes in the parse tree
    """
    def __init__(self, name, value=None):
        """Initialises a Node

        Args:
            name (str): non-terminal as described in the refactored BNF
            value (*, optional): non-terminal that is derived from expanding its parent non-terminal. Defaults to None.
        """
        self.name = name
        self.value = value
        self.children = []

    def add_child(self, child):
        """Appends a Node to the sub-tree generated by expanding a non-terminal

        Args:
            child (Node): token obtained after expanding a non-terminal
        """
        self.children.append(child)
        
    def print_tree(self, depth=0):
        """Prints the parse tree that has been constructed

        Args:
            depth (int): Depth of the current node in the tree (used for indentation)
        """
        indent = "  " * depth
        print(f"{indent}{self.name}: {self.value}")

        for child in self.children:
            child.print_tree(depth + 1)
