grammar Tiny;

program
  : statement* EOF
  ;

statement
  : LET IDENT ASSIGN INT SEMI
  | BUG IDENT SEMI
  ;

LET: 'let';
BUG: 'bug';
ASSIGN: '=';
SEMI: ';';
IDENT: [a-zA-Z_][a-zA-Z0-9_]*;
INT: [0-9]+;
WS: [ \t\r\n]+ -> skip;
